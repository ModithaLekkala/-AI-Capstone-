import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay        
import numpy as np
from datetime import datetime

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
            'accuracies': [],
            'losses': []
        }
    
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
        self.cases[case]['accuracies'].append(acc)
        if acc > self.bestacc:
            self.bestacc = acc
            self.bestfold = case[5]

    def addLoss(self, case, loss):
        if case not in self.cases:
            self.initCase(case)
        self.cases[case]['losses'].append(loss)

    def displayTrainEvalAcc(self, model_name, dataset_name, epochs):
        epochs = list(range(1, epochs+1))
        plt.figure(figsize=(10, 6))

        folds = sorted({int(k[len('train'):]) for k in self.cases if k.startswith('train')})
        train_mat = np.vstack([self.cases[f'train{f}']['accuracies'] for f in folds])
        valid_mat = np.vstack([self.cases[f'valid{f}']['accuracies'] for f in folds])

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
                    ha='center', va='center', fontsize=10, alpha=0.8)

        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.ylim(top=1)
        plt.title(
            f'Training {model_name.upper()} model\n'
            f'Balanced dataset: {dataset_name.upper()}\n'
            f'Lr scheduler: {self.scheduler}  Init LR: {self.init_lr:.1e}  '
            f'Weight decay: {self.init_wd}\n'
            f'Neurons: {self.hidden_layers}  Distilled: {self.distilled}'
        )
        plt.legend(loc='lower right')
        plt.grid(True)
        plt.tight_layout()

        # 6) Save
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        plt.savefig(f'pysrc/metric_plots/training_acc_{model_name}_{dataset_name}_{ts}.png')
        plt.close()


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
                        color='tab:blue', alpha=0.2, label="±1 std dev")

        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.title(
            f"{model_name.upper()} {dataset_name.upper()} Training Loss\n"
            f"(Mean ± Std over {len(fold_ids)} folds)"
        )
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = f"pysrc/metric_plots/training_loss_{model_name}_{dataset_name}_{ts}.png"
        plt.savefig(out)
        plt.close()

   
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
        rows = 2
        cols = 5
        file_ct = 1
        while(n_matrices > 0):
            fig, axes = plt.subplots(rows, cols, figsize=(12, 6))
            
            for ax, cm, title in zip(axes.flatten(), self.cases[case]['cms'], self.cases[case]['cms_names']):
                disp = ConfusionMatrixDisplay(confusion_matrix=cm)
                disp.plot(ax=ax, values_format='d', cmap='Blues', colorbar=False)
                ax.set_title(title)

            plt.tight_layout()
            plt.savefig(f'pysrc/metric_plots/confusions/{case}{file_ct}__{model_name}__{dataset_name}_{datetime.now().strftime("%Y%m%d-%H:%M:%S.%f")[:-3]}.png')
            file_ct += 1
            n_matrices -= 10 # each png file contains 10 epoch conf matrices
            self.cases[case]['cms'] = self.cases[case]['cms'][10:]
            self.cases[case]['cms_names'] = self.cases[case]['cms_names'][10:]

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

        
