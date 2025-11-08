import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay        
import numpy as np
from datetime import datetime
import csv


RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


class MetricsManager():
    def __init__(self, init_lr, init_epochs, scheduler, hidden_layers, distilled, init_wd, res_dir, dataset, model_arch, model_name):
        self.cases = {}
        self.bestacc = -np.inf
        self.bestfold = 0
        self.init_lr = init_lr
        self.epochs = init_epochs
        self.scheduler = scheduler
        self.hidden_layers = hidden_layers
        self.distilled = distilled
        self.init_wd = init_wd
        self.res_dir = res_dir
        self.dataset = dataset
        self.model_arch = model_arch
        self.model_name = model_name
        print(f'Set results dir: [{self.res_dir}]')
        print(f'Set results file: [{self.res_dir}/results_{self.dataset}.csv]')
        print(f'Set model identifier: {self.model_arch}')

    def initCase(self, case):
        self.cases[case] = {
            'cms': [],
            'cms_names': [],
            'accuracy': [],
            'losses': [],
            'precision': [],
            'f1': [],
            'recall': []
        }

    def addF1(self, case, f1):
        self.cases[case]['f1'].append(f1)

    def addRec(self, case, recall):
        self.cases[case]['recall'].append(recall)

    def addPrec(self, case, prec):
        self.cases[case]['precision'].append(prec)
    
    def addAcc(self, case, acc):
        if case not in self.cases:
            self.initCase(case)
        self.cases[case]['accuracy'].append(acc)
        if acc > self.bestacc:
            self.bestacc = acc
            # Extract fold number if present, otherwise use 0 for single training
            if len(case) > 5 and case.startswith('train'):
                try:
                    self.bestfold = int(case[5:])
                except ValueError:
                    self.bestfold = 0
            else:
                self.bestfold = 0

    def addLoss(self, case, loss):
        if case not in self.cases:
            self.initCase(case)
        self.cases[case]['losses'].append(loss)

    def displayTrainEvalAcc(self):
        if not isinstance(self.epochs, list):
            self.epochs = list(range(1, self.epochs+1))
        plt.rcParams.update({
            'font.size': 18,
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
        })
        plt.figure(figsize=(8, 5))

        # Check if we have cross-validation folds or simple training
        folds = sorted({int(k[len('train'):]) for k in self.cases if k.startswith('train') and k != 'train'})
        
        if len(folds) > 0:  # Cross-validation mode
            train_mat = np.vstack([self.cases[f'train{f}']['accuracy'] for f in folds])
            valid_mat = np.vstack([self.cases[f'valid{f}']['accuracy'] for f in folds])

            mean_train = train_mat.mean(axis=0)
            std_train  = train_mat.std(axis=0)
            mean_valid = valid_mat.mean(axis=0)
            std_valid  = valid_mat.std(axis=0)

            plt.plot(self.epochs, mean_train,  color='blue',  lw=2, label='Mean training accuracy')
            plt.fill_between(self.epochs,
                            mean_train - std_train,
                            mean_train + std_train,
                            color='blue', alpha=0.2)

            plt.plot(self.epochs, mean_valid, color='orange', lw=2, label='Mean validation accuracy', linestyle='--')
            plt.fill_between(self.epochs,
                            mean_valid - std_valid,
                            mean_valid + std_valid,
                            color='orange', alpha=0.2)
        else:  # Simple training mode (base models)
            if 'train' in self.cases and 'valid' in self.cases:
                # Training with validation split
                train_acc = self.cases['train']['accuracy']
                valid_acc = self.cases['valid']['accuracy']
                
                plt.plot(self.epochs[:len(train_acc)], train_acc, color='blue', lw=2, label='Training accuracy')
                plt.plot(self.epochs[:len(valid_acc)], valid_acc, color='orange', lw=2, label='Validation accuracy', linestyle='--')
            elif 'train' in self.cases:
                # Training only (no validation)
                train_acc = self.cases['train']['accuracy']
                plt.plot(self.epochs[:len(train_acc)], train_acc, color='blue', lw=2, label='Training accuracy')

        cmap = plt.get_cmap('Set2')
        y_min, y_max = plt.ylim()
        # for i, (xmin, xmax, lr) in enumerate(self.lr_regions):
        #     color = cmap(i % cmap.N)
        #     plt.axvspan(xmin, xmax, color=color, alpha=0.3)
        #     xmid = (xmin + xmax) / 2
        #     yloc = y_max - 0.5 * (y_max - y_min)
        #     plt.text(xmid, yloc, f'lr:{lr:.0e}',
        #             ha='center', va='center', alpha=0.8)

        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.ylim(top=1)
        # Add a caption describing the plot. [Quale e' il messaggio di questo plot, cosa devo guardare?]
        plt.legend(loc='lower right')
        plt.grid(False)
        plt.tight_layout()
        now = datetime.now().strftime("%d-%H%M%S")
        out = f'{self.res_dir}/plots_{self.dataset}/training_acc_{self.model_name}_{self.model_arch}_{self.dataset}_{now}.png'
        plt.savefig(out)
        plt.close()
        print(f'Saved training chart to {out}')

    def saveEvalResults(self):
        eval_cases = sorted(
            [c for c in self.cases if c.startswith('evalu') and c != 'evalu'],
            key=lambda c: int(c[len('evalu'):])
        )

        metrics = ['accuracy', 'precision', 'recall', 'f1']
        summary = []

        for m in metrics:
            # final value of metric m for each fold
            vals = []
            for c in eval_cases:
                arr = self.cases[c].get(m, [])
                if arr:
                    vals.append(arr[-1])
            vals = np.array(vals, dtype=float)
            mean = float(vals.mean()) if vals.size else float('nan')
            std  = float(vals.std())  if vals.size else float('nan')
            summary.append((m.rstrip('s'), mean, std))

        # 4) Write to CSV
        out_filename = f"{self.res_dir}/results_{self.model_name}_{self.model_arch}_{self.dataset}.csv"
        with open(out_filename, 'w', newline='') as fp:
            writer = csv.writer(fp)
            writer.writerow(['metric', 'mean', 'std'])
            for metric_name, mean, std in summary:
                writer.writerow([metric_name, f"{mean:.6f}", f"{std:.6f}"])

        print(f"Saved evaluation summary to {out_filename}")


    def displayLosses(self):
        # Check if we have cross-validation folds or simple training
        fold_ids = sorted(int(k[len("train"):]) for k in self.cases if k.startswith("train") and k != "train")
        
        if len(fold_ids) > 0:  # Cross-validation mode
            all_epochs = []
            for k, case in self.cases.items():
                if k.startswith("train") and k != "train":
                    all_epochs += [epoch for (_, epoch) in case["losses"]]
            n_epochs = max(all_epochs) + 1       # e.g. 0..9 → 10 epochs
            epoch_indices = np.arange(1, n_epochs+1)

            per_fold_epoch_loss = []
            for f in fold_ids:
                # bucket all batch losses by epoch
                buckets = [[] for _ in range(n_epochs)]
                for loss, epoch in self.cases[f"train{f}"]["losses"]:
                    buckets[epoch].append(loss)
                # average each bucket
                avg_losses = [np.mean(b) if len(b)>0 else np.nan for b in buckets]
                per_fold_epoch_loss.append(avg_losses)

            loss_mat = np.vstack(per_fold_epoch_loss)
            mean_loss = loss_mat.mean(axis=0)
            std_loss  = loss_mat.std(axis=0)

            plt.figure(figsize=(8,5))
            plt.plot(epoch_indices, mean_loss, color='tab:blue', lw=2, label="Mean train loss")
            plt.fill_between(epoch_indices,
                            mean_loss - std_loss,
                            mean_loss + std_loss,
                            color='tab:blue', alpha=0.2, label="Standard Deviation")
        else:  # Simple training mode (base models)
            if 'train' in self.cases:
                # Get losses from simple training
                train_losses = self.cases['train']['losses']
                if len(train_losses) > 0:
                    # Group losses by epoch
                    epochs_dict = {}
                    for loss, epoch in train_losses:
                        if epoch not in epochs_dict:
                            epochs_dict[epoch] = []
                        epochs_dict[epoch].append(loss)
                    
                    # Calculate mean loss per epoch
                    epochs = sorted(epochs_dict.keys())
                    epoch_indices = [e + 1 for e in epochs]  # Convert to 1-indexed
                    mean_losses = [np.mean(epochs_dict[e]) for e in epochs]
                    
                    plt.figure(figsize=(8,5))
                    plt.plot(epoch_indices, mean_losses, color='tab:blue', lw=2, label="Training loss")
                else:
                    return  # No losses to plot

        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.legend()
        plt.grid(False)
        plt.tight_layout()
        plt.rcParams.update({
            'font.size': 18,
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
        })
        now = datetime.now().strftime("%d-%H%M%S")
        out = f"{self.res_dir}/plots_{self.dataset}/training_loss_{self.model_name}_{self.model_arch}_{self.dataset}_{now}.png"
        plt.savefig(out)
        plt.close()
        print(f'Saved loss chart to {out}')

    def addConfMatrix(self, case, y_true, y_pred, title=None):
        cm = confusion_matrix(y_true, y_pred)
        if case not in self.cases:
            self.initCase(case)

        self.cases[case]['cms'].append(cm)
        if title != None:
            self.cases[case]['cms_names'].append(title)
        else:
            self.cases[case]['cms_names'].append('DEFAULT TITLE')
        

    def displayConfMatrixPlot(self, case):
        # Set font configuration for confusion matrices
        plt.rcParams.update({
            'font.size': 24,  # Increased font size for better readability
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
        })
        
        n_matrices = len(self.cases[case]['cms'])
        file_ct = 1
        if('evalu' in case):
            rows = 1; cols = 1; xsize = 6; ysize = 6
            assert(n_matrices==1, 'More than one confusion matrix for evaluation case.')
        else:
            rows = 4; cols = 5; xsize = 12; ysize = 9

        while(n_matrices > 0):
            fig, axes = plt.subplots(rows, cols, figsize=(xsize, ysize))
            axes = np.atleast_1d(axes).flatten()

            for ax, cm, title in zip(axes, self.cases[case]['cms'], self.cases[case]['cms_names']):
                disp = ConfusionMatrixDisplay(confusion_matrix=cm)
                disp.plot(ax=ax, values_format='d', cmap='Blues', colorbar=False)

            plt.tight_layout()
            out=f'{self.res_dir}/plots_{self.dataset}/{case}{file_ct}_{self.model_name}_{self.model_arch}_{self.dataset}_{datetime.now().strftime("%d-%H:%M:%S.%f")[:-3]}.png'
            print(f'Saved evaluation confusion matrix to {out}')
            plt.savefig(out)
            plt.close(fig=fig)
            file_ct += 1
            n_matrices -= rows*cols # each png file contains 10 epoch conf matrices
            self.cases[case]['cms'] = self.cases[case]['cms'][rows*cols:]
            self.cases[case]['cms_names'] = self.cases[case]['cms_names'][rows*cols:]

        # self.cases[case] = None

    def batchLog(self, mode, epoch_no, dataset_len, loss, acc, curr_len, kfold, epochs):
        if(acc < 0.7):
            acc_str = self.redLog(acc*100)
        elif(acc > 0.92):
            acc_str = self.greenLog(acc*100)
        else:
            acc_str = f'{acc*100:.3f}%'

        # print(f"{mode} | Kfold: [{kfold}] Epoch: [{epoch_no:>3d}\{epochs:>3d}] [{curr_len:>6d}/{dataset_len:>6d}] Loss: {loss:>5f} Accuracy: {acc_str}")

    def redLog(self, string):
        return f'{RED}{(string):.3f}%{RESET}'
    
    def greenLog(self, string):
        return f'{GREEN}{(string):.3f}%{RESET}'

    def plot_confidence_histogram(self, fold_confidence_data, model_name, model_arch, dataset, results_dir):
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Get all unique confidence scores across all folds
        all_confidences = []
        for fold_data in fold_confidence_data:
            all_confidences.extend([conf for conf, _, _ in fold_data])
        unique_confs = np.unique(all_confidences)
        
        # Calculate accuracy per confidence score per fold
        fold_accuracies = {}
        confidence_counts = {}
        total_samples = len(all_confidences)
        
        for fold_idx, fold_data in enumerate(fold_confidence_data):
            if not fold_data:
                continue
            confidences, preds, truths = zip(*fold_data)
            confidences = np.array(confidences)
            preds = np.array(preds)
            truths = np.array(truths)
            
            fold_accuracies[fold_idx] = {}
            for conf in unique_confs:
                mask = confidences == conf
                count = np.sum(mask)
                if count > 0:
                    accuracy = np.mean(preds[mask] == truths[mask])
                    fold_accuracies[fold_idx][conf] = accuracy
                    # Count total occurrences across all folds
                    if conf not in confidence_counts:
                        confidence_counts[conf] = 0
                    confidence_counts[conf] += count
        
        # Calculate mean and std for each confidence score
        conf_means = []
        conf_stds = []
        conf_percentages = []
        
        for conf in unique_confs:
            fold_accs = [fold_accuracies[fold][conf] for fold in fold_accuracies.keys() if conf in fold_accuracies[fold]]
            if fold_accs:
                conf_means.append(np.mean(fold_accs))
                conf_stds.append(np.std(fold_accs))
            else:
                conf_means.append(0)
                conf_stds.append(0)
            
            # Calculate percentage for this confidence score
            count = confidence_counts.get(conf, 0)
            percentage = (count / total_samples) * 100 if total_samples > 0 else 0
            conf_percentages.append(percentage)
        
        conf_means = np.array(conf_means)
        conf_stds = np.array(conf_stds)
        conf_percentages = np.array(conf_percentages)
        
        # Calculate weighted values (accuracy × percentage)
        weighted_values = conf_means * (conf_percentages / 100.0)
        weighted_stds = conf_stds * (conf_percentages / 100.0)
        
        plt.rcParams.update({
            'font.size': 20,  # Reduced font size to fit more content
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
        })
        fig, ax1 = plt.subplots(figsize=(14, 8))
        
        # Primary y-axis: Weighted accuracy bars (accuracy × percentage)
        bars = ax1.bar(unique_confs, weighted_values, width=0.6, alpha=0.7, 
                      color='green', edgecolor='black', capsize=5)
        ax1.errorbar(unique_confs, weighted_values, yerr=weighted_stds, fmt='none', 
                    color='black', capsize=5)
        
        ax1.set_xlabel('Confidence Score')
        ax1.set_ylabel('P(Correct|Confidence) × Sample %', color='black')
        max_weighted = max(weighted_values) if len(weighted_values) > 0 else 1
        ax1.set_ylim([0, max_weighted * 1.2])
        ax1.tick_params(axis='y', labelcolor='black')
        
        # Fit Gaussian model to confidence scores
        from scipy.stats import norm
        import pickle
        import os
        
        # Prepare data for Gaussian fitting (use all confidence values with their frequencies)
        confidence_data_for_fitting = []
        for conf, count in confidence_counts.items():
            confidence_data_for_fitting.extend([conf] * count)
        
        if len(confidence_data_for_fitting) > 0:
            # Fit Gaussian distribution
            mu, sigma = norm.fit(confidence_data_for_fitting)
            
            # Create smooth curve for overlay
            x_smooth = np.linspace(min(unique_confs), max(unique_confs), 200)
            gaussian_curve = norm.pdf(x_smooth, mu, sigma)
            
            # Scale Gaussian curve to match the weighted values scale
            # Scale by maximum weighted value for proper overlay
            scale_factor = max_weighted * 0.8  # Scale to 80% of max for visibility
            gaussian_curve_scaled = gaussian_curve * scale_factor / max(gaussian_curve)
            
            # Plot Gaussian curve overlay
            ax1.plot(x_smooth, gaussian_curve_scaled, 'b-', linewidth=3, 
                    label='Gaussian Fit', alpha=0.8)
            
            # Add legend
            ax1.legend(loc='upper right')
            
            # Save Gaussian model parameters
            gaussian_model = {
                'mu': float(mu),
                'sigma': float(sigma),
                'model_name': model_name,
                'model_arch': model_arch,
                'dataset': dataset,
                'total_samples': total_samples,
                'fitted_data_size': len(confidence_data_for_fitting)
            }
            
            # Ensure directory exists
            model_dir = f'{results_dir}/models_{dataset}'
            os.makedirs(model_dir, exist_ok=True)
            
            # Save model
            model_path = f'{model_dir}/gaussian_confidence_model_{model_name}_{model_arch}_{dataset}.pkl'
            with open(model_path, 'wb') as f:
                pickle.dump(gaussian_model, f)
            
            print(f'Gaussian confidence model saved: {model_path}')
            print(f'  μ = {mu:.4f}, σ = {sigma:.4f}')
        
        for spine in ax1.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(0.7)
        
        plot_path = f'{results_dir}/plots_{dataset}/confidence_histogram_{model_name}_{model_arch}_{dataset}.png'
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300, bbox_inches='tight', edgecolor='black')
        plt.close()
        print(f'Confidence histogram saved: {plot_path}')

        
