import os
import ast
import pandas as pd
import json
from datetime import datetime

from .utils import data_preprocess, data_binarization, metrics_binary_dataset
from ..helpers.utils import get_file_from_keyword, suppress_warnings, get_cfg
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
from sklearn.model_selection import train_test_split, StratifiedShuffleSplit
from sklearn.metrics import confusion_matrix

from .shap_explainer import ShapExplainer
from .metrics import MetricsManager

import json

DATASET_PATH = '/home/sgeraci/Desktop/datasets'

TRAIN = 'train'
VALID = 'valid'
EVALU = 'evalu'

class Trainer():
    _cached_datasets = {}
    _cached_dataloaders = {}
    
    def _get_dataset_key(self):
        key_components = [
            self.dataset,
            str(self.random_seed)
        ]
        return '|'.join(str(comp) for comp in key_components)
    
    @classmethod
    def get_cache_info(cls):
        return {
            'cached_datasets': len(cls._cached_datasets),
            'cached_dataloaders': len(cls._cached_dataloaders),
            'cache_keys': list(cls._cached_datasets.keys())
        }
    
    def __init__(self, model_name, dataset_name, arch, shap_indeces_path=None, eval_only=False):
        suppress_warnings()
        self.eval_only = eval_only

        self.dataset_name = dataset_name
        self.model_name = model_name
        self.arch = arch
        self.shap_indeces_path = shap_indeces_path

        print('\n')
        print(f'{"*" * 10} TRAINER INIT {"*" * 10}')
        print(f'Init config:\n Model: {self.model_name}\n Dataset: {self.dataset_name}\n Arch: {self.arch}\n SHAP indices path: {self.shap_indeces_path}\n')
        
        # Load trainer configuration
        trainer_cfg = get_cfg('trainer')
        
        # Load parameters from config file
        self.batch_size = trainer_cfg.getint('TRAINING', 'BATCH_SIZE')
        subset_size_str = trainer_cfg.get('TRAINING', 'SUBSET_SIZE')
        self.subset_size = int(subset_size_str) if subset_size_str else None
        self.loss = trainer_cfg.get('TRAINING', 'LOSS')
        self.optim = trainer_cfg.get('TRAINING', 'OPTIM')
        self.scheduler_type = trainer_cfg.get('TRAINING', 'SCHEDULER')
        self.lr = trainer_cfg.getfloat('TRAINING', 'LR')
        self.momentum = trainer_cfg.getfloat('TRAINING', 'MOMENTUM')
        self.weight_decay = trainer_cfg.getfloat('TRAINING', 'WEIGHT_DECAY')
        
        # Set epochs based on model type from config
        if self.model_name == 'mlp':
            # MLP models use fewer epochs
            mlp_epochs = trainer_cfg.getint('TRAINING', 'MLP_MODEL_EPOCHS')
            self.epochs = mlp_epochs
            self.final_epochs = mlp_epochs
        else:
            # BNN models: different epochs for cross-validation vs final training
            self.epochs = trainer_cfg.getint('TRAINING', 'BNN_CROSS_VAL_EPOCHS')
            self.final_epochs = trainer_cfg.getint('TRAINING', 'BNN_FINAL_EPOCHS')
        
        self.distilled = trainer_cfg.getboolean('TRAINING', 'DISTILLED')
        self.log_freq = trainer_cfg.getint('TRAINING', 'LOG_FREQ')
        self.random_seed = trainer_cfg.getint('TRAINING', 'RANDOM_SEED')
        self.shap_base_path = trainer_cfg.get('SHAP', 'SHAP_PATH')
        self.shap_background_size = trainer_cfg.getint('SHAP', 'BACKGROUND_SIZE')
        self.shap_explain_size = trainer_cfg.getint('SHAP', 'EXPLAIN_SIZE')
        self.nn_input_size = trainer_cfg.getint('TRAINING', 'EXTR_FEATS_WIDTH')
        self.folds = trainer_cfg.getint('TRAINING', 'FOLDS')


        # randomness
        gen = torch.manual_seed(self.random_seed)

        # init
        self.cfg = get_cfg(self.arch)
        self.dataset_cfg = get_cfg(self.dataset_name)
        self.num_classes = self.cfg.getint('MODEL', 'NUM_CLASSES')
        if 'tf' in self.model_name or 'tofino' in self.model_name:
            self.nn_input_size = self.cfg.getint('MODEL', 'INPUT_LAYER')
        self.hidden_nrs = ast.literal_eval(self.cfg.get('MODEL', 'OUT_FEATURES'))
        self.model_arch = f"{self.nn_input_size}-{'-'.join(str(i) for i in self.hidden_nrs)}-{self.num_classes}"

        self.dataset = self.dataset_cfg.get('DATASET', 'NAME')
        self.dataset_path = self.dataset_cfg.get('DATASET', 'PATH')
        self.dataset_test_path = self.dataset_cfg.get('DATASET', 'TEST_PATH', fallback='')
        self.dataset_dir = os.path.dirname(self.dataset_path)

        self.selected_feats = json.loads(self.dataset_cfg.get('DATASET', 'SELECTED_FEATURES'))
        self.last_selected_feats_file = f'{DATASET_PATH}/{self.dataset}/last_selected_features.json'

        # binarized dataset path - strict checking
        bin_ds = f'{self.dataset_dir}/bin_{self.dataset}_168b'
        if os.path.exists(bin_ds):
            bin_ds = bin_ds
        elif os.path.exists(f'{bin_ds}.csv'):
            bin_ds = f'{bin_ds}.csv'
        # else:
        #     raise FileNotFoundError(f'CRITICAL ERROR: Binarized dataset {bin_ds} not found. Expected file must exist.')

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
                print(f'Last and current selected features match. Continue with dataset {bin_ds} loading.')
        else:
            print(f'Saving current selected features to {self.last_selected_feats_file}...', end='')
            with open(self.last_selected_feats_file, 'w') as f:
                json.dump(self.selected_feats, f)
            print('saved.')
        
        dataset_key = self._get_dataset_key()
        if dataset_key in Trainer._cached_datasets:
            print(f'Using cached base dataset for key: {dataset_key}')
            cached_data = Trainer._cached_datasets[dataset_key]
            # Get the full 168b dataset from cache
            Xbin = cached_data['Xbin_full']
            Y = cached_data['Y_full']
            print(f'Cached base dataset shape: {Xbin.shape}')
        else:
            print(f'Loading and caching new base dataset with key: {dataset_key}')
        
            # preprocess dataset and dataloader - strict checking
            if not os.path.isfile(bin_ds):
                self.builder = CommonDataset
                
                # Strict checking for main dataset file
                if not os.path.exists(self.dataset_path):
                    raise FileNotFoundError(f'CRITICAL ERROR: Main dataset file {self.dataset_path} does not exist. Expected file must exist.')
                
                data = pd.read_csv(self.dataset_path, delimiter=',')
                
                # Strict checking for test dataset file if specified
                if self.dataset_test_path != '':
                    if not os.path.exists(self.dataset_test_path):
                        raise FileNotFoundError(f'CRITICAL ERROR: Test dataset file {self.dataset_test_path} does not exist. Expected file must exist.')
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

                print('\\nDATASETS PREPROCESSING')
                x_tmp,  _ = data_preprocess(data[data.columns[:-1]], dict)
                
                # Get binarizable features only
                binarization_cfg = get_cfg('binarization')
                binarizable_features = list(binarization_cfg.options('FEATURE_BIT_WIDTHS'))
                
                # Filter to only binarizable features for binarization
                x_binarizable = x_tmp[[col for col in x_tmp.columns if col in binarizable_features]]
                Xbin = data_binarization(x_binarizable.astype('int'), selected_columns=list(x_binarizable.columns))

                print(f"Binarized dataset doesn't exists, saving it in {bin_ds} for future references... ", end='')
                pd.concat([pd.DataFrame(Xbin), Y], axis=1).to_csv(bin_ds, index=False)
                print('saved.')
            else:
                print(f'{self.dataset} binarized dataset exists, load it...', end='')
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
                print(f'loaded. New shape: {Xbin.shape}')

            # Cache the full 168b dataset before SHAP filtering
            print(f'Caching base dataset with key: {dataset_key}...', end=' ')
            Trainer._cached_datasets[dataset_key] = {
                'Xbin_full': Xbin,
                'Y_full': Y
            }
            print(f'dataset cached. Cache now contains {len(Trainer._cached_datasets)} entries.')
        
        # Apply SHAP filtering if provided (happens for both cached and non-cached data)
        if self.shap_indeces_path is not None:
            if not os.path.exists(self.shap_indeces_path):
                raise FileNotFoundError(f'CRITICAL ERROR: SHAP indices file {self.shap_indeces_path} does not exist. Expected file must exist.')

            print(f'\nLoading SHAP indices from {self.shap_indeces_path}...', end='')
            
            try:
                with open(self.shap_indeces_path, 'r') as f:
                    shap_data = json.load(f)
                    best_indices = shap_data['feature_indices'][:self.nn_input_size]
            except (json.JSONDecodeError, KeyError) as e:
                raise ValueError(f'CRITICAL ERROR: Invalid SHAP indices file format in {self.shap_indeces_path}: {e}')
                
            print(f' found {len(best_indices)} indices.')
            print(f'SHAP best 5 features: {best_indices[:5]}...')
            
            # Filter the dataset to use only the best features
            if len(best_indices) > 0:
                print(f'Filtering dataset from {Xbin.shape[1]} to {len(best_indices)} features...')
                Xbin = Xbin.iloc[:, best_indices]
                print(f'Filtered {self.dataset} shape: {Xbin.shape}\n')
            else:
                raise Exception(f'Error: No valid SHAP indices found on {self.shap_indeces_path}.')


        # Split and convert to tensors (happens for both cached and non-cached data)
        Xbin_tr, Xbin_te, Y_tr, Y_te = train_test_split(Xbin, Y, test_size=0.3, random_state=self.random_seed, shuffle=True)
        self.Y_tr = Y_tr.values
        self.Y_te = Y_te.values

        # dataset prep terminated - Xbin is already a numpy array
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
            
            # Strict checking for teacher weights
            if not os.path.exists(self.teacher_path):
                raise FileNotFoundError(f'CRITICAL ERROR: Teacher weights file {self.teacher_path} does not exist. Expected file must exist.')
            
            try:
                weight = torch.load(self.teacher_path)
                self.teacher = deeper(teacher_cfg, teach_nn_input_size) 
                self.teacher.load_state_dict(weight)
            except Exception as e:
                raise RuntimeError(f'CRITICAL ERROR: Failed to load teacher weights from {self.teacher_path}: {e}')
            

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
        self.trainer_dir = f'{self.model_name}_{self.model_arch}'
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up from ml_helpers to p4src
        self.results_dir = os.path.join(script_dir, "results", self.trainer_dir)
        
        print('Create results dir if it doen not exist...', end='')
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        if not os.path.exists(f'{self.results_dir}/plots_{self.dataset}'):
            os.makedirs(f'{self.results_dir}/plots_{self.dataset}')

        if not os.path.exists(f'{self.results_dir}/weights_{self.dataset}'):
            os.makedirs(f'{self.results_dir}/weights_{self.dataset}')
        print(' done')

        # Cross-validation setup
        self.kfolder = StratifiedShuffleSplit(n_splits=self.folds, test_size=0.1, random_state=self.random_seed)
        self.kfold_idx = 1
        self.best_acc = -np.inf
        
        # Initialize MetricsManager
        self.metrics_manager = MetricsManager(self.lr, 
                                            self.epochs, 
                                            self.scheduler_type, 
                                            self.hidden_nrs, 
                                            self.distilled, 
                                            self.weight_decay, 
                                            self.results_dir, 
                                            self.dataset, 
                                            self.model_arch, 
                                            self.model_name)

        # Store evaluation results only
        self.eval_results = {}
        
        # Check for existing weights in results directory
        if self.eval_only:
            self.existing_weights_path = self._check_existing_weights()
        else:
            self.existing_weights_path = None

    def _check_existing_weights(self):
        """Check if the exact expected weight file exists in results directory - strict checking"""
        weights_dir = f'{self.results_dir}/weights_{self.dataset}'
        
        if not os.path.exists(weights_dir):
            raise FileNotFoundError(f"CRITICAL ERROR: Weights directory not found: {weights_dir}. Expected directory must exist for eval_only mode.")
            
        # Look for the exact expected weight file pattern: final_{model_name}_acc*.pth
        weight_pattern = f"final_{self.model_name}_acc"
        
        try:
            weight_files = [f for f in os.listdir(weights_dir) if f.startswith(weight_pattern) and f.endswith('.pth')]
            
            if not weight_files:
                raise FileNotFoundError(f"CRITICAL ERROR: No weight files found with pattern '{weight_pattern}*.pth' in {weights_dir}. Expected weight file must exist for eval_only mode.")
                
            if len(weight_files) > 1:
                print(f"Warning: Multiple weight files found: {weight_files}")
                
            # Sort by accuracy (extract from filename) and take the best one
            def extract_accuracy(filename):
                try:
                    if 'acc' in filename:
                        acc_part = filename.split('acc')[1].split('.pth')[0]
                        return float(acc_part)
                    else:
                        return 0.0
                except (IndexError, ValueError):
                    return 0.0
            
            weight_files.sort(key=extract_accuracy, reverse=True)
            best_weight_file = weight_files[0]
            weight_path = os.path.join(weights_dir, best_weight_file)
            
            # Strict verification that the file actually exists and is readable
            if not os.path.isfile(weight_path):
                raise FileNotFoundError(f"CRITICAL ERROR: Weight file {weight_path} does not exist or is not a file.")
                
            print(f"Found expected weight file: {weight_path}")
            return weight_path
                
        except FileNotFoundError:
            # Re-raise FileNotFoundError as-is
            raise
        except OSError as e:
            raise RuntimeError(f"CRITICAL ERROR: Cannot access weights directory {weights_dir}: {e}")
        except Exception as e:
            raise RuntimeError(f"CRITICAL ERROR: Error checking for weights: {e}")
        
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
            raise Exception(f"Unrecognized optimizer {self.optim}")

        # LR scheduler
        if self.scheduler_type == 'PLATEAU':
            self.scheduler = ReduceLROnPlateau(optimizer=self.optimizer, patience=self.patience, verbose=True, min_lr=1e-7, factor=0.1)
        elif self.scheduler_type == 'FIXED':
            self.scheduler = None
        else:
            raise Exception(f"Unrecognized scheduler {self.scheduler_type}")

    def load_model(self):
        """Initialize model and optionally load weights for eval_only mode"""
        # Initialize model
        self.model = self.model_f(self.cfg, self.nn_input_size).to(device=self.device)
        self.build_model()
        
        # Load weights if in eval_only mode and weights exist
        if self.eval_only and self.existing_weights_path and self.shap_indeces_path is None:
            print(f"\nLoading weights from expected location: {self.existing_weights_path}")
            try:
                # Verify file exists and is readable before loading
                if not os.path.isfile(self.existing_weights_path):
                    raise FileNotFoundError(f"Weight file {self.existing_weights_path} does not exist")
                    
                weights = torch.load(self.existing_weights_path, map_location=self.device)
                self.model.load_state_dict(weights)
                print("✅ Weights loaded successfully!\n")
                
            except FileNotFoundError as e:
                raise FileNotFoundError(f"CRITICAL ERROR: {e}")
            except Exception as e:
                raise RuntimeError(f"CRITICAL ERROR: Failed to load weights from {self.existing_weights_path}: {e}")

    def train_model(self, cross_validate=False, train_only=False):
        torch.autograd.set_detect_anomaly(True)

        # Initialize model and load weights if needed
        self.load_model()
        
        # Skip training if eval_only mode
        if self.eval_only:
            print("✅ Eval-only mode: Skipping training...\n")

        if not self.eval_only:
            if cross_validate:
                print('\nPerforming cross-validation training:')
                best_fold_w = self.cross_validate_model()
                
                print('\nFinal model training on full dataset:')
                # Create new model and train on full dataset with additional epochs
                self.model = self.model_f(self.cfg, self.nn_input_size).to(device=self.device)
                self.build_model()
                
                # Temporarily increase epochs for final training
                original_epochs = self.epochs
                self.epochs = self.final_epochs
                
                # Train on full dataset (no validation split)
                final_w, final_acc = self.train(self.X_tr, self.Y_tr)
                
                # Restore original epochs
                self.epochs = original_epochs
                
                # Save both best fold and final model
                best_fold_out = f'{self.results_dir}/weights_{self.dataset}/best_fold_{self.model_name}_acc{self.best_acc:.3f}.pth'
                torch.save(best_fold_w, best_fold_out)
                print(f'Best fold model saved in {best_fold_out}')
                
            else:
                print('\nSimple model training (no cross-validation):')
                X_train, X_val, Y_train, Y_val = train_test_split(
                    self.X_tr, self.Y_tr, test_size=0.2, random_state=self.random_seed, shuffle=True
                )

                # Train the model
                final_w, final_acc = self.train(X_train, Y_train, X_val, Y_val)
        
        # Generate training plots for base models (simple training)
        # if not self.eval_only:
        #     print("Generating training plots...")
        #     self.metrics_manager.displayTrainEvalAcc()
        #     self.metrics_manager.displayLosses()
        
        # Evaluate on test set
        if(not train_only):
            self.eval_model()
        # print(f'Evaluation results: {self.eval_results}')

        # Save final model using existing save logic
        if not self.eval_only:
            self._save_model(final_w, final_acc)

    def compute_shap_indices(self, force_recompute=False, use_eval=False):
        _, indices_file = ShapExplainer.run_from_trainer(
            self, 
            use_eval=use_eval, 
            method="kernel", 
            force_recompute=force_recompute,
            background_size=self.shap_background_size,
            explain_size=self.shap_explain_size
        )
        return indices_file

    def cross_validate_model(self):
        self.fold_confidences = []
        self.fold_confidence_data = []  # Store per-fold confidence accuracies
        
        for train_ids, val_ids in self.kfolder.split(self.X_tr, self.Y_tr):
            print(f'\n{10*"*"} CROSS VALIDATION FOLD {self.kfold_idx} {10*"*"}\n')
            self.load_model()  # Use load_model instead of manual initialization
            self.train_case = f'{TRAIN}{self.kfold_idx}'
            self.valid_case = f'{VALID}{self.kfold_idx}'
            self.evalu_case = f'{EVALU}{self.kfold_idx}'

            # train fold
            fold_w, fold_acc = self.train(self.X_tr[train_ids], self.Y_tr[train_ids], self.X_tr[val_ids], self.Y_tr[val_ids])
            
            # extract confidence scores for validation set
            with torch.no_grad():
                self.model.eval()
                val_data = torch.tensor(self.X_tr[val_ids], dtype=torch.float32, device=self.device)
                val_confidence = self.get_confidence(val_data)
                val_pred = self.model(val_data)
                if self.loss == 'SqrHinge':
                    val_cls = val_pred.argmax(1).round()
                elif self.loss == 'CrossEntropy':
                    val_cls = F.softmax(val_pred, dim=1).argmax(1)
                
                fold_conf_data = []
                for conf, pred, truth in zip(val_confidence.numpy(), val_cls.numpy(), self.Y_tr[val_ids]):
                    self.fold_confidences.append((conf, pred, truth))
                    fold_conf_data.append((conf, pred, truth))
                
                self.fold_confidence_data.append(fold_conf_data)

            # evaluate fold
            # self.eval_model()

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
        self.metrics_manager.displayTrainEvalAcc()
        self.metrics_manager.displayLosses()
        
        self.metrics_manager.plot_confidence_histogram(self.fold_confidence_data, self.model_name, self.model_arch, self.dataset, self.results_dir)

        return self.best_fold

    def get_confidence(self, x):
        x = x.view(x.shape[0], -1)
        x = 2.0 * x - torch.tensor([1.0], device=x.device)
        for mod in self.model.features[:-3]:
            x = mod(x)
        x = x.cpu()
        x[x == -1] = 0
        return x.sum(dim=1)
    
    def infer(self, features):
        if not hasattr(self, 'model') or self.model is None:
            raise RuntimeError("Model not initialized. Load a trained model first.")
            
        self.model.eval()
        
        # Convert to tensor if needed
        if isinstance(features, np.ndarray):
            features = torch.tensor(features, dtype=torch.float32, device=self.device)
        
        # Add batch dimension for single sample
        features = features.unsqueeze(0)
            
        with torch.no_grad():
            # Get model output
            logits = self.model(features)
            
            # Get class probabilities and predictions
            if self.loss == 'SqrHinge':
                prediction = logits.argmax(1).round()
                probabilities = torch.sigmoid(logits)
            elif self.loss == 'CrossEntropy':
                probabilities = F.softmax(logits, dim=1)
                prediction = probabilities.argmax(1)
            
            # Get confidence score for BNN models
            confidence = None
            if 'bnn' in self.model_name.lower():
                confidence = self.get_confidence(features)
                confidence = float(confidence[0].cpu().numpy())
            
            # Convert to numpy and extract single values
            prediction = int(prediction[0].cpu().numpy())
            probabilities = probabilities[0].cpu().numpy()
            
            result = {
                'prediction': prediction,
                'probabilities': probabilities,
            }
            if confidence is not None:
                result['confidence'] = confidence
                    
        return result

    def _save_model(self, weights, accuracy):
        """Save model to results directory weights folder"""
        # Save to results directory weights folder
        final_out = f'{self.results_dir}/weights_{self.dataset}/final_{self.model_name}_acc{accuracy:.3f}.pth'
        torch.save(weights, final_out)
        print(f'Final model saved in {final_out}')

    def train(self, X, Y, X_val=None, Y_val=None):
        # Initialize metrics cases if not already done
        if not hasattr(self, 'train_case'):
            self.train_case = TRAIN
            self.valid_case = VALID
            self.evalu_case = EVALU
        
        if self.train_case not in self.metrics_manager.cases:
            self.metrics_manager.initCase(self.train_case)
        if self.valid_case not in self.metrics_manager.cases:
            self.metrics_manager.initCase(self.valid_case)
        if self.evalu_case not in self.metrics_manager.cases:
            self.metrics_manager.initCase(self.evalu_case)
            
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
                self.metrics_manager.addLoss(self.train_case, (loss.item(), self.epoch))

                if(batch % self.log_freq == 0):
                    loss_val, current = loss.item(), batch * dataloader.batch_size + len(X_tr)
                    # print(f'  Batch [{current:>5d}/{len(dataloader.dataset):>5d}] Loss: {loss_val:.6f} Acc: {acc:.4f}')
                    if hasattr(self, 'kfold_idx'):
                        self.metrics_manager.batchLog(mode=TRAIN, epoch_no=self.epoch, curr_len=current, dataset_len=len(dataloader.dataset), loss=loss_val, acc=acc, kfold=self.kfold_idx, epochs=self.epochs)

                preds = np.hstack((preds, cls))
                truth = np.hstack((truth, Y_tr))

            # statistics
            acc = (preds == truth).mean()
            self.metrics_manager.addAcc(self.train_case, acc)
            
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
                
            self.metrics_manager.addLoss(self.valid_case, (loss.item(), self.epoch))
                
            preds = np.hstack((preds, cls))
            truth = np.hstack((truth, Y_val))
            losses = np.hstack((losses, loss.item()))
    
        # statistics
        avg_acc = (preds == truth).mean()
        avg_loss = losses.mean()
        self.metrics_manager.addAcc(self.valid_case, avg_acc)
        if hasattr(self, 'kfold_idx'):
            self.metrics_manager.batchLog(mode=VALID, epoch_no=self.epoch, curr_len=0, dataset_len=len(dataloader.dataset), loss=avg_loss, acc=avg_acc, kfold=self.kfold_idx, epochs=self.epochs)
        
        return avg_acc, avg_loss
    def eval_model(self):
        # Load model if not already loaded (for eval_only mode)
        if not hasattr(self, 'model') or self.model is None:
            if self.eval_only:
                print("Loading model for evaluation...")
                self.load_model()
            else:
                raise RuntimeError("Model not initialized. Call train_model() first.")
                
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
        eval_csv_metrics_path = f'{self.results_dir}/final_eval_metrics__{self.model_name}_{self.model_arch}_{self.dataset}.csv'

        if not os.path.exists(os.path.dirname(eval_csv_path)):
            os.makedirs(os.path.dirname(eval_csv_path))
        eval_df.to_csv(eval_csv_path)
        
        # Calculate and store evaluation metrics
        a, p, r, _, _, _, f1, _ = metrics_binary_dataset(truth, preds, pd.get_dummies(preds).values)
        
        # Add confusion matrix and metrics to MetricsManager
        if not hasattr(self, 'evalu_case'):
            self.evalu_case = EVALU
        if self.evalu_case not in self.metrics_manager.cases:
            self.metrics_manager.initCase(self.evalu_case)
            
        self.metrics_manager.addAcc(self.evalu_case, a)
        self.metrics_manager.addPrec(self.evalu_case, p)
        self.metrics_manager.addRec(self.evalu_case, r)
        self.metrics_manager.addF1(self.evalu_case, f1)
        self.metrics_manager.addConfMatrix(self.evalu_case, truth, preds, None)
        
        # Display confusion matrix plot only for final evaluation (not cross-validation)
        # Only show confusion matrix if this is not a cross-validation fold evaluation
        if self.evalu_case == EVALU:  # Final evaluation, not cross-validation fold
            self.metrics_manager.displayConfMatrixPlot(self.evalu_case)
        
        # Calculate additional metrics for CSV
        cm = confusion_matrix(truth, preds)
        tn, fp, fn, tp = cm.ravel()
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        
        # Create metrics DataFrame and save to CSV
        metrics_data = {
            'accuracy': [a],
            'precision': [p],
            'recall': [r],
            'f1_score': [f1],
            'specificity': [specificity],
            'dataset': [self.dataset],
            'model_name': [self.model_name],
            'model_arch': [self.model_arch],
            'num_samples': [len(truth)],
            'num_positive_actual': [int(np.sum(truth))],
            'num_negative_actual': [int(len(truth) - np.sum(truth))],
            'true_positives': [int(tp)],
            'true_negatives': [int(tn)],
            'false_positives': [int(fp)],
            'false_negatives': [int(fn)],
            'predictions_file': [eval_csv_path],
            'timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        }
        
        metrics_df = pd.DataFrame(metrics_data)
        metrics_df.to_csv(eval_csv_metrics_path, index=False)
        
        # Append to common results file for comparison
        self._append_to_common_results(metrics_data)
        
        self.eval_results = {
            'accuracy': a,
            'precision': p,
            'recall': r,
            'f1_score': f1,
            'predictions_file': eval_csv_path,
            'metrics_file': eval_csv_metrics_path,
            'confusion_matrix': cm.tolist()
        }
        
        print(f'\nEvaluation Results:')
        print(f'Accuracy: {a:.4f}')
        print(f'Precision: {p:.4f}')
        print(f'Recall: {r:.4f}')
        print(f'F1 Score: {f1:.4f}')
        print(f'Specificity: {specificity:.4f}')

        print(f'\nResults saved to: {eval_csv_path}')
        print(f'Metrics saved to: {eval_csv_metrics_path}')
    
    def _append_to_common_results(self, metrics_data):
        """Append or update evaluation results in a common comparison file."""
        # Get the results directory path (same logic as used for self.results_dir)
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up from ml_helpers to p4src
        results_base_dir = os.path.join(script_dir, "results")
        common_results_file = os.path.join(results_base_dir, "all_model_results.csv")
        
        # Create DataFrame from current metrics
        current_df = pd.DataFrame(metrics_data)
        
        # Check if common file exists
        if os.path.exists(common_results_file):
            try:
                # Read existing data
                existing_df = pd.read_csv(common_results_file)
                
                # Check for existing record with same model_name, model_arch, and dataset
                match_conditions = (
                    (existing_df['model_name'] == metrics_data['model_name'][0]) &
                    (existing_df['model_arch'] == metrics_data['model_arch'][0]) &
                    (existing_df['dataset'] == metrics_data['dataset'][0])
                )
                
                existing_record = existing_df[match_conditions]
                
                if len(existing_record) > 0:
                    # Replace existing record(s)
                    print(f"Found existing record for {metrics_data['model_name'][0]}_{metrics_data['model_arch'][0]}_{metrics_data['dataset'][0]}")
                    print("Replacing existing record with new results...")
                    
                    # Remove existing record(s) and add new one
                    existing_df = existing_df[~match_conditions]
                    combined_df = pd.concat([existing_df, current_df], ignore_index=True)
                else:
                    # No existing record, append new data
                    print(f"Adding new record for {metrics_data['model_name'][0]}_{metrics_data['model_arch'][0]}_{metrics_data['dataset'][0]}")
                    combined_df = pd.concat([existing_df, current_df], ignore_index=True)
                    
            except Exception as e:
                print(f"Warning: Could not read existing common results file: {e}")
                print("Creating new common results file...")
                combined_df = current_df
        else:
            # Create new file
            combined_df = current_df
            print(f"Creating new common results file: {common_results_file}")
        
        # Save combined results
        try:
            # Ensure results directory exists
            os.makedirs(results_base_dir, exist_ok=True)
            combined_df.to_csv(common_results_file, index=False)
            print(f"Results updated in common file: {common_results_file}")
        except Exception as e:
            print(f"Warning: Could not save to common results file: {e}")
        
        # Print summary of records in file
        try:
            final_df = pd.read_csv(common_results_file)
            print(f"Total records in all_model_results.csv: {len(final_df)}")
        except Exception as e:
            print(f"Warning: Could not read final results for summary: {e}")
        except Exception as e:
            print(f"Warning: Could not save to common results file: {e}")
    
    def get_shap_feature_indices(self):
        """Get SHAP feature indices for this model and dataset."""
        indices_file = ShapExplainer.check_existing_shap_indices(self.model_arch, self.dataset)
        if indices_file:
            return ShapExplainer.load_shap_indices(indices_file)
        else:
            print(f"No SHAP indices found for {self.model_arch} on {self.dataset}")
            return None
    
    def get_shap_path(self):
        """Get the SHAP indices file path for this model and dataset.
        
        Returns
        -------
        str or None
            Path to the SHAP indices file if it exists, None otherwise
        """
        indices_file = ShapExplainer.check_existing_shap_indices(self.model_arch, self.dataset)
        if indices_file:
            print(f"Found SHAP indices for {self.model_name} ({self.model_arch}) on {self.dataset}: {indices_file}")
            return indices_file
        else:
            print(f"No SHAP indices found for {self.model_name} ({self.model_arch}) on {self.dataset}")
            return None

    def get_expected_shap_path(self):
        """Get the expected SHAP indices file path for this model and dataset.
        
        This method returns the path where SHAP indices should be located,
        regardless of whether the file actually exists.
        
        Returns
        -------
        str
            Expected path to the SHAP indices file
        """
        # Use the same logic as in ShapExplainer to construct the expected path
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up from ml_helpers to p4src
        base_dir = os.path.join(script_dir, "shaps")
        shap_dir_name = f"shap_{self.model_name}_{self.model_arch.replace('_', '-')}_{self.dataset.lower()}"
        expected_path = os.path.join(base_dir, shap_dir_name, "feature_indices.json")
        
        print(f"Expected SHAP path for {self.model_name} ({self.model_arch}) on {self.dataset}: {expected_path}")
        return expected_path
