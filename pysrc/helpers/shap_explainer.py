# shap_explainer.py
from __future__ import annotations

import os
import math
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Optional, Sequence, Dict, Any
import shap


class ShapExplainer:
    """
    Model-agnostic SHAP explainer for PyTorch models (BNN or MLP).

    Artifacts saved under out_dir/timestamp/:
      - shap_values_class*.npy                (raw SHAP arrays)
      - mean_abs_shap_importance.csv          (overall feature importance)
      - mean_abs_shap_importance_class*.csv   (per-class importance)
      - summary_beeswarm.png                  (beeswarm for a class)
      - bar_importance_overall.png            (overall bar chart)
      - bar_importance_class*.png             (per-class bar charts)

    Notes
    -----
    • Pass the EXACT feature representation your model sees (e.g., binarized inputs for BNN).
    • By default uses KernelExplainer (stable for non-differentiable / binarized nets).
    """

    def __init__(
        self,
        model: torch.nn.Module,
        device: torch.device,
        out_dir: str,
        predict_mode: str = "proba",   # "proba" (default) or "logits"
        random_state: int = 42,
        method: str = "kernel",        # "kernel" (safe default), or "auto" (try gradient if suitable)
        verbose: bool = True,
    ):
        self.model = model
        self.device = device
        self.predict_mode = predict_mode
        self.method = method.lower()
        self.verbose = verbose

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.out_dir = os.path.join(out_dir, f"shap_{ts}")
        os.makedirs(self.out_dir, exist_ok=True)

        self.rng = np.random.RandomState(random_state)

    # ------------------------ prediction wrapper ------------------------

    def _predict(self, X: np.ndarray) -> np.ndarray:
        """Return outputs suitable for SHAP (N, C) where C=#classes or 1."""
        self.model.eval()
        with torch.no_grad():
            x = torch.tensor(X, dtype=torch.float32, device=self.device)
            logits = self.model(x)
            # logits: (N, C) or (N,) or (N, 1)
            if logits.ndim == 1:
                logits = logits.unsqueeze(1)
            if self.predict_mode == "proba":
                # softmax over last dim even for binary with 2 outputs
                probs = F.softmax(logits, dim=1)
                return probs.detach().cpu().numpy()
            return logits.detach().cpu().numpy()

    def _infer_n_classes(self, X_sample: np.ndarray) -> int:
        self.model.eval()
        with torch.no_grad():
            x = torch.tensor(X_sample[: min(8, len(X_sample))], dtype=torch.float32, device=self.device)
            out = self.model(x)
        return int(out.shape[1]) if out.ndim == 2 else 1

    # ------------------------ public API ------------------------

    def explain(
        self,
        X_background: np.ndarray,
        X_explain: np.ndarray,
        feature_names: Optional[Sequence[str]] = None,
        class_names: Optional[Sequence[str]] = None,
        background_size: int = 1000,
        explain_size: int = 256,
        nsamples: str | int = "auto",
        max_display: int = 20,
    ) -> Dict[str, Any]:
        """
        Compute SHAP on a sample of X_explain using X_background as background.

        Parameters
        ----------
        X_background : np.ndarray
            Background data (same preprocessing as training inputs).
        X_explain : np.ndarray
            Samples to explain (e.g., evaluation/test inputs).
        feature_names : list[str], optional
        class_names : list[str], optional
        background_size : int
        explain_size : int
        nsamples : "auto" or int
        max_display : int

        Returns
        -------
        dict with paths and metadata.
        """
        # ---- sample for tractability ----
        bg_size = min(background_size, len(X_background))
        ex_size = min(explain_size, len(X_explain))
        bg_idx = self.rng.choice(len(X_background), size=bg_size, replace=False)
        ex_idx = self.rng.choice(len(X_explain), size=ex_size, replace=False)
        X_bg = np.ascontiguousarray(X_background[bg_idx], dtype=np.float32)
        X_ex = np.ascontiguousarray(X_explain[ex_idx], dtype=np.float32)

        n_features = X_bg.shape[1]
        if feature_names is None or len(feature_names) != n_features:
            # ensure names align with real shape
            feature_names = [f"f{i}" for i in range(n_features)]

        n_classes = self._infer_n_classes(X_bg)
        if class_names is None or len(class_names) != n_classes:
            class_names = [f"class_{i}" for i in range(n_classes)]

        # ---- pick explainer ----
        # KernelExplainer works for both BNN & MLP and mismatched pipelines.
        # If method="auto" and the model looks differentiable, we can switch to GradientExplainer for speed.
        use_kernel = True
        if self.method == "auto":
            # crude heuristic: if module names contain 'Binary' or 'Sign', stay kernel
            names = " ".join([m.__class__.__name__.lower() for m in self.model.modules()])
            if ("binary" not in names) and ("sign" not in names):
                use_kernel = False

        if use_kernel:
            if self.verbose:
                print("[SHAP] Using KernelExplainer (model-agnostic).")
            explainer = shap.KernelExplainer(self._predict, X_bg, link="logit")
            sv = explainer.shap_values(X_ex, nsamples=nsamples)
        else:
            if self.verbose:
                print("[SHAP] Using GradientExplainer (fast for smooth nets).")
            # GradientExplainer expects a callable returning outputs; we supply the model itself.
            self.model.eval()
            explainer = shap.GradientExplainer(self.model, torch.tensor(X_bg, dtype=torch.float32, device=self.device))
            # Returns shap.Explanation (new API) or ndarray depending on SHAP version
            with torch.no_grad():
                sv = explainer.shap_values(torch.tensor(X_ex, dtype=torch.float32, device=self.device))

        # ---- normalize shapes to (N, F, C) ----
        values = self._to_nfc(sv)  # (N, F, C)
        N, F, C = values.shape

        # guard: feature_names must match F
        if len(feature_names) != F:
            if self.verbose:
                print(f"[SHAP] Adjusting feature_names from {len(feature_names)} to {F}.")
            feature_names = [f"f{i}" for i in range(F)]

        # ---- compute importances ----
        # overall importance: mean abs across samples and classes -> (F,)
        overall_importance = np.mean(np.abs(values), axis=(0, 2))
        imp_df = (
            pd.DataFrame({"feature": feature_names, "mean_abs_shap": overall_importance})
            .sort_values("mean_abs_shap", ascending=False)
            .reset_index(drop=True)
        )
        imp_csv = os.path.join(self.out_dir, "mean_abs_shap_importance.csv")
        imp_df.to_csv(imp_csv, index=False)

        # per-class importances
        per_class_csvs = []
        for c in range(C):
            imp_c = np.mean(np.abs(values[:, :, c]), axis=0)  # (F,)
            imp_c_df = (
                pd.DataFrame({"feature": feature_names, "mean_abs_shap": imp_c})
                .sort_values("mean_abs_shap", ascending=False)
                .reset_index(drop=True)
            )
            path_c = os.path.join(self.out_dir, f"mean_abs_shap_importance_class{c}.csv")
            imp_c_df.to_csv(path_c, index=False)
            per_class_csvs.append(path_c)

        # ---- plots ----
        # 1) Beeswarm: pick class with largest total variance for a richer plot
        cls_for_plot = int(np.argmax(np.var(values, axis=0).sum(axis=0)))
        X_ex_df = pd.DataFrame(X_ex, columns=feature_names)
        plt.figure()
        shap.summary_plot(values[:, :, cls_for_plot], X_ex_df, show=False, max_display=max_display)
        self._savefig("summary_beeswarm.png")

        # 2) Overall bar chart (top-K)
        order = np.argsort(overall_importance)[::-1][:max_display]
        plt.figure()
        plt.barh(np.array(feature_names)[order][::-1], overall_importance[order][::-1])
        plt.title("Overall mean|SHAP| importance")
        plt.xlabel("mean(|SHAP|)")
        self._savefig("bar_importance_overall.png")

        # 3) Per-class bar charts
        for c in range(C):
            imp_c = np.mean(np.abs(values[:, :, c]), axis=0)
            order_c = np.argsort(imp_c)[::-1][:max_display]
            plt.figure()
            plt.barh(np.array(feature_names)[order_c][::-1], imp_c[order_c][::-1])
            plt.title(f"mean|SHAP| importance – {class_names[c]}")
            plt.xlabel("mean(|SHAP|)")
            self._savefig(f"bar_importance_class{c}.png")

        if self.verbose:
            print(
                f"[SHAP] Saved to {self.out_dir}\n"
                f" - {imp_csv}\n"
                f" - summary_beeswarm.png\n"
                f" - bar_importance_overall.png\n"
                f" - bar_importance_class*.png\n"
                f" - raw shap_values_class*.npy"
            )

        return {
            "dir": self.out_dir,
            "importance_csv": imp_csv,
            "per_class_csvs": per_class_csvs,
            "n_classes": C,
            "class_names": class_names,
        }

    # ------------------------ utilities ------------------------

    def _to_nfc(self, sv: Any) -> np.ndarray:
        """
        Normalize different SHAP outputs to shape (N, F, C).
        Handles:
          • list of (N, F) per class (KernelExplainer multiclass)
          • shap.Explanation with .values of shape (N, F) or (N, F, C)
          • raw ndarray (N, F) or (N, F, C)
        Also saves raw per-class arrays to disk.
        """
        if isinstance(sv, list):
            # list of (N, F) each class
            values = np.stack(sv, axis=-1)  # (N, F, C)
            for c, arr in enumerate(sv):
                np.save(os.path.join(self.out_dir, f"shap_values_class{c}.npy"), arr)
            return values

        if hasattr(sv, "values"):  # shap.Explanation
            vals = sv.values
            if vals.ndim == 2:
                vals = vals[..., None]     # (N, F) -> (N, F, 1)
            # try to save per-class if possible
            for c in range(vals.shape[-1]):
                np.save(os.path.join(self.out_dir, f"shap_values_class{c}.npy"), vals[..., c])
            return vals

        # ndarray fallback
        arr = np.asarray(sv)
        if arr.ndim == 2:
            arr = arr[..., None]  # (N, F) -> (N, F, 1)
        for c in range(arr.shape[-1]):
            np.save(os.path.join(self.out_dir, f"shap_values_class{c}.npy"), arr[..., c])
        return arr

    def _savefig(self, filename: str, dpi: int = 200):
        plt.tight_layout()
        path = os.path.join(self.out_dir, filename)
        plt.savefig(path, dpi=dpi)
        plt.close()

    # ------------------------ convenience for your Trainer ------------------------

    @staticmethod
    def run_from_trainer(
        trainer,                       # your Trainer instance
        out_dir: Optional[str] = None,
        use_eval: bool = True,         # explain on eval/test if available, else on train
        background_size: int = 256,
        explain_size: int = 1000,
        nsamples: str | int = "auto",
        max_display: int = 20,
        predict_mode: str = "proba",
        method: str = "kernel",        # or "auto"
        random_state: int = 42,
        feature_names: Optional[Sequence[str]] = None,
        class_names: Optional[Sequence[str]] = None,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        One-liner to compute SHAP using fields from your Trainer.

        Expects:
          - trainer.model (trained)
          - trainer.device
          - trainer.X_tr (background)
          - trainer.X_te or trainer.X_val (explained set) when use_eval=True
          - trainer.res_dir and trainer.dataset (for default out_dir)
        """
        model = trainer.model
        device = trainer.device

        # choose out directory
        if out_dir is None:
            out_dir = os.path.join(trainer.results_dir, f"shap_{getattr(trainer, 'dataset', 'dataset')}")

        # pick arrays
        X_bg = getattr(trainer, "X_tr", None)
        if X_bg is None:
            raise ValueError("Trainer must provide X_tr for background.")

        X_ex = None
        if use_eval:
            X_ex = getattr(trainer, "X_te", None)
            if X_ex is None:
                X_ex = getattr(trainer, "X_val", None)
        if X_ex is None:
            # fallback: explain on training data
            X_ex = X_bg

        # names, if available on trainer
        if feature_names is None:
            feature_names = getattr(trainer, "feature_names", None) or getattr(trainer, "selected_feats", None)
        if class_names is None:
            if hasattr(trainer, "args") and hasattr(trainer.args, "num_classes"):
                class_names = [f"class_{i}" for i in range(trainer.args.num_classes)]

        expl = ShapExplainer(
            model=model,
            device=device,
            out_dir=out_dir,
            predict_mode=predict_mode,
            random_state=random_state,
            method=method,
            verbose=verbose,
        )
        return expl.explain(
            X_background=X_bg,
            X_explain=X_ex,
            feature_names=feature_names,
            class_names=class_names,
            background_size=background_size,
            explain_size=explain_size,
            nsamples=nsamples,
            max_display=max_display,
        )
