import os
import ast
import pandas as pd
import json

from utils import get_cfg, data_preprocess, data_binarization, metrics_binary_dataset
from datasets import CommonDataset
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

import json

DATASET_PATH = '/home/sgeraci/Desktop/datasets'

TRAIN = 'train'
VALID = 'valid'
EVALU = 'evalu'
TRAIN_DATASET_PATH = f'{DATASET_PATH}/UNSW-NB15/UNSW_NB15_training-set.csv'
EVALU_DATASET_PATH = f'{DATASET_PATH}/UNSW-NB15/UNSW_NB15_testing-set.csv'

class Trainer():
    def __init__(self, args):
        self.args = args

        # randomness
        self.random_seed = 42
        gen = torch.manual_seed(self.random_seed)

        # init
        self.cfg = get_cfg(self.args.model)
        self.dataset_cfg = get_cfg(self.args.dataset_name)
        self.num_classes = self.cfg.getint('MODEL', 'NUM_CLASSES')
        self.nn_input_size = self.cfg.getint('MODEL', 'INPUT_LAYER')

        self.dataset = self.dataset_cfg.get('DATASET', 'NAME')
        self.dataset_path = self.dataset_cfg.get('DATASET', 'PATH')
        self.dataset_test_path = self.dataset_cfg.get('DATASET', 'TEST_PATH', fallback='')
        self.dataset_dir = os.path.dirname(self.dataset_path)
        self.dataset_name = 'balanced' if self.args.balance_dataset else 'vanilla'

        self.selected_feats = json.loads(self.dataset_cfg.get('DATASET', 'SELECTED_FEATURES'))
        self.last_selected_feats_file = f'{DATASET_PATH}/{self.dataset}/last_selected_features.json'

        self.kfolder = StratifiedShuffleSplit(n_splits=self.args.folds, test_size=0.1, random_state=self.random_seed)
        self.kfold_idx = 1
        self.best_acc = -np.inf
        self.metrics_manager = MetricsManager(self.args.lr, self.args.epochs, self.args.scheduler, ast.literal_eval(self.cfg.get('MODEL', 'OUT_FEATURES')), self.args.distilled, self.args.weight_decay)
        
        if self.args.distilled:
            self.model_name = 'distilled'
        elif self.args.model == 'mbnn' or self.args.model == 'tbnn':
            self.model_name = 'bnn' 
        else:
            self.model_name = 'full'

        bin_ds = f'{self.dataset_dir}/bin_{self.dataset}_{self.nn_input_size}b'

        if os.path.isfile(self.last_selected_feats_file):
            with open(self.last_selected_feats_file, 'r') as f:
                self.last_selected_feats = json.load(f)
            
            if self.last_selected_feats != self.selected_feats:
                print('Last selected features are different the current ones, removing last binarized dataset if exists...', end='')
                if os.path.isfile(bin_ds):
                    os.remove(bin_ds)
                    print('deleted.')
            else:
                print('Last and current selected features match. Continue with dataset loading.')
        else:
            print(f'Saving current selected features to {self.last_selected_feats_file}...', end='')
            with open(self.last_selected_feats_file, 'w') as f:
                json.dump(self.selected_feats, f)
            print('saved.')
        
        # preprocess dataset and dataloader
        if not os.path.isfile(bin_ds):
            self.builder = CommonDataset
            data = pd.read_csv(self.dataset_path, delimiter=',')
            
            if self.dataset_test_path != '':
                data_te = pd.read_csv(self.dataset_test_path, delimiter=',')
                data = pd.concat([data, data_te], axis=0, ignore_index=True)
            
            dict = {
                'categorical_features_values': 6,
                'continuous_features_values': 50,
                'list_drop': [
                    'id',
                    'attack_cat'
                ]
            }

            # feature selection
            data = data[self.selected_feats]
            Y=data[data.columns[-1]]

            print('\nDATASETS PREPROCESSING')
            x_tmp,  _ = data_preprocess(data[data.columns[:-1]], dict)
            Xbin, _ = data_binarization(x_tmp.astype('int'), input_size=self.nn_input_size)
        
            print('Binarized dataset doesn\'t exists, saving it for future references... ', end='')
            pd.concat([pd.DataFrame(Xbin), Y], axis=1).to_csv(bin_ds, index=False)
            print('saved.')
        else:
            print('Binarized dataset exists, load it...', end='')
            data = pd.read_csv(bin_ds)
            Xbin=data[data.columns[:-1]]
            Y=data[data.columns[-1]]
            # print(f'Head(1):\n{Xbin.head(1)}')
            # Xbin = Xbin.to_numpy()
            print(f'loaded.\nNew {self.dataset} shape: {Xbin.shape}', end='')

        Xbin_tr, Xbin_te, Y_tr, Y_te = train_test_split(Xbin, Y, test_size=0.3, random_state=self.random_seed, shuffle=True)
        self.Y_tr = Y_tr.values
        self.Y_te = Y_te.values

        # dataset prep termined
        self.X_tr = torch.tensor(Xbin_tr.values, dtype=torch.float32)
        self.X_te = torch.tensor(Xbin_te.values, dtype=torch.float32)

        self.test_dataloader = DataLoader(CommonDataset(self.X_te, self.Y_te), batch_size=self.args.batch_size, shuffle=True)
        
        self.device = torch.device('cpu')
        if self.args.model == 'mbnn' or self.args.model == 'tbnn':
            self.model_f = smaller
        else:
            self.model_f = deeper
        
        if self.args.distilled:
            dist_cfg = get_cfg('distillation')
            self.teacher_path = dist_cfg.get('TEACHER', 'WEIGHT_PATH')
            self.soft_target_loss_weight = dist_cfg.getfloat('STUDENT', 'TEACHER_LOSS_WEIGHT')
            self.ce_loss_weight = dist_cfg.getfloat('STUDENT', 'STUDENT_LOSS_WEIGHT')
            self.T = dist_cfg.getfloat('DISTILLATION', 'T')
            weight = torch.load(self.teacher_path)
            self.teacher = deeper(self.cfg, self.nn_input_size) 
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
        self.eval_model()

        self.metrics_manager.displayConfMatrixPlot(EVALU, dataset_name=self.dataset_name, model_name=f'{self.model_name}_kfold{self.kfold_idx}')

        
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
            self.model = self.model_f(self.cfg, self.nn_input_size).to(device=self.device)
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
        dataset = CommonDataset(X, Y)
        sampler = ImbalancedDatasetSampler(dataset, Y if self.args.balance_dataset else None)
        dataloader = DataLoader(dataset, batch_size=self.args.batch_size, sampler=sampler if not self.args.balance_dataset else None)
            
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
        dataset = CommonDataset(X, Y)
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
        self.metrics_manager.addConfMatrix(EVALU, truth, preds, f'Fold n. {self.kfold_idx}')
