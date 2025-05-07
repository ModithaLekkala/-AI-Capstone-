import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay        
import numpy as np
from datetime import datetime

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


class MetricsManager():
    def __init__(self, init_lr, init_epochs, scheduler, hidden_layers, distilled):
        self.cases = {}
        self.bestacc = -np.inf
        self.bestfold = 0
        self.init_lr = init_lr
        self.curr_lr = init_lr
        self.lr_regions = set()
        self.epochs = init_epochs
        self.scheduler = scheduler
        self.hidden_layers = hidden_layers
        self.distilled = distilled

    def initCase(self, case):
        self.cases[case] = {
            'cms': [],
            'cms_names': [],
            'accuracies': [],
            'losses': []
        }

    def addLr(self, region: tuple):
        lr, epoch = region
        
        if (lr != self.curr_lr):
            if len(self.lr_regions) == 0:
                self.lr_regions.add((1, epoch, self.curr_lr))
            else:
                _, last_epoch, _ = list(self.lr_regions)[0]
                self.lr_regions.add((last_epoch, epoch, self.curr_lr))
            self.curr_lr = lr
        elif epoch == self.epochs:
            if len(self.lr_regions) == 0:
                self.lr_regions.add((1, epoch, self.curr_lr))
            else:
                _, last_epoch, _ = list(self.lr_regions)[0]
                self.lr_regions.add((last_epoch, epoch, self.curr_lr))
        

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

        for case in self.cases.keys():
            fold=case[5]
            accuracies = self.cases[case]['accuracies']
            linewidth = 0.7
            marker=''
            label_train=None
            label_valid=None

            if self.bestfold in case:
                linewidth = 3
                marker='o'
                label_train=f'Best fold {fold} training accuracy'
                label_valid=f'Best fold {fold} validation accuracy'

            if 'train' in case:
                plt.plot(epochs, accuracies, linewidth = linewidth,marker=marker, label=label_train)
                
            if 'valid' in case:
                plt.plot(epochs, accuracies, linewidth = linewidth, linestyle='dashed', marker=marker, label=label_valid)


        # lr ragions (PLATEAU scheduler)
        cmap = plt.get_cmap('Set2')

        y_min, y_max = plt.ylim()
        regions = list(self.lr_regions)

        for i, (xmin, xmax, lr) in enumerate(regions):
            color = cmap(i % cmap.N) 
            plt.axvspan(xmin, xmax, color=color, alpha=0.3)
            yloc = y_max - 0.5 * (y_max - y_min)
            xmid = (xmin + xmax) / 2
            plt.text(xmid, yloc, f'lr:{lr:.0e}',
                    ha='center', va='center',
                    fontsize=10,
                    alpha=0.8)
            
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.ylim(top=1)
        plt.title(f'Training {model_name.upper()} model \nBalanced dataset: {dataset_name.upper()} \nLr scheduler: {self.scheduler} \nInit_lr: {self.init_lr} \nNeurons: {self.hidden_layers} \nDistilled: {self.distilled}')
        plt.legend(loc='lower right')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f'pysrc/metric_plots/training_acc_{model_name}_{dataset_name}_{self.distilled}_{datetime.now().strftime("%Y%m%d-%H:%M:%S.%f")[:-3]}.png')

    def displayLosses(self, model_name, dataset_name):
        plt.figure(figsize=(8, 5))

        for case in self.cases.keys():
            if 'train' in case:
                fold=case[5]
                losses = self.cases[case]['losses']
                x = []
                y = []

                for (loss, epoch) in losses:
                    x.append(epoch), y.append(loss)

                plt.plot(x, y, linewidth=0.7)
                plt.xlabel('Epoch')
                plt.ylabel('Loss')
                plt.title(f'{model_name.upper()} {dataset_name.upper()} loss over training time')
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(f'pysrc/metric_plots/training_loss__{model_name}_{dataset_name}_fold{fold}__{datetime.now().strftime("%Y%m%d-%H:%M:%S.%f")[:-3]}.png')



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

        
