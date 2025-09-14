import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay        
import numpy as np
from datetime import datetime
import csv


RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


class MetricsManager():
    def __init__(self, init_lr, init_epochs, scheduler, hidden_layers, distilled, init_wd):
        self.cases = {}
        self.bestacc = -np.inf
        self.bestfold = 0
        self.init_lr = init_lr
        self.curr_lr = init_lr
        self.lr_regions = list()
        self.epochs = init_epochs
        self.scheduler = scheduler
        self.hidden_layers = hidden_layers
        self.distilled = distilled
        self.init_wd = init_wd

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
    
    def addLrRegion(self, item):
        if item not in self.lr_regions:
            self.lr_regions.append(item)

    def addLr(self, region: tuple):
        lr, epoch = region
        
        if (lr != self.curr_lr):
            if len(self.lr_regions) == 0:
                self.addLrRegion((1, epoch, self.curr_lr))
            else:
                _, last_epoch, _ = self.lr_regions[-1]
                self.addLrRegion((last_epoch, epoch, self.curr_lr))
            self.curr_lr = lr
        elif epoch == self.epochs:
            if len(self.lr_regions) == 0:
                self.addLrRegion((1, epoch, self.curr_lr))
            else:
                _, last_epoch, _ = self.lr_regions[-1]
                self.addLrRegion((last_epoch, epoch, self.curr_lr))
        

    def addAcc(self, case, acc):
        if case not in self.cases:
            self.initCase(case)
        self.cases[case]['accuracy'].append(acc)
        if acc > self.bestacc:
            self.bestacc = acc
            self.bestfold = case[5]

    def addLoss(self, case, loss):
        if case not in self.cases:
            self.initCase(case)
        self.cases[case]['losses'].append(loss)

    def displayTrainEvalAcc(self, model_name, dataset_name, epochs):
        epochs = list(range(1, epochs+1))
        plt.rcParams.update({'font.size': 18})
        plt.figure(figsize=(8, 5))

        folds = sorted({int(k[len('train'):]) for k in self.cases if k.startswith('train')})
        train_mat = np.vstack([self.cases[f'train{f}']['accuracy'] for f in folds])
        valid_mat = np.vstack([self.cases[f'valid{f}']['accuracy'] for f in folds])

        mean_train = train_mat.mean(axis=0)
        std_train  = train_mat.std(axis=0)
        mean_valid = valid_mat.mean(axis=0)
        std_valid  = valid_mat.std(axis=0)

        plt.plot(epochs, mean_train,  color='blue',  lw=2, label='Mean training accuracy')
        plt.fill_between(epochs,
                        mean_train - std_train,
                        mean_train + std_train,
                        color='blue', alpha=0.2)

        plt.plot(epochs, mean_valid, color='orange', lw=2, label='Mean validation accuracy', linestyle='--')
        plt.fill_between(epochs,
                        mean_valid - std_valid,
                        mean_valid + std_valid,
                        color='orange', alpha=0.2)

        cmap = plt.get_cmap('Set2')
        y_min, y_max = plt.ylim()
        for i, (xmin, xmax, lr) in enumerate(self.lr_regions):
            color = cmap(i % cmap.N)
            plt.axvspan(xmin, xmax, color=color, alpha=0.3)
            xmid = (xmin + xmax) / 2
            yloc = y_max - 0.5 * (y_max - y_min)
            plt.text(xmid, yloc, f'lr:{lr:.0e}',
                    ha='center', va='center', alpha=0.8)

        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.ylim(top=1)
        # Add a caption describing the plot. [Quale e' il messaggio di questo plot, cosa devo guardare?]
        plt.legend(loc='lower right')
        plt.grid(False)
        plt.tight_layout()
        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = f'pysrc/metric_plots/training_acc_{model_name}_{dataset_name}_{now}.png'
        plt.savefig(out)
        plt.close()
        print(f'Saved training chart to {out}')

    def saveEvalResults(self, model_name):
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
        out_filename = f"pysrc/metric_plots/results_{model_name}.csv"
        with open(out_filename, 'w', newline='') as fp:
            writer = csv.writer(fp)
            writer.writerow(['metric', 'mean', 'std'])
            for metric_name, mean, std in summary:
                writer.writerow([metric_name, f"{mean:.6f}", f"{std:.6f}"])

        print(f"Saved evaluation summary to {out_filename}")


    def displayLosses(self, model_name, dataset_name):
        all_epochs = []
        for k, case in self.cases.items():
            if k.startswith("train"):
                all_epochs += [epoch for (_, epoch) in case["losses"]]
        n_epochs = max(all_epochs) + 1       # e.g. 0..9 → 10 epochs
        epoch_indices = np.arange(1, n_epochs+1)

        fold_ids = sorted(int(k[len("train"):]) for k in self.cases if k.startswith("train"))
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

        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.legend()
        plt.grid(False)
        plt.tight_layout()
        plt.rcParams.update({'font.size': 18})
        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = f"pysrc/metric_plots/training_loss_{model_name}_{dataset_name}_{now}.png"
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
        

    def displayConfMatrixPlot(self, case, model_name, dataset_name):
        n_matrices = len(self.cases[case]['cms'])
        file_ct = 1
        if('evalu' in case):
            rows = 2; cols = 3; xsize = 10; ysize = 8
        else:
            rows = 4; cols = 5; xsize = 12; ysize = 9

        while(n_matrices > 0):
            fig, axes = plt.subplots(rows, cols, figsize=(xsize, ysize))
            
            for ax, cm, title in zip(axes.flatten(), self.cases[case]['cms'], self.cases[case]['cms_names']):
                disp = ConfusionMatrixDisplay(confusion_matrix=cm)
                disp.plot(ax=ax, values_format='d', cmap='Blues', colorbar=False)
                ax.set_title(title)

            plt.tight_layout()
            plt.savefig(f'pysrc/metric_plots/confusions/{case}{file_ct}__{model_name}__{dataset_name}_{datetime.now().strftime("%Y%m%d-%H:%M:%S.%f")[:-3]}.png')
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

        print(f"{mode} | Kfold: [{kfold}] Epoch: [{epoch_no:>3d}\{epochs:>3d}] [{curr_len:>6d}/{dataset_len:>6d}] Loss: {loss:>5f} Accuracy: {acc_str}")

    def redLog(self, string):
        return f'{RED}{(string):.3f}%{RESET}'
    
    def greenLog(self, string):
        return f'{GREEN}{(string):.3f}%{RESET}'

        
