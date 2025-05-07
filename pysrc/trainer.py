import os
import ast
import pandas as pd

from utils import get_model_cfg, data_preprocess, data_binarization, get_distillation_cfg
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
from sklearn.model_selection import StratifiedShuffleSplit


TRAIN = 'train'
VALID = 'valid'
TRAIN_DATASET_PATH = '/home/sgeraci/slu/inet-hynn/datasets/UNSW_NB15_training-set.csv'
VALID_DATASET_PATH = '/home/sgeraci/slu/inet-hynn/datasets/UNSW_NB15_testing-set.csv'

class Trainer():
    def __init__(self, args):
        self.args = args

        # randomness
        self.random_seed = 42
        torch.manual_seed(self.random_seed)

        # init
        self.cfg = get_model_cfg()
        self.num_classes = self.cfg.getint('MODEL', 'NUM_CLASSES')
        self.dataset = self.cfg.get('MODEL', 'DATASET')
        self.selected_feats = ['sttl', 'ct_srv_dst', 'ct_dst_src_ltm', 'ct_srv_src', 'sbytes', 'smean', 'synack', 'dmean', 'tcprtt', 'ct_src_ltm', 'dbytes', 'service', 'ct_dst_sport_ltm', 'dloss', 'dload', 'ct_dst_ltm', 'sloss', 'swin', 'label']
        self.model_name = 'bnn' if self.args.quantized else 'full'
        self.dataset_name = 'balanced' if self.args.balance_dataset else 'vanilla'
        self.kfolder = StratifiedShuffleSplit(n_splits=self.args.folds, test_size=0.2, random_state=self.random_seed)
        self.kfold_idx = 0
        self.best_acc = -np.inf
        self.metrics_manager = MetricsManager(self.args.lr, self.args.epochs, self.args.scheduler, ast.literal_eval(self.cfg.get('MODEL', 'OUT_FEATURES')), self.args.distilled)
        self.reset_stats()
        
        # preprocess dataset and dataloader
        if self.dataset == 'UNSW_NB15':
            self.builder = UNSW_NB15_Dataset
            data_tr = pd.read_csv(TRAIN_DATASET_PATH, delimiter=',')
            data_te = pd.read_csv(VALID_DATASET_PATH, delimiter=',')
            dict = {
                'categorical_features_values': 6,
                'continuous_features_values': 50,
                'list_drop': [
                    'id',
                    'attack_cat'
                ]
            }

            data = pd.concat([data_tr, data_te], ignore_index=True)
            data = data[self.selected_feats]

            labels=data[data.columns[-1]]
            print(f'{sum(labels)} samples of class 1')
            print(f'{len(labels) - sum(labels)} samples of class 0')
            print('\nDATASETS PREPROCESSING')
            X_df, self.Y, _ = data_preprocess(data, dict, binarization=self.args.quantized)
 
        Xbin, _ = data_binarization(X_df.astype('int'))
        self.X = torch.tensor(Xbin, dtype=torch.float32)
        self.nn_size = self.X.shape[1]
    
        self.device = torch.device('cpu')
        if self.args.quantized:
            self.model_f = smaller
        else:
            self.model_f = deeper
        
        if self.args.distilled:
            dist_cfg = get_distillation_cfg()
            self.teacher_path = dist_cfg.get('TEACHER', 'WEIGHT_PATH')
            self.soft_target_loss_weight = dist_cfg.getfloat('STUDENT', 'TEACHER_LOSS_WEIGHT')
            self.ce_loss_weight = dist_cfg.getfloat('STUDENT', 'STUDENT_LOSS_WEIGHT')
            weight = torch.load(self.teacher_path)
            self.teacher = deeper(self.cfg, self.nn_size) 
            self.teacher.load_state_dict(weight)

        if self.args.subset_size:
            N = len(self.Y)
            S = min(args.subset_size, N)
            # generate a shuffled permutation of indices [0..N-1]
            perm = torch.randperm(N, generator=torch.Generator().manual_seed(self.random_seed))
            # take the first S indices
            sel = perm[:S]
            # subset X and Y
            self.X = self.X[sel]
            self.Y = self.Y[sel]

        # loss
        if args.loss == 'SqrHinge':
            self.criterion = SqrHingeLoss()
            self.model.seq.append(nn.Tanh())
        elif args.loss == 'CrossEntropy':
            self.criterion = nn.CrossEntropyLoss()
        else:
            raise ValueError(f"{args.loss} not supported.")
        self.criterion = self.criterion.to(device=self.device)
        

    def train_model(self):
        torch.autograd.set_detect_anomaly(True)
    
        for train_ids, val_ids in self.kfolder.split(self.X, self.Y):
            print(f'\n{10*"*"} KFOLD {self.kfold_idx} {10*"*"}\n')

            self.model = self.model_f(self.cfg, self.nn_size).to(device=self.device)
            tr_ds = UNSW_NB15_Dataset(self.X[train_ids], self.Y[train_ids])
            val_ds = UNSW_NB15_Dataset(self.X[val_ids], self.Y[val_ids])
            self.sampler = ImbalancedDatasetSampler(tr_ds, self.Y[train_ids]) if self.args.balance_dataset else None
            self.train_dataloader = DataLoader(tr_ds, batch_size=self.args.batch_size, shuffle=True if not self.args.balance_dataset else None, sampler=self.sampler)
            self.valid_dataloader = DataLoader(val_ds, batch_size=self.args.batch_size, shuffle=False)
            self.train_case = f'{TRAIN}{self.kfold_idx}'
            self.valid_case = f'{VALID}{self.kfold_idx}'
            
            # optimizer
            if self.args.optim == 'ADAM':
                self.optimizer = optim.Adam(self.model.parameters(),  lr=self.args.lr, weight_decay=self.args.weight_decay)
            elif self.args.optim == 'SGD':
                self.optimizer = optim.SGD(self.model.parameters(), lr=self.args.lr, momentum=self.args.momentum, weight_decay=self.args.weight_decay)
            else:
                raise Exception(f"Unrecognized optimizer {self.args.scheduler}")

            # LR scheduler
            if self.args.scheduler == 'PLATEAU':
                self.scheduler = ReduceLROnPlateau(optimizer=self.optimizer, patience=self.args.patience, verbose=True, min_lr=1e-7, factor=0.1)
            elif self.args.scheduler == 'FIXED':
                self.scheduler = None
            else:
                raise Exception(f"Unrecognized scheduler {self.args.scheduler}")
            
            # save binary weight in hex format
            if self.args.distilled:
                self.train_fold_distilled()
                binw = self.model.get_bin_weights()
                binw[binw == -1] = 0
                for ix, layerw in enumerate(binw):
                    print(f"Layer {ix} binarized weights shape: {layerw.shape}")


            else:
                self.train_fold()
            
            torch.save(self.model.state_dict(), f'{self.args.checkpoints_path}/bestkfold_{self.kfold_idx}__{self.model_name}_{self.dataset_name}_acc{self.best_acc:.3f}.pth')
            
            self.best_acc = -np.inf
            self.kfold_idx+=1
            
            # self.metrics_manager.displayConfMatrixPlot(self.train_case, dataset_name=self.dataset_name, model_name=f'{self.model_name}_kfold{self.kfold_idx}')
            # self.metrics_manager.displayConfMatrixPlot(self.valid_case, dataset_name=self.dataset_name, model_name=f'{self.model_name}_kfold{self.kfold_idx}')
        
        self.metrics_manager.displayTrainEvalAcc(f'{self.model_name}', self.dataset_name, self.args.epochs)
        self.metrics_manager.displayLosses(f'{self.model_name}', self.dataset_name)

    def train_fold(self):
        for epoch in range(1, self.args.epochs+1):
                
            self.model.train()
            self.criterion.train()

            accuracies = []

            for batch, (X_tr, Y_tr) in enumerate(self.train_dataloader):
                if isinstance(self.criterion, SqrHingeLoss):
                    target = Y_tr.unsqueeze(1)
                    target_onehot = torch.Tensor(target.size(0), 2)
                    target_onehot.fill_(-1)
                    target_onehot.scatter_(1, target, 1)
                    target = target.squeeze()
                    target_var = target_onehot
                else:
                    target_var = Y_tr

                # forward pass
                pred = self.model(X_tr)
                loss = self.criterion(pred, target_var)
                # backpropagation
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                if hasattr(self.model, 'clip_weights'):
                    self.model.clip_weights(-1, 1)

                if self.args.loss == 'SqrHinge':
                    cls = pred.argmax(1).round()
                elif self.args.loss == 'CrossEntropy':
                    cls = F.softmax(pred, dim=1).argmax(1)
                    
                acc = (cls == Y_tr).float().mean()
                accuracies.append(acc.item())
                self.metrics_manager.addLoss(self.train_case, (loss.item(), epoch))

                if(batch % self.args.log_freq == 0):
                    loss, current = loss.item(), batch * self.train_dataloader.batch_size + len(X_tr)     
                    self.metrics_manager.batchLog(mode='Train', epoch_no=epoch, curr_len=current, dataset_len=len(self.train_dataloader.dataset), loss=loss, acc=acc, kfold=self.kfold_idx, epochs=self.args.epochs)

                self.per_epoch_tr_pred  = torch.concat([self.per_epoch_tr_pred, cls])
                self.per_epoch_tr_truth = torch.concat([self.per_epoch_tr_truth, Y_tr])

            with torch.no_grad():
                val_loss, val_acc = self.eval_model(epoch)
            
            self.metrics_manager.addAcc(f'valid{self.kfold_idx}', val_acc)
            self.metrics_manager.addAcc(f'train{self.kfold_idx}', np.mean(accuracies))
            # lr decay
            if self.scheduler != None:
                self.scheduler.step(val_loss)
                self.metrics_manager.addLr((self.optimizer.param_groups[0]['lr'], epoch))
            
            # statistics
            # self.metrics_manager.addConfMatrix(self.train_case, self.per_epoch_tr_truth, self.per_epoch_tr_pred, f'Epoch n{epoch}')
            self.reset_stats()

            if(self.best_acc < val_acc):
                self.best_acc = val_acc
                self.best_fold = self.model.state_dict() 

    def train_fold_distilled(self, T=2):
        for epoch in range(1, self.args.epochs+1):
            self.teacher.eval()
            self.model.train()
            self.criterion.train()

            accuracies = []

            for batch, (X_tr, Y_tr) in enumerate(self.train_dataloader):
                if isinstance(self.criterion, SqrHingeLoss):
                    target = Y_tr.unsqueeze(1)
                    target_onehot = torch.Tensor(target.size(0), 2)
                    target_onehot.fill_(-1)
                    target_onehot.scatter_(1, target, 1)
                    target = target.squeeze()
                    target_var = target_onehot
                else:
                    target_var = Y_tr

                with torch.no_grad():
                    teacher_logits = self.teacher(X_tr)

                # forward pass
                student_logits = self.model(X_tr)
                
                soft_targets = nn.functional.softmax(teacher_logits / T, dim=-1)
                soft_prob = nn.functional.log_softmax(student_logits / T, dim=-1)

                soft_targets_loss = torch.sum(soft_targets * (soft_targets.log() - soft_prob)) / soft_prob.size()[0] * (T**2)
                label_loss = self.criterion(student_logits, target_var)
                loss = self.soft_target_loss_weight * soft_targets_loss + self.ce_loss_weight * label_loss

                # backpropagation
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                if hasattr(self.model, 'clip_weights'):
                    self.model.clip_weights(-1, 1)

                if self.args.loss == 'SqrHinge':
                    cls = student_logits.argmax(1).round()
                elif self.args.loss == 'CrossEntropy':
                    cls = F.softmax(student_logits, dim=1).argmax(1)
                    
                acc = (cls == Y_tr).float().mean()
                accuracies.append(acc.item())
                self.metrics_manager.addLoss(self.train_case, (loss.item(), epoch))

                if(batch % self.args.log_freq == 0):
                    loss, current = loss.item(), batch * self.train_dataloader.batch_size + len(X_tr)     
                    self.metrics_manager.batchLog(mode='Train', epoch_no=epoch, curr_len=current, dataset_len=len(self.train_dataloader.dataset), loss=loss, acc=acc, kfold=self.kfold_idx, epochs=self.args.epochs)

                self.per_epoch_tr_pred  = torch.concat([self.per_epoch_tr_pred, cls])
                self.per_epoch_tr_truth = torch.concat([self.per_epoch_tr_truth, Y_tr])

            with torch.no_grad():
                val_loss, val_acc = self.eval_model(epoch)
            
            self.metrics_manager.addAcc(f'valid{self.kfold_idx}', val_acc)
            self.metrics_manager.addAcc(f'train{self.kfold_idx}', np.mean(accuracies))
            # lr decay
            if self.scheduler != None:
                self.scheduler.step(val_loss)
                self.metrics_manager.addLr((self.optimizer.param_groups[0]['lr'], epoch))
            
            # statistics
            # self.metrics_manager.addConfMatrix(self.train_case, self.per_epoch_tr_truth, self.per_epoch_tr_pred, f'Epoch n{epoch}')
            self.reset_stats()

            if(self.best_acc < val_acc):
                self.best_acc = val_acc
                self.best_fold = self.model.state_dict() 


    def eval_model(self, epoch):
        self.model.eval()
        self.criterion.eval()

        accuracies = []
        losses = []

        for batch, (X_val, Y_val) in enumerate(self.valid_dataloader):
            
            # for hingeloss only
            if isinstance(self.criterion, SqrHingeLoss):
                target = Y_val.unsqueeze(1)
                target_onehot = torch.Tensor(target.size(0), 2)
                target_onehot.fill_(-1)
                target_onehot.scatter_(1, target, 1)
                target = target.squeeze()
                target_var = target_onehot
            else:
                target_var = Y_val

            # compute output
            pred = self.model(X_val)
            loss = self.criterion(pred, target_var)

            # compute loss
            loss, current = loss.item(), batch * self.train_dataloader.batch_size + len(X_val)
            if self.args.loss == 'SqrHinge':
                cls = pred.argmax(1).round()
                acc = (cls == Y_val).float().mean()
            elif self.args.loss == 'CrossEntropy':
                cls = F.softmax(pred, dim=1).argmax(1)
                acc = (cls == Y_val).float().mean()
            
            accuracies.append(acc)
            losses.append(loss)
            self.per_epoch_te_pred  = torch.concat([self.per_epoch_te_pred, cls])
            self.per_epoch_te_truth = torch.concat([self.per_epoch_te_truth, Y_val])

        # add epoch confusion matrix to stats 
        # self.metrics_manager.addConfMatrix(self.valid_case, self.per_epoch_te_truth, self.per_epoch_te_pred, f'Epoch n{epoch}')
        self.metrics_manager.batchLog(mode='Valid', epoch_no=epoch, curr_len=current, dataset_len=len(self.valid_dataloader.dataset), loss=np.array(losses).mean(), acc=np.array(accuracies).mean(), epochs=self.args.epochs, kfold=self.kfold_idx)
        print('\n')
        return np.array(losses).mean(), np.array(accuracies).mean()


    def reset_stats(self):
        self.per_epoch_tr_pred = torch.tensor([])
        self.per_epoch_te_pred = torch.tensor([])
        self.per_epoch_tr_truth = torch.tensor([])
        self.per_epoch_te_truth = torch.tensor([])