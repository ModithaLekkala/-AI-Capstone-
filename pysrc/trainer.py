import os
import ast
import pandas as pd

from utils import get_model_cfg, data_preprocess, data_binarization, get_distillation_cfg, metrics_binary_dataset
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
from sklearn.model_selection import train_test_split


TRAIN = 'train'
VALID = 'valid'
EVALU = 'evalu'
TRAIN_DATASET_PATH = '/home/sgeraci/slu/inet-hynn/datasets/UNSW_NB15_training-set.csv'
EVALU_DATASET_PATH = '/home/sgeraci/slu/inet-hynn/datasets/UNSW_NB15_testing-set.csv'

class Trainer():
    def __init__(self, args):
        self.args = args

        # randomness
        self.random_seed = 42
        gen = torch.manual_seed(self.random_seed)

        # init
        self.cfg = get_model_cfg()
        self.num_classes = self.cfg.getint('MODEL', 'NUM_CLASSES')
        self.dataset = self.cfg.get('MODEL', 'DATASET')
        self.selected_feats = ['sttl', 'ct_srv_dst', 'ct_dst_src_ltm', 'ct_srv_src', 'sbytes', 'smean', 'synack', 'dmean', 'tcprtt', 'ct_src_ltm', 'dbytes', 'service', 'ct_dst_sport_ltm', 'dloss', 'dload', 'ct_dst_ltm', 'sloss', 'swin', 'label']
        self.dataset_name = 'balanced' if self.args.balance_dataset else 'vanilla'
        self.kfolder = StratifiedShuffleSplit(n_splits=self.args.folds, test_size=0.1, random_state=self.random_seed)
        self.kfold_idx = 1
        self.best_acc = -np.inf
        self.metrics_manager = MetricsManager(self.args.lr, self.args.epochs, self.args.scheduler, ast.literal_eval(self.cfg.get('MODEL', 'OUT_FEATURES')), self.args.distilled, self.args.weight_decay)
        
        if self.args.distilled:
            self.model_name = 'distilled'
        elif self.args.quantized:
            self.model_name = 'bnn' 
        else:
            self.model_name = 'full'
        
        # preprocess dataset and dataloader
        if self.dataset == 'UNSW_NB15':
            self.builder = UNSW_NB15_Dataset
            data_tr = pd.read_csv(TRAIN_DATASET_PATH, delimiter=',')
            data_te = pd.read_csv(EVALU_DATASET_PATH, delimiter=',')
            dict = {
                'categorical_features_values': 6,
                'continuous_features_values': 50,
                'list_drop': [
                    'id',
                    'attack_cat'
                ]
            }

            # split feats and labels from eval set
            x_tmp = data_te[data_te.columns[-1]]
            y_tmp = data_te[data_te.columns[:-1]]

            # generate test set from evaluation dataset and attach the remaining part to the training dataset  
            x_tmp_tr, x_tmp_te, y_tmp_tr, y_tmp_te = train_test_split(x_tmp, y_tmp, test_size=0.3, random_state=self.random_seed)

            # merge features and labels again
            tmp     = pd.concat([y_tmp_tr, x_tmp_tr], axis=1)
            data_te = pd.concat([y_tmp_te, x_tmp_te], axis=1)
            
            # attach remaining to training
            data_tr = pd.concat([data_tr, tmp], ignore_index=True)

            # feature selection
            data_tr = data_tr[self.selected_feats]
            data_te = data_te[self.selected_feats]

            print('\nDATASETS PREPROCESSING')
            X_tr_df, self.Y_tr, _ = data_preprocess(data_tr, dict, binarization=self.args.quantized)
            X_te_df, Y_te, _ = data_preprocess(data_te, dict, binarization=self.args.quantized)


            # keep track of indeces to split again after
            train_idx = X_tr_df.shape[0]
            # merge tr and te to binarized together
            X_tmp = pd.concat([X_tr_df, X_te_df], ignore_index=True)

        Xbin, _ = data_binarization(X_tmp.astype('int'))

        # split again
        Xbin_tr = Xbin[:train_idx]
        Xbin_te = Xbin[train_idx:]

        # dataset prep termined
        self.X_tr = torch.tensor(Xbin_tr, dtype=torch.float32)
        self.X_te = torch.tensor(Xbin_te, dtype=torch.float32)

        self.nn_size = self.X_tr.shape[1]
    
        self.test_dataloader = DataLoader(UNSW_NB15_Dataset(self.X_te, Y_te), batch_size=self.args.batch_size, shuffle=False)
        
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
            self.T = dist_cfg.getfloat('DISTILLATION', 'T')
            weight = torch.load(self.teacher_path)
            self.teacher = deeper(self.cfg, self.nn_size) 
            self.teacher.load_state_dict(weight)
            

        if self.args.subset_size:
            N = len(self.Y_tr)
            S = min(args.subset_size, N)
            # generate a shuffled permutation of indices [0..N-1]
            perm = torch.randperm(N, generator=gen)
            # take the first S indices
            sel = perm[:S]
            # subset X and Y
            self.X_tr = self.X_tr[sel]
            self.Y_tr = self.Y_tr[sel]

    def train_model(self):
        torch.autograd.set_detect_anomaly(True)

        # cross validation and get best fold
        best_fold_w = self.cross_validate_model()

        # retraining best fold on the entire dataset
        print('\nFinal model training:')
        self.model.load_state_dict(best_fold_w)
        final_w, final_acc = self.train(self.X_tr, self.Y_tr)

        #TODO Make hyperparameters search and make last training from 0 with that found params
        
        # export
        best_fold_out = f'{self.args.checkpoints_path}/best_fold_{self.model_name}_{self.dataset_name}_acc{final_acc:.3f}.pth'
        final_out = f'{self.args.checkpoints_path}/final_{self.model_name}_{self.dataset_name}_acc{final_acc:.3f}.pth'
        torch.save(best_fold_w, best_fold_out)
        torch.save(final_w, final_out)
        print(f'Best fold model saved in {best_fold_out}')
        print(f'Final model saved in {final_out}')
        

    def cross_validate_model(self):
        for train_ids, val_ids in self.kfolder.split(self.X_tr, self.Y_tr):
            print(f'\n{10*"*"} CROSS VALIDATION FOLD {self.kfold_idx} {10*"*"}\n')
            self.model = self.model_f(self.cfg, self.nn_size).to(device=self.device)
            self.train_case = f'{TRAIN}{self.kfold_idx}'
            self.valid_case = f'{VALID}{self.kfold_idx}'
            self.evalu_case = f'{EVALU}{self.kfold_idx}'

            # loss
            if self.args.loss == 'SqrHinge':
                self.criterion = SqrHingeLoss()
                self.model.features.append(nn.Tanh())
            elif self.args.loss == 'CrossEntropy':
                self.criterion = nn.CrossEntropyLoss()
            else:
                raise ValueError(f"{self.args.loss} not supported.")
            self.criterion = self.criterion.to(device=self.device)
        
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
            
            # train fold
            fold_w, fold_acc = self.train(self.X_tr[train_ids], self.Y_tr[train_ids], self.X_tr[val_ids], self.Y_tr[val_ids])

            # evaluate fold
            self.eval_model()

            if self.best_acc < fold_acc:
                self.best_acc = fold_acc
                self.best_fold = fold_w
            
            self.kfold_idx+=1
            
            # self.metrics_manager.displayConfMatrixPlot(self.train_case, dataset_name=self.dataset_name, model_name=f'{self.model_name}_kfold{self.kfold_idx}')
            # self.metrics_manager.displayConfMatrixPlot(self.valid_case, dataset_name=self.dataset_name, model_name=f'{self.model_name}_kfold{self.kfold_idx}')
                
        # if self.args.distilled:
        #     binw = self.model.get_bin_weights()
        #     binw[binw == -1] = 0
        #     for ix, layerw in enumerate(binw):
        #         print(f"Layer {ix} binarized weights shape: {layerw.shape}")
        self.metrics_manager.displayTrainEvalAcc(self.model_name, self.dataset_name, self.args.epochs)
        self.metrics_manager.displayLosses(self.model_name, self.dataset_name)
        self.metrics_manager.saveEvalResults(self.model_name)


        return self.best_fold

    def train(self, X, Y, X_val=None, Y_val=None):
        dataset = UNSW_NB15_Dataset(X, Y)
        sampler = ImbalancedDatasetSampler(dataset, Y if self.args.balance_dataset else None)
        dataloader = DataLoader(dataset, batch_size=self.args.batch_size, shuffle=True if not self.args.balance_dataset else None)
            
        fold_acc = -np.inf

        for self.epoch in range(1, self.args.epochs+1):
            preds = np.array([])
            truth = np.array([])

            self.model.train()
            self.criterion.train()

            for batch, (X_tr, Y_tr) in enumerate(dataloader):
                if isinstance(self.criterion, SqrHingeLoss):
                    target = Y_tr.unsqueeze(1)
                    target_onehot = torch.Tensor(target.size(0), 2)
                    target_onehot.fill_(-1)
                    target_onehot.scatter_(1, target, 1)
                    target = target.squeeze()
                    target_var = target_onehot
                else:
                    target_var = Y_tr


                pred = self.model(X_tr)

                if self.args.distilled:
                    with torch.no_grad():
                        teacher_logits = self.teacher(X_tr)
                    student_logits = pred

                    soft_targets = nn.functional.softmax(teacher_logits / self.T, dim=-1)
                    soft_prob = nn.functional.log_softmax(student_logits / self.T, dim=-1)

                    soft_targets_loss = torch.sum(soft_targets * (soft_targets.log() - soft_prob)) / soft_prob.size()[0] * (self.T**2)
                    label_loss = self.criterion(student_logits, target_var)
                    loss = self.soft_target_loss_weight * soft_targets_loss + self.ce_loss_weight * label_loss
                else:
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
                self.metrics_manager.addLoss(self.train_case, (loss.item(), self.epoch))

                if(batch % self.args.log_freq == 0):
                    loss, current = loss.item(), batch * dataloader.batch_size + len(X_tr)     
                    self.metrics_manager.batchLog(mode=TRAIN, epoch_no=self.epoch, curr_len=current, dataset_len=len(dataloader.dataset), loss=loss, acc=acc, kfold=self.kfold_idx, epochs=self.args.epochs)

                preds = np.hstack((preds, cls))
                truth = np.hstack((truth, Y_tr))

            # statistics
            acc = (preds == truth).mean()
            self.metrics_manager.addAcc(self.train_case, acc)
            self.metrics_manager.addConfMatrix(self.train_case, truth, preds, f'Epoch n{self.epoch}')
            
            if(X_val is not None and Y_val is not None):
                with torch.no_grad():
                    valid_acc, valid_loss = self.val_model(X_val, Y_val)
                acc_cmp = valid_acc
            else:
                acc_cmp = acc

            if(fold_acc < acc_cmp):
                fold_acc = acc_cmp
                fold_weights = self.model.state_dict()

            # lr decay
            if self.scheduler != None:
                self.scheduler.step(valid_loss)
                self.metrics_manager.addLr((self.optimizer.param_groups[0]['lr'], self.epoch))
            
        return fold_weights, fold_acc


    def val_model(self, X, Y):
        dataset = UNSW_NB15_Dataset(X, Y)
        dataloader = DataLoader(dataset, batch_size=self.args.batch_size, shuffle=False)
  
        preds = np.array([])
        truth = np.array([])
        losses = np.array([])
        
        self.model.eval()
        self.criterion.eval()

        for _, (X_val, Y_val) in enumerate(dataloader):
            if isinstance(self.criterion, SqrHingeLoss):
                target = Y_val.unsqueeze(1)
                target_onehot = torch.Tensor(target.size(0), 2)
                target_onehot.fill_(-1)
                target_onehot.scatter_(1, target, 1)
                target = target.squeeze()
                target_var = target_onehot
            else:
                target_var = Y_val

            # forward pass
            pred = self.model(X_val)
            loss = self.criterion(pred, target_var)

            if hasattr(self.model, 'clip_weights'):
                self.model.clip_weights(-1, 1)

            if self.args.loss == 'SqrHinge':
                cls = pred.argmax(1).round()
            elif self.args.loss == 'CrossEntropy':
                cls = F.softmax(pred, dim=1).argmax(1)
                
            self.metrics_manager.addLoss(self.valid_case, (loss.item(), self.epoch))

            preds = np.hstack((preds, cls))
            truth = np.hstack((truth, Y_val))
            losses = np.hstack((losses, loss.item()))
    
        # statistics
        avg_acc = (preds == truth).mean()
        avg_loss = losses.mean()
        self.metrics_manager.addAcc(self.valid_case, avg_acc)
        self.metrics_manager.addConfMatrix(self.valid_case, truth, preds, f'Epoch n{self.epoch}')
        self.metrics_manager.batchLog(mode=VALID, epoch_no=self.epoch, curr_len=0, dataset_len=len(dataloader.dataset), loss=loss, acc=avg_acc, kfold=self.kfold_idx, epochs=self.args.epochs)
        print('\n')

        return avg_acc, avg_loss
    

    def eval_model(self):
        preds = np.array([])
        truth = np.array([])

        self.model.eval()
        for _, (X_test, Y_test) in enumerate(self.test_dataloader):

            # compute output
            pred = self.model(X_test)

            if self.args.loss == 'SqrHinge':
                cls = pred.argmax(1).round()
            elif self.args.loss == 'CrossEntropy':
                cls = F.softmax(pred, dim=1).argmax(1)
            cls = cls.detach().numpy()

            preds = np.hstack((preds, cls))
            truth = np.hstack((truth, Y_test))

        # add stats 
        a, p, r, _, _, _, f1, _ = metrics_binary_dataset(truth, preds, pd.get_dummies(preds).values)
        self.metrics_manager.addAcc(self.evalu_case, a)
        self.metrics_manager.addPrec(self.evalu_case, p)
        self.metrics_manager.addRec(self.evalu_case, r)
        self.metrics_manager.addF1(self.evalu_case, f1)
        self.metrics_manager.addConfMatrix(self.evalu_case, truth, preds, f'Epoch n{self.epoch}')