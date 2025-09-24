import os
import ast
import pandas as pd
import json

from .utils import get_cfg, data_preprocess, data_binarization, metrics_binary_dataset, get_file_from_keyword, suppress_warnings
from .datasets import CommonDataset
from torch.utils.data import DataLoader

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
import torch.nn.functional as F 
import numpy as np

from .losses import SqrHingeLoss

from .models import smaller, deeper
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix

from .shap_explainer import ShapExplainer

import json

DATASET_PATH = '/home/sgeraci/Desktop/datasets'

TRAIN = 'train'
VALID = 'valid'
EVALU = 'evalu'

class Trainer():
    def __init__(self, model_name='full', dataset_name='CICIDS2017', arch='dense'):
        # Suppress PyTorch warnings at the beginning of training
        suppress_warnings()
        
        # Parameters passed directly
        self.dataset_name = dataset_name
        self.model_name = model_name
        self.arch = arch
        
        print(f'Init config:\n Model: {self.model_name}\n Dataset: {self.dataset_name}\n Arch: {self.arch}\n')
        
        # Load trainer configuration
        trainer_cfg = get_cfg('trainer')
        
        # Load parameters from config file
        self.batch_size = trainer_cfg.getint('TRAINING', 'BATCH_SIZE')
        subset_size_str = trainer_cfg.get('TRAINING', 'SUBSET_SIZE')
        self.subset_size = int(subset_size_str) if subset_size_str else None
        self.loss = trainer_cfg.get('TRAINING', 'LOSS')
        self.optim = trainer_cfg.get('TRAINING', 'OPTIM')
        self.scheduler = trainer_cfg.get('TRAINING', 'SCHEDULER')
        self.lr = trainer_cfg.getfloat('TRAINING', 'LR')
        self.momentum = trainer_cfg.getfloat('TRAINING', 'MOMENTUM')
        self.weight_decay = trainer_cfg.getfloat('TRAINING', 'WEIGHT_DECAY')
        self.epochs = trainer_cfg.getint('TRAINING', 'EPOCHS')
        self.balance_dataset = trainer_cfg.getboolean('TRAINING', 'BALANCE_DATASET')
        self.distilled = trainer_cfg.getboolean('TRAINING', 'DISTILLED')
        self.log_freq = trainer_cfg.getint('TRAINING', 'LOG_FREQ')
        self.random_seed = trainer_cfg.getint('TRAINING', 'RANDOM_SEED')
        self.weights_path = trainer_cfg.get('TRAINING', 'WEIGHTS_PATH')
        self.compute_shap = trainer_cfg.getboolean('TRAINING', 'COMPUTE_SHAP')
        

        # randomness
        gen = torch.manual_seed(self.random_seed)

        # init
        self.cfg = get_cfg(self.arch)
        self.dataset_cfg = get_cfg(self.dataset_name)
        self.num_classes = self.cfg.getint('MODEL', 'NUM_CLASSES')
        self.nn_input_size = self.cfg.getint('MODEL', 'INPUT_LAYER')
        self.hidden_nrs = ast.literal_eval(self.cfg.get('MODEL', 'OUT_FEATURES'))
        self.model_arch = f"{self.nn_input_size}-{'-'.join(str(i) for i in self.hidden_nrs)}-{self.num_classes}"

        self.dataset = self.dataset_cfg.get('DATASET', 'NAME')
        self.dataset_path = self.dataset_cfg.get('DATASET', 'PATH')
        self.dataset_test_path = self.dataset_cfg.get('DATASET', 'TEST_PATH', fallback='')
        self.dataset_dir = os.path.dirname(self.dataset_path)

        self.selected_feats = json.loads(self.dataset_cfg.get('DATASET', 'SELECTED_FEATURES'))
        self.last_selected_feats_file = f'{DATASET_PATH}/{self.dataset}/last_selected_features.json'

        # binarized dataset path
        # Try both with and without .csv extension for 168b dataset
        bin_ds_csv = f'{self.dataset_dir}/bin_{self.dataset}_168b.csv'
        bin_ds_no_ext = f'{self.dataset_dir}/bin_{self.dataset}_168b'
        
        if os.path.exists(bin_ds_csv):
            bin_ds = bin_ds_csv
        elif os.path.exists(bin_ds_no_ext):
            bin_ds = bin_ds_no_ext
        else:
            bin_ds = bin_ds_csv  # Default fallback

        if os.path.isfile(self.last_selected_feats_file):
            with open(self.last_selected_feats_file, 'r') as f:
                self.last_selected_feats = json.load(f)
            
            if self.last_selected_feats != self.selected_feats:
                print('Last selected features are different from the current ones!')
                print(f'DEBUG - Feature comparison:')
                print(f'  Last features count: {len(self.last_selected_feats)}')
                print(f'  Current features count: {len(self.selected_feats)}')
                
                # Find differences
                last_set = set(self.last_selected_feats)
                current_set = set(self.selected_feats)
                
                features_removed = last_set - current_set
                features_added = current_set - last_set
                
                if features_removed:
                    print(f'  Features removed: {list(features_removed)}')
                if features_added:
                    print(f'  Features added: {list(features_added)}')
                
                # Check if it's just an ordering issue
                if last_set == current_set:
                    print(f'  NOTE: Same features but different order!')
                    print(f'  Last order: {self.last_selected_feats}')
                    print(f'  Current order: {self.selected_feats}')
                
                print('Removing last binarized dataset if exists...', end='')
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
            
            # Get binarizable features only
            binarization_cfg = get_cfg('binarization')
            binarizable_features = list(binarization_cfg.options('FEATURE_BIT_WIDTHS'))
            
            # Filter to only binarizable features for binarization
            x_binarizable = x_tmp[[col for col in x_tmp.columns if col in binarizable_features]]
            Xbin = data_binarization(x_binarizable.astype('int'), selected_columns=list(x_binarizable.columns))

            print(f'Binarized dataset doesn\'t exists, saving it in {bin_ds} for future references... ', end='')
            pd.concat([pd.DataFrame(Xbin), Y], axis=1).to_csv(bin_ds, index=False)
            print('saved.')
        else:
            print('Binarized dataset exists, load it...', end='')
            try:
                data = pd.read_csv(bin_ds)
            except Exception as e:
                print(f"Error reading {bin_ds}: {e}")
                # If it fails, try reading without header
                try:
                    print("Trying to read without header...")
                    data = pd.read_csv(bin_ds, header=None)
                    # Add column names
                    n_features = data.shape[1] - 1  # Assuming last column is label
                    feature_names = [str(i) for i in range(n_features)]
                    data.columns = feature_names + ['label']
                except Exception as e2:
                    print(f"Failed to read dataset: {e2}")
                    raise e2
                    
            Xbin=data[data.columns[:-1]]
            Y=data[data.columns[-1]]
            print(f'loaded.\nNew {self.dataset} shape: {Xbin.shape}')

        Xbin_tr, Xbin_te, Y_tr, Y_te = train_test_split(Xbin, Y, test_size=0.3, random_state=self.random_seed, shuffle=True)
        self.Y_tr = Y_tr.values
        self.Y_te = Y_te.values

        # dataset prep termined - Xbin is already a numpy array
        self.X_tr = torch.tensor(Xbin_tr.values, dtype=torch.float32)
        self.X_te = torch.tensor(Xbin_te.values, dtype=torch.float32)

        self.test_dataloader = DataLoader(CommonDataset(self.X_te, self.Y_te), batch_size=self.batch_size, shuffle=True)
        
        self.device = torch.device('cpu')
        if 'bnn' in self.model_name or 'distilled' in self.model_name:
            self.model_f = smaller
        else:
            self.model_f = deeper
        
        if self.distilled:
            teacher_cfg_name = self.cfg.get('DISTILLATION', 'TEACHER')
            teacher_cfg = get_cfg(teacher_cfg_name)

            teach_nn_input_size = teacher_cfg.getint('MODEL', 'INPUT_LAYER')
            assert teach_nn_input_size==self.nn_input_size, "Teacher and student input layer must be the same"

            teach_hidden_nrs = ast.literal_eval(teacher_cfg.get('MODEL', 'OUT_FEATURES'))
            arch=f"{teach_nn_input_size}-{'-'.join(str(i) for i in teach_hidden_nrs)}-{self.num_classes}"
            self.teacher_path = get_file_from_keyword(
                f"pysrc/results/full_{arch}/weights_{self.dataset}",
                'final')

            print('\n******* TEACHER *******')
            print(f'Config: {teacher_cfg_name}')
            print(f'Architecure: {arch}')
            print(f'Teacher weights: {self.teacher_path}')
            print('\n***********************')

            self.soft_target_loss_weight = self.cfg.getfloat('DISTILLATION', 'TEACHER_LOSS_WEIGHT')
            self.ce_loss_weight = self.cfg.getfloat('DISTILLATION', 'STUDENT_LOSS_WEIGHT')
            self.T = self.cfg.getfloat('DISTILLATION', 'T')
            weight = torch.load(self.teacher_path)
            self.teacher = deeper(teacher_cfg, teach_nn_input_size) 
            self.teacher.load_state_dict(weight)
            

        if self.subset_size:
            N = len(self.Y_tr)
            S = min(self.subset_size, N)
            # generate a shuffled permutation of indices [0..N-1]
            perm = torch.randperm(N, generator=gen)
            # take the first S indices
            sel = perm[:S]
            # subset X and Y
            self.X_tr = self.X_tr[sel]
            self.Y_tr = self.Y_tr[sel]

        # results folder name
        self.results_dir = f"p4src/results/{self.model_name}_{self.model_arch}"
        
        print('Create results dir if it doen not exist...', end='')
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        if not os.path.exists(f'{self.results_dir}/plots_{self.dataset}'):
            os.makedirs(f'{self.results_dir}/plots_{self.dataset}')

        if not os.path.exists(f'{self.results_dir}/weights_{self.dataset}'):
            os.makedirs(f'{self.results_dir}/weights_{self.dataset}')
        print(' done')

        # Store evaluation results only
        self.eval_results = {}
        
        # Check for existing weights in configured path
        self.p4src_weights_dir = self.weights_path
        self.existing_weights_path = self._check_existing_weights()
        
    def _check_existing_weights(self):
        """Check if weights already exist for this model configuration"""
        if not os.path.exists(self.p4src_weights_dir):
            os.makedirs(self.p4src_weights_dir)
            return None
            
        # Expected weight file pattern: {model_name}_{arch}_{dataset}.pth
        weight_filename = f"{self.model_name}_{self.arch}_{self.dataset}.pth"
        weight_path = os.path.join(self.p4src_weights_dir, weight_filename)
        
        if os.path.exists(weight_path):
            print(f"Found existing weights: {weight_path}")
            return weight_path
        else:
            print(f"No existing weights found for: {weight_filename}")
            return None
        
    def build_model(self):
        # loss
        if self.loss == 'SqrHinge':
            self.criterion = SqrHingeLoss()
            self.model.features.append(nn.Tanh())
        elif self.loss == 'CrossEntropy':
            self.criterion = nn.CrossEntropyLoss()
        else:
            raise ValueError(f"{self.loss} not supported.")
        self.criterion = self.criterion.to(device=self.device)
    
        # optimizer
        if self.optim == 'ADAM':
            self.optimizer = optim.Adam(self.model.parameters(),  lr=self.lr, weight_decay=self.weight_decay)
        elif self.optim == 'SGD':
            self.optimizer = optim.SGD(self.model.parameters(), lr=self.lr, momentum=self.momentum, weight_decay=self.weight_decay)
        else:
            raise Exception(f"Unrecognized optimizer {self.scheduler}")

        # LR scheduler
        if self.scheduler == 'PLATEAU':
            self.scheduler = ReduceLROnPlateau(optimizer=self.optimizer, patience=self.patience, verbose=True, min_lr=1e-7, factor=0.1)
        elif self.scheduler == 'FIXED':
            self.scheduler = None
        else:
            raise Exception(f"Unrecognized scheduler {self.scheduler}")

    def train_model(self):
        torch.autograd.set_detect_anomaly(True)

        # Initialize model
        self.model = self.model_f(self.cfg, self.nn_input_size).to(device=self.device)
        self.build_model()
        
        # Check if we have existing weights
        if self.existing_weights_path:
            print(f"Loading existing weights from: {self.existing_weights_path}")
            try:
                weights = torch.load(self.existing_weights_path, map_location=self.device)
                self.model.load_state_dict(weights)
                print("Weights loaded successfully! Skipping training...")
                
                # Only evaluate the model
                self.eval_model()
                print(f'Evaluation results: {self.eval_results}')
                
                # Check for existing SHAP indices, generate only if needed
                if self.compute_shap:
                    existing_indices = ShapExplainer.check_existing_shap_indices(self.model_arch, self.dataset)
                    if existing_indices:
                        print(f"Found existing SHAP indices: {existing_indices}")
                        # Load and display existing indices
                        indices_data = ShapExplainer.load_shap_indices(existing_indices)
                        print(f"Top 5 features: {indices_data['feature_names'][:5]}")
                    else:
                        print("Computing SHAP feature indices...")
                        ShapExplainer.run_from_trainer(self, use_eval=False, method="kernel")
                return
                
            except Exception as e:
                print(f"Error loading weights: {e}")
                print("Proceeding with training...")
        
        print('\nNo existing weights found. Starting training...')
        print('\nSimple model training (no cross-validation):')
        
        # Simple train/validation split for monitoring
        X_train, X_val, Y_train, Y_val = train_test_split(
            self.X_tr, self.Y_tr, test_size=0.2, random_state=self.random_seed, shuffle=True
        )
        
        # Train the model
        final_w, final_acc = self.train(X_train, Y_train, X_val, Y_val)
        
        # Evaluate on test set
        self.eval_model()

        # Save final model using existing save logic
        self._save_model(final_w, final_acc)
        
        print(f'Evaluation results: {self.eval_results}')

        # Generate SHAP feature indices with intelligent caching
        if self.compute_shap:
            existing_indices = ShapExplainer.check_existing_shap_indices(self.model_arch, self.dataset)
            if existing_indices:
                print(f"SHAP indices already exist: {existing_indices}")
                # Load and display existing indices
                indices_data = ShapExplainer.load_shap_indices(existing_indices)
                print(f"Using existing top 126 features: {indices_data['feature_names'][:5]}...")
            else:
                print("Computing new SHAP feature indices...")
                result = ShapExplainer.run_from_trainer(self, use_eval=False, method="kernel")
                if 'indices_file' in result:
                    print(f"SHAP indices saved: {result['indices_file']}")
    
    def _save_model(self, weights, accuracy):
        """Save model to both original location and p4src weights directory"""
        # Original location
        final_out = f'{self.results_dir}/weights_{self.dataset}/final_{self.model_name}_acc{accuracy:.3f}.pth'
        torch.save(weights, final_out)
        print(f'Final model saved in {final_out}')
        
        # p4src weights location for future reuse
        p4src_weight_filename = f"{self.model_name}_{self.arch}_{self.dataset}.pth"
        p4src_weight_path = os.path.join(self.p4src_weights_dir, p4src_weight_filename)
        torch.save(weights, p4src_weight_path)
        print(f'Model also saved for reuse in {p4src_weight_path}')

    def train(self, X, Y, X_val=None, Y_val=None):
        dataset = CommonDataset(X, Y)
        dataloader = DataLoader(dataset, batch_size=self.batch_size)
            
        fold_acc = -np.inf

        for self.epoch in range(1, self.epochs+1):
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

                if self.distilled:
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

                if self.loss == 'SqrHinge':
                    cls = pred.argmax(1).round()
                elif self.loss == 'CrossEntropy':
                    cls = F.softmax(pred, dim=1).argmax(1)
                    
                acc = (cls == Y_tr).float().mean()

                if(batch % self.log_freq == 0):
                    loss_val, current = loss.item(), batch * dataloader.batch_size + len(X_tr)
                    print(f'  Batch [{current:>5d}/{len(dataloader.dataset):>5d}] Loss: {loss_val:.6f} Acc: {acc:.4f}')

                preds = np.hstack((preds, cls))
                truth = np.hstack((truth, Y_tr))

            # statistics
            acc = (preds == truth).mean()
            
            if(X_val is not None and Y_val is not None):
                with torch.no_grad():
                    valid_acc, valid_loss = self.val_model(X_val, Y_val)
                acc_cmp = valid_acc
                print(f'Epoch {self.epoch:>2d}/{self.epochs} | Train Acc: {acc:.4f} | Val Acc: {valid_acc:.4f} | Val Loss: {valid_loss:.6f}')

                # lr decay
                if self.scheduler != None:
                    self.scheduler.step(valid_loss)
            else:
                print(f'Epoch {self.epoch:>2d}/{self.epochs} | Train Acc: {acc:.4f}')
                # lr decay
                if self.scheduler != None:
                    self.scheduler.step(loss)
                acc_cmp = acc

            if(fold_acc < acc_cmp):
                fold_acc = acc_cmp
                fold_weights = self.model.state_dict()
            
        return fold_weights, fold_acc


    def val_model(self, X, Y):
        dataset = CommonDataset(X, Y)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)
  
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

            if self.loss == 'SqrHinge':
                cls = pred.argmax(1).round()
            elif self.loss == 'CrossEntropy':
                cls = F.softmax(pred, dim=1).argmax(1)
                
            preds = np.hstack((preds, cls))
            truth = np.hstack((truth, Y_val))
            losses = np.hstack((losses, loss.item()))
    
        # statistics
        avg_acc = (preds == truth).mean()
        avg_loss = losses.mean()

        return avg_acc, avg_loss
    

    def eval_model(self):
        preds = np.array([])
        truth = np.array([])

        self.model.eval()
        for _, (X_test, Y_test) in enumerate(self.test_dataloader):

            # compute output
            pred = self.model(X_test)

            if self.loss == 'SqrHinge':
                cls = pred.argmax(1).round()
            elif self.loss == 'CrossEntropy':
                cls = F.softmax(pred, dim=1).argmax(1)
            cls = cls.detach().numpy()

            preds = np.hstack((preds, cls))
            truth = np.hstack((truth, Y_test))

        # Save evaluation results
        eval_df = pd.DataFrame(np.column_stack([preds.astype('int'), truth.astype('int')]), columns=['preds', 'truth'])
        eval_csv_path = f'{self.results_dir}/final_eval_res__{self.model_name}_{self.model_arch}_{self.dataset}.csv'
        eval_df.to_csv(eval_csv_path)
        
        # Calculate and store evaluation metrics
        a, p, r, _, _, _, f1, _ = metrics_binary_dataset(truth, preds, pd.get_dummies(preds).values)
        
        self.eval_results = {
            'accuracy': a,
            'precision': p,
            'recall': r,
            'f1_score': f1,
            'predictions_file': eval_csv_path,
            'confusion_matrix': confusion_matrix(truth, preds).tolist()
        }
        
        print(f'\nEvaluation Results:')
        print(f'Accuracy: {a:.4f}')
        print(f'Precision: {p:.4f}')
        print(f'Recall: {r:.4f}')
        print(f'F1 Score: {f1:.4f}')
        print(f'Results saved to: {eval_csv_path}')
    
    def get_shap_feature_indices(self, k=126):
        """Get SHAP feature indices for this model and dataset."""
        indices_file = ShapExplainer.check_existing_shap_indices(self.model_arch, self.dataset, k)
        if indices_file:
            return ShapExplainer.load_shap_indices(indices_file)
        else:
            print(f"No SHAP indices found for {self.model_arch} on {self.dataset}")
            return None
