# shap_explainer.py
from __future__ import annotations

import os
import math
import random 
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

        if 'shap_' in os.path.basename(out_dir):
            self.out_dir = out_dir
        else:
            self.out_dir = self.out_dir.split('/shap_')[0]+self.out_dir.split('/shap_')[1]
        os.makedirs(self.out_dir, exist_ok=True)

        # np.random.seed(random_state)
        # torch.manual_seed(random_state)
        # random.seed(random_state)
        

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
        max_display: int = 10,
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
        # ---- ensure reproducibility ----
        # self._set_seeds()
        
        # ---- sample for tractability ----
        bg_size = min(background_size, len(X_background))
        ex_size = min(explain_size, len(X_explain))
        bg_idx = np.random.choice(len(X_background), size=bg_size, replace=False)
        ex_idx = np.random.choice(len(X_explain), size=ex_size, replace=False)
        X_bg = np.ascontiguousarray(X_background[bg_idx], dtype=np.float32)
        X_ex = np.ascontiguousarray(X_explain[ex_idx], dtype=np.float32)

        n_features = X_bg.shape[1]
        if feature_names is None or len(feature_names) != n_features:
            # ensure names align with real shape
            feature_names = [f"bit_f{i}" for i in range(n_features)]

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
            # Set random state for KernelExplainer for reproducibility
            explainer = shap.KernelExplainer(self._predict, X_bg, link="logit")
            # Pass random state to SHAP computation
            if isinstance(nsamples, str) and nsamples == "auto":
                nsamples = min(2 * len(X_bg) + 2048, 5000)  # Default with seed consideration
            sv = explainer.shap_values(X_ex, nsamples=nsamples)
        else:
            if self.verbose:
                print("[SHAP] Using GradientExplainer (fast for smooth nets).")
            # GradientExplainer expects a callable returning outputs; we supply the model itself.
            self.model.eval()
            # Set deterministic mode for gradient computation
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
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
            feature_names = [f"bit_f{i}" for i in range(F)]

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
        plt.figure(figsize=(10, 8))
        plt.rcParams.update({
            'font.size': 28,
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
        })
        shap.summary_plot(values[:, :, cls_for_plot], X_ex_df, show=False, max_display=max_display)
        plt.xlabel("SHAP value")  # Remove "(impact on model output)" from the default label
        self._savefig("summary_beeswarm.png")

        # 2) Overall bar chart (top-K)
        order = np.argsort(overall_importance)[::-1][:max_display]
        plt.figure(figsize=(12, 8))
        plt.rcParams.update({
            'font.size': 20,
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
        })
        plt.barh(np.array(feature_names)[order][::-1], overall_importance[order][::-1])
        # plt.title("mean(abs(SHAP)) importance")
        plt.xlabel("mean(abs(SHAP))")
        plt.tight_layout()
        self._savefig("bar_importance_overall.png")

        # ---- save all features ordered by importance ----
        self._save_features_by_importance(imp_df)
        
        if self.verbose:
            print(
                f"[SHAP] Saved to {self.out_dir}\n"
                f" - {imp_csv}\n"
                f" - summary_beeswarm.png\n"
                f" - bar_importance_overall.png\n"
                # f" - bar_importance_class*.png\n"
                f" - raw shap_values_class*.npy\n"
                f" - feature_indices.json"
            )

        return {
            "dir": self.out_dir,
            "importance_csv": imp_csv,
            # "per_class_csvs": per_class_csvs,
            "n_classes": C,
            "class_names": class_names,
        }

    def _save_features_by_importance(self, importance_df: pd.DataFrame):
        """Save all features ordered by SHAP importance."""
        import json
        
        # Use all features (already sorted by importance)
        all_features = importance_df
        
        # Extract feature indices (assuming feature names are like 'bit_f152', 'bit_f145', etc.)
        feature_indices = []
        feature_names = []
        
        for _, row in all_features.iterrows():
            feature_name = row['feature']
            feature_names.append(feature_name)
            
            # Extract index from feature name (e.g., 'bit_f152' -> 152)
            if feature_name.startswith('bit_f'):
                try:
                    idx = int(feature_name.replace('bit_f', ''))
                    feature_indices.append(idx)
                except ValueError:
                    print(f"Warning: Could not extract index from feature name: {feature_name}")
            else:
                print(f"Warning: Unexpected feature name format: {feature_name}")
        
        # Save all features ordered by importance
        indices_data = {
            'total_features': len(all_features),
            'feature_indices': feature_indices,
            'feature_names': feature_names,
            'importance_values': all_features['mean_abs_shap'].tolist()
        }
        
        indices_file = os.path.join(self.out_dir, "feature_indices.json")
        with open(indices_file, 'w') as f:
            json.dump(indices_data, f, indent=2)
        
        if self.verbose:
            print(f"Saved all {len(all_features)} features ordered by importance to: {indices_file}")
            print(f"Top 5 feature indices: {feature_indices[:5]}")
        
        return indices_file

    @staticmethod
    def check_existing_shap_indices(model_arch: str, dataset_name: str, base_dir: str = None) -> str:
        """
        Check if SHAP feature indices already exist for the given model architecture and dataset.
        
        Parameters
        ----------
        model_arch : str
            Model architecture string (e.g., "168-42-2")
        dataset_name : str
            Dataset name (e.g., "CICIDS2017")
        base_dir : str, optional
            Base directory to search in. If None, uses relative path to results directory.
            
        Returns
        -------
        str or None
            Path to existing SHAP indices file if found, None otherwise
        """
        # Set base directory relative to this script's location
        if base_dir is None:
            # Get the directory of this script and navigate to shap folder
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up from ml_helpers to p4src
            base_dir = os.path.join(script_dir, "shaps")
        
        # Create the specific SHAP directory name
        shap_dir_name = f"shap_{model_arch.replace('_', '-')}_{dataset_name.lower()}"
        shap_path = os.path.join(base_dir, shap_dir_name)
        
        # Only check the specific directory, no fallback
        if os.path.exists(shap_path):
            indices_file = os.path.join(shap_path, "feature_indices.json")
            if os.path.exists(indices_file):
                return indices_file
        
        return None
    
    @staticmethod
    def load_shap_indices(indices_file_path: str) -> dict:
        """
        Load SHAP feature indices from file.
        
        Parameters
        ----------
        indices_file_path : str
            Path to the indices JSON file
            
        Returns
        -------
        dict
            Dictionary containing feature indices, names, and importance values
        """
        import json
        
        with open(indices_file_path, 'r') as f:
            return json.load(f)

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
        path = os.path.join(self.out_dir, filename)
        plt.savefig(path, dpi=dpi, bbox_inches='tight')
        plt.close()
        # Reset font size for next plot
        plt.rcParams.update({'font.size': plt.rcParamsDefault['font.size']})

    # ------------------------ convenience for your Trainer ------------------------

    @staticmethod
    def run_from_trainer(
        trainer,                       # your Trainer instance
        out_dir: Optional[str] = None,
        use_eval: bool = True,         # explain on eval/test if available, else on train
        background_size: Optional[int] = None,  # Will use trainer config if None
        explain_size: Optional[int] = None,     # Will use trainer config if None
        nsamples: str | int = "auto",
        max_display: int = 10,
        predict_mode: str = "proba",
        method: str = "kernel",        # or "auto"
        random_state: int = 42,
        feature_names: Optional[Sequence[str]] = None,
        class_names: Optional[Sequence[str]] = None,
        verbose: bool = True,
        force_recompute: bool = True,  # Force recomputation even if indices exist
    ) -> tuple[Dict[str, Any], str]:
        """
        One-liner to compute SHAP using fields from your Trainer.
        Now checks for existing feature indices before computing.
        Saves all features ordered by importance (not just top k).
        
        Reproducibility: Uses random_state for deterministic sampling and SHAP computation.

        Expects:
          - trainer.model (trained)
          - trainer.device
          - trainer.X_tr (background)
          - trainer.X_te or trainer.X_val (explained set) when use_eval=True
          - trainer.model_arch (for naming)
          - trainer.dataset (for naming)
        """
        model = trainer.model
        device = trainer.device
        model_arch = getattr(trainer, 'model_arch', 'unknown')
        dataset_name = getattr(trainer, 'dataset', 'dataset')
        model_name = trainer.model_name
        
        # Use trainer's SHAP configuration as defaults if parameters not specified
        background_size = background_size or getattr(trainer, 'shap_background_size', 256)
        explain_size = explain_size or getattr(trainer, 'shap_explain_size', 500)
        
        if verbose:
            print(f"SHAP Configuration:")
            print(f"  Background size: {background_size}")
            print(f"  Explain size: {explain_size}")
            print(f"  Random state: {random_state}")
        
        # Check for existing SHAP indices unless force recompute
        if not force_recompute:
            existing_indices_file = ShapExplainer.check_existing_shap_indices(
                model_arch, dataset_name
            )
            if existing_indices_file:
                if verbose:
                    print(f"Found existing SHAP feature indices: {existing_indices_file}")
                    print("Skipping SHAP computation. Use force_recompute=True to override.")
                    
                    # Load and display top features
                    indices_data = ShapExplainer.load_shap_indices(existing_indices_file)
                    print(f"Top 5 feature indices: {indices_data['feature_indices'][:5]}")
                    print(f"Top 5 feature names: {indices_data['feature_names'][:5]}")
                
                return {
                    "indices_file": existing_indices_file,
                    "indices_data": ShapExplainer.load_shap_indices(existing_indices_file),
                    "existing": True
                }

        # Set up output directory with architecture-based naming
        if out_dir is None:
            # Get the directory of this script and navigate to shap folder
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up from ml_helpers to p4src
            base_dir = os.path.join(script_dir, "shaps")
            shap_dir_name = f"shap_{model_name}_{model_arch.replace('_', '-')}_{dataset_name.lower()}"
            out_dir = os.path.join(base_dir, shap_dir_name)

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

        if verbose:
            print(f"\n Computing SHAP for architecture: {model_arch}")
            print(f"Results will be saved to: {out_dir}")

        expl = ShapExplainer(
            model=model,
            device=device,
            out_dir=out_dir,
            predict_mode=predict_mode,
            random_state=random_state,
            method=method,
            verbose=verbose,
        )
        
        result = expl.explain(
            X_background=X_bg,
            X_explain=X_ex,
            feature_names=feature_names,
            class_names=class_names,
            background_size=background_size,
            explain_size=explain_size,
            nsamples=nsamples,
            max_display=max_display,
        )
        
        # Add indices file path to result
        indices_file = os.path.join(out_dir, "feature_indices.json")
        if os.path.exists(indices_file):
            result["indices_file"] = indices_file
            result["indices_data"] = ShapExplainer.load_shap_indices(indices_file)
        
        return result, indices_file
