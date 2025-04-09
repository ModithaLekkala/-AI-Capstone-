import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay        
import math

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


class MetricsManager():
    def __init__(self, case_names, subplots_per_fig=10):
        self.subplots_per_fig = subplots_per_fig
        self.cases = {}
        for name in case_names:
            self.cases[name] = {
                'cms': [],
                'cms_names': []
            }
        
            
    def addConfMatrix(self, case, y_true, y_pred, title=None):
        cm = confusion_matrix(y_true, y_pred)
        self.cases[case]['cms'].append(cm)
        if title != None:
            self.cases[case]['cms_names'].append(title)
        else:
            self.cases[case]['cms_names'].append('DEFAULT TITLE')
        

    def displayConfMatrixPlot(self, case):
        n_matrices = len(self.cases[case]['cms'])
        rows = 2
        cols = 5
        fig, axes = plt.subplots(rows, cols, figsize=(12, 6))
        file_ct = 1
        while(n_matrices > 0):
            for ax, cm, title in zip(axes.flatten(), self.cases[case]['cms'], self.cases[case]['cms_names']):
                disp = ConfusionMatrixDisplay(confusion_matrix=cm)
                disp.plot(ax=ax, values_format='d', cmap='Blues', colorbar=False)
                ax.set_title(title)

            plt.tight_layout()
            plt.savefig(f'pysrc/metric_plots/{case}{file_ct}.png')
            file_ct += 1
            n_matrices -= 10 # each png file contains 10 epoch conf matrices

        self.cases[case] = None

    def batchLog(self, mode, epoch_no, curr_len, dataset_len, loss, acc):
        if(acc < 0.7):
            acc_str = self.redLog(acc*100)
        elif(acc > 0.92):
            acc_str = self.greenLog(acc*100)
        else:
            acc_str = f'{acc*100:.3f}%'

        print(f"{mode} | Epoch: [{epoch_no}] [{curr_len:>6d}/{dataset_len:>6d}] Loss: {loss:>5f} Accuracy: {acc_str}")

    def redLog(self, string):
        return f'{RED}{(string):.3f}%{RESET}'
    
    def greenLog(self, string):
        return f'{GREEN}{(string):.3f}%{RESET}'
        
