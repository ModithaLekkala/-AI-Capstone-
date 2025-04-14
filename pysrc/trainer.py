import os
import pandas as pd

from utils import get_model_cfg, data_preprocess, data_binarization
from configparser import ConfigParser
from datasets import UNSW_NB15_Dataset
from torch.utils.data import DataLoader

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
import torch.nn.functional as F 
import numpy as np

from losses import SqrHingeLoss
from metrics import MetricsManager

from torchsampler import ImbalancedDatasetSampler

from models import smaller, deeper


class Trainer():
    def __init__(self, args):
        self.args = args

        # gather configurations
        self.cfg = get_model_cfg()
        self.num_classes = self.cfg.getint('MODEL', 'NUM_CLASSES')
        self.dataset = self.cfg.get('MODEL', 'DATASET')
        
        # preprocess dataset and dataloader
        if self.dataset == 'UNSW_NB15':
            self.builder = UNSW_NB15_Dataset
            data_tr = pd.read_csv('/home/sgeraci/slu/inet-hynn/datasets/UNSW_NB15_training-set.csv', delimiter=',')
            data_te = pd.read_csv('/home/sgeraci/slu/inet-hynn/datasets/UNSW_NB15_testing-set.csv', delimiter=',')
            dict = {
                'categorical_features_values': 6,
                'continuous_features_values': 50,
                'list_drop': [
                    'id',
                    'attack_cat'
                ]
            }

            print()
            print('TRAINING SET PREPROCESSING')
            X_tr, Y_tr, Xbin_tr, Xbin_desc_tr,_, _ = data_preprocess(data_tr, dict, binarization=self.args.quantized)
            print()
            print('TESTING SET PREPROCESSING')
            X_te, Y_te, Xbin_te, Xbin_desc_te, _, _ = data_preprocess(data_te, dict, binarization=self.args.quantized)

        train_dataset = self.builder(Xbin_tr if self.args.quantized else X_tr, Y_tr)
        test_dataset = self.builder(Xbin_te if self.args.quantized else X_te, Y_te)
        
        # balancer for unbalanced dataset
        tr_shuffle = True
        tr_sampler = None
        if self.args.balance_dataset:
            tr_shuffle = False
            tr_sampler = ImbalancedDatasetSampler(train_dataset)

        self.train_dataloader = DataLoader(train_dataset, batch_size=self.args.batch_size, sampler=tr_sampler, shuffle=tr_shuffle)
        self.test_dataloader = DataLoader(test_dataset, batch_size=self.args.batch_size, shuffle=False)
        
        # set model and evaluation metrics
        self.device = torch.device('cpu')
        if self.args.quantized:
            assert sum(Xbin_desc_tr.values()) == sum(Xbin_desc_te.values())
            self.nn_size = sum(Xbin_desc_tr.values())
            self.model = smaller(self.cfg, self.nn_size)
        else:
            assert X_tr.shape[1] == X_te.shape[1]
            self.nn_size = X_tr.shape[1]
            self.model = deeper(self.cfg, self.nn_size)
        self.model = self.model.to(device=self.device)

        self.epoch = 0
        self.best_val_acc = 0

        # loss
        if args.loss == 'SqrHinge':
            self.criterion = SqrHingeLoss()
            self.model.seq.append(nn.Tanh())
        elif args.loss == 'CrossEntropy':
            self.criterion = nn.CrossEntropyLoss()
        else:
            raise ValueError(f"{args.loss} not supported.")
        self.criterion = self.criterion.to(device=self.device)

        # optimizer
        if args.optim == 'ADAM':
            self.optimizer = optim.Adam(
                self.model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
        elif args.optim == 'SGD':
            self.optimizer = optim.SGD(
                self.model.parameters(),
                lr=self.args.lr,
                momentum=self.args.momentum,
                weight_decay=self.args.weight_decay)
        
        # LR scheduler
        if args.scheduler == 'PLATEAU':
            self.scheduler = ReduceLROnPlateau(optimizer=self.optimizer, patience=args.patience, verbose=True, min_lr=1e-6)
        elif args.scheduler == 'FIXED':
            self.scheduler = None
        else:
            raise Exception("Unrecognized scheduler {}".format(self.args.scheduler))
        
        self.metrics_manager = MetricsManager(['train', 'test'])
        self.reset_stats()


    def train_model(self):
        torch.autograd.set_detect_anomaly(True)
        best_acc = -np.inf

        for epoch in range(0, self.args.epochs):
            self.model.train()
            self.criterion.train()

            for batch, (X, Y) in enumerate(self.train_dataloader):
                if isinstance(self.criterion, SqrHingeLoss):
                    target = Y.unsqueeze(1)
                    target_onehot = torch.Tensor(target.size(0), 2)
                    target_onehot.fill_(-1)
                    target_onehot.scatter_(1, target, 1)
                    target = target.squeeze()
                    target_var = target_onehot
                else:
                    target_var = Y

                # forward pass
                pred = self.model(X)
                loss = self.criterion(pred, target_var)
                # backpropagation
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                if self.args.loss == 'SqrHinge':
                    cls = pred.argmax(1).round()
                elif self.args.loss == 'CrossEntropy':
                    cls = F.softmax(pred, dim=1).argmax(1)
                    
                if(batch % self.args.log_freq == 0):
                    loss, current = loss.item(), batch * self.train_dataloader.batch_size + len(X)     
                    acc = (cls == Y).float().mean()                    
                    self.metrics_manager.batchLog('Train', epoch, current, len(self.train_dataloader.dataset), loss, acc)

                self.per_epoch_tr_pred  = torch.concat([self.per_epoch_tr_pred, cls])
                self.per_epoch_tr_truth = torch.concat([self.per_epoch_tr_truth, Y])

            with torch.no_grad():
                val_loss, val_acc = self.eval_model(epoch)

            # lr decay
            if self.scheduler != None:
                self.scheduler.step(val_loss)
            # add epoch confusion matrix to stats 
            self.metrics_manager.addConfMatrix('train', self.per_epoch_tr_truth, self.per_epoch_tr_pred, f'Epoch n{epoch}')
            self.reset_stats()

            if(best_acc < val_acc):
                best_acc = val_acc
                model_name = 'bnn' if self.args.quantized else 'full'
                dataset_name = 'balanced' if self.args.balance_dataset else 'vanilla'
                torch.save(self.model.state_dict(), f'{self.args.checkpoints_path}/{model_name}_{dataset_name}_acc{val_acc:.3f}.pth')

        self.metrics_manager.displayConfMatrixPlot('train', kwargs='balanced' if self.args.balance_dataset else 'vanilla')
        self.metrics_manager.displayConfMatrixPlot('test', kwargs='balanced' if self.args.balance_dataset else 'vanilla')


    def eval_model(self, epoch):
        self.model.eval()
        self.criterion.eval()

        accuracies = []
        losses = []

        for batch, (X, Y) in enumerate(self.test_dataloader):
            
            # for hingeloss only
            if isinstance(self.criterion, SqrHingeLoss):
                target = Y.unsqueeze(1)
                target_onehot = torch.Tensor(target.size(0), 2)
                target_onehot.fill_(-1)
                target_onehot.scatter_(1, target, 1)
                target = target.squeeze()
                target_var = target_onehot
            else:
                target_var = Y

            # compute output
            pred = self.model(X)
            loss = self.criterion(pred, target_var)

            # compute loss
            loss, current = loss.item(), batch * self.train_dataloader.batch_size + len(X)
            if self.args.loss == 'SqrHinge':
                cls = pred.argmax(1).round()
                acc = (cls == Y).float().mean()
            elif self.args.loss == 'CrossEntropy':
                cls = F.softmax(pred, dim=1).argmax(1)
                acc = (cls == Y).float().mean()
            
            accuracies.append(acc)
            losses.append(loss)
            self.metrics_manager.batchLog('Valid', epoch, current, len(self.test_dataloader.dataset), loss, acc)
            self.per_epoch_te_pred  = torch.concat([self.per_epoch_te_pred, cls])
            self.per_epoch_te_truth = torch.concat([self.per_epoch_te_truth, Y])

        # add epoch confusion matrix to stats 
        self.metrics_manager.addConfMatrix('test', self.per_epoch_te_truth, self.per_epoch_te_pred, f'Epoch n{epoch}')
        return np.array(losses).mean(), np.array(accuracies).mean()
    
    def reset_stats(self):
        self.per_epoch_tr_pred = torch.tensor([])
        self.per_epoch_te_pred = torch.tensor([])
        self.per_epoch_tr_truth = torch.tensor([])
        self.per_epoch_te_truth = torch.tensor([])
            
        


        



