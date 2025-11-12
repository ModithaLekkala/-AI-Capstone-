import os
import ast
import json
import random
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
import torch.nn.functional as F 
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import confusion_matrix
import copy

from .utils import suppress_warnings, get_cfg
from .losses import SqrHingeLoss
from .models import smaller, deeper
from .shap_explainer import ShapExplainer
from .metrics import MetricsManager

suppress_warnings()

class SimpleTrainer:
    """
    Simplified trainer that operates directly on X, Y data without dataset initialization complexity.
    """
    
    def __init__(self, model_name, model_arch, device='cpu'):
        """
        Initialize SimpleTrainer with model configuration.
        
        Args:
            model_name (str): Model type ('tf_bnn', 'mlp', etc.)
            arch (str): Architecture name ('tiny', 'dense', 'wide')
            device (str): Device to use ('cpu', 'cuda')
        """
        self.model_name = model_name
        self.arch = model_arch
        self.device = device
        
        # Load configuration
        self.cfg = get_cfg(model_arch)
        trainer_cfg = get_cfg('trainer')
        
        # Model configuration
        self.model = None
        self.model_f = None
        self.nn_input_size = None
        self.optimizer = None
        self.criterion = None
        self.scheduler = None
        
        # Training configuration from trainer config
        self.batch_size = trainer_cfg.getint('TRAINING', 'BATCH_SIZE')
        self.learning_rate = trainer_cfg.getfloat('TRAINING', 'LR')
        self.scheduler_type = trainer_cfg.get('TRAINING', 'SCHEDULER')
        self.loss = trainer_cfg.get('TRAINING', 'LOSS')
        self.random_seed = trainer_cfg.getint('GENERAL', 'RANDOM_SEED', fallback=42)
        torch.manual_seed(self.random_seed)
        np.random.seed(self.random_seed)
        random.seed(self.random_seed)

        # Set epochs based on model type
        if model_name == 'mlp':
            self.epochs = trainer_cfg.getint('TRAINING', 'MLP_MODEL_EPOCHS')
            self.final_epochs = self.epochs
        else:  # BNN models
            self.epochs = trainer_cfg.getint('TRAINING', 'BNN_CROSS_VAL_EPOCHS')
            self.final_epochs = trainer_cfg.getint('TRAINING', 'BNN_FINAL_EPOCHS')
        
        # SHAP configuration from trainer config
        self.shap_background_size = trainer_cfg.getint('SHAP', 'BACKGROUND_SIZE', fallback=64)
        self.shap_explain_size = trainer_cfg.getint('SHAP', 'EXPLAIN_SIZE', fallback=32)
        
        # Results configuration
        self.results_dir = f'results/{self.model_name}_{model_arch}'
        # os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize MetricsManager for plotting
        hidden_nrs = ast.literal_eval(self.cfg.get('MODEL', 'OUT_FEATURES'))[0]  # First hidden layer size
        self.metrics_manager = MetricsManager(
            init_lr=self.learning_rate,
            init_epochs=self.epochs,
            scheduler=self.scheduler_type,
            hidden_layers=hidden_nrs,
            distilled=False,  # Not used for simple trainer
            init_wd=0.0,  # Default value
            res_dir=self.results_dir,
            dataset='simple',  # Placeholder since we don't have dataset
            model_arch=self.arch,
            model_name=self.model_name
        )

        self.nn_input_size = self.cfg.getint('MODEL', 'INPUT_LAYER')
        
        # Initialize model functions
        self._setup_model_functions()
    
    def _setup_model_functions(self):
        """Setup model creation functions based on model_name."""
        if 'bnn' in self.model_name:
            self.model_f = smaller
        elif 'mlp' in self.model_name:
            self.model_f = deeper
        else:
            raise ValueError(f"Unknown model_name: {self.model_name}")
    
    def _get_model_identifier(self):
        """Generate model identifier string."""
        hidden_size = ast.literal_eval(self.cfg.get('MODEL', 'OUT_FEATURES'))
        output_size = self.cfg.getint('MODEL', 'NUM_CLASSES')
        return f"{self.nn_input_size}-{'-'.join(str(i) for i in hidden_size)}-{output_size}]"
    
    def reset_model(self, nn_input_size=None):
        """
        Initialize/reset the model with given input size.
        
        Args:
            input_size (int): Number of input features
        """
        if nn_input_size is not None:
            self.nn_input_size = nn_input_size
            
        self.model = self.model_f(self.cfg, self.nn_input_size).to(device=self.device)
    
        self._build_optimizer_and_criterion()
        print(f"Model reset: {self._get_model_identifier()}")
    
    def _build_optimizer_and_criterion(self):
        """Build optimizer, criterion and scheduler."""
        # Optimizer
        if hasattr(self.cfg, 'get') and self.cfg.get('TRAIN', 'OPTIMIZER', fallback='Adam') == 'SGD':
            self.optimizer = optim.SGD(self.model.parameters(), lr=self.learning_rate, momentum=0.9)
        else:
            self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Loss function
        if self.loss == 'SqrHinge':
            self.criterion = SqrHingeLoss()
            self.model.features.append(nn.Tanh())
        elif self.loss == 'CrossEntropy':
            self.criterion = nn.CrossEntropyLoss()
        else:
            self.criterion = nn.CrossEntropyLoss()
        
        # Scheduler
        if self.scheduler_type == 'ReduceLROnPlateau':
            self.scheduler = ReduceLROnPlateau(self.optimizer, mode='min', factor=0.5, patience=10)
        else:
            self.scheduler = None
    
    def train(self, X, Y, with_validation=False, validation_split=0.2, verbose=True):
        """
        Train the model on provided data.
        
        Args:
            X (array-like): Input features
            Y (array-like): Target labels
            with_validation (bool): Whether to use validation split
            validation_split (float): Fraction of data to use for validation
            verbose (bool): Whether to print training progress
            
        Returns:
            dict: Training results with final accuracy and loss
        """
        if self.model is None:
            raise ValueError("Model not initialized. Call reset_model() first.")
        
        # Convert to tensors
        X_tensor = torch.tensor(X, dtype=torch.float32, device=self.device)
        Y_tensor = torch.tensor(Y, dtype=torch.long, device=self.device)
        
        if with_validation:
            # Split data for validation
            n_samples = len(X_tensor)
            n_val = int(n_samples * validation_split)
            indices = torch.randperm(n_samples)
            
            train_indices = indices[n_val:]
            val_indices = indices[:n_val]
            
            X_train = X_tensor[train_indices]
            Y_train = Y_tensor[train_indices]
            X_val = X_tensor[val_indices]
            Y_val = Y_tensor[val_indices]
            
            train_dataset = TensorDataset(X_train, Y_train)
            val_dataset = TensorDataset(X_val, Y_val)
        else:
            train_dataset = TensorDataset(X_tensor, Y_tensor)
            val_dataset = None
        
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False) if val_dataset else None
        
        self.model.train()
        best_val_acc = 0
        best_model_state = None
        train_accs = []
        
        for epoch in range(self.epochs):
            # Training phase
            train_loss = 0
            train_correct = 0
            train_total = 0
            
            for batch_X, batch_Y in train_loader:
                self.optimizer.zero_grad()
                
                outputs = self.model(batch_X)
                
                # Prepare targets based on loss function
                if self.loss == 'SqrHinge':
                    target = batch_Y.unsqueeze(1)
                    target_onehot = torch.zeros(target.size(0), 2, device=self.device)
                    target_onehot.fill_(-1)
                    target_onehot.scatter_(1, target, 1)
                    targets = target_onehot
                else:
                    targets = batch_Y
                
                loss = self.criterion(outputs, targets)
                loss.backward()
                self.optimizer.step()
                
                # Clip weights if BNN
                if hasattr(self.model, 'clip_weights'):
                    self.model.clip_weights(-1, 1)
                
                train_loss += loss.item()
                
                # Calculate accuracy
                if self.loss == 'SqrHinge':
                    pred = outputs.argmax(1).round()
                else:
                    pred = outputs.argmax(1)
                train_correct += (pred == batch_Y).sum().item()
                train_total += batch_Y.size(0)
            
            train_acc = train_correct / train_total
            train_loss_avg = train_loss / len(train_loader)
            train_accs.append(train_acc)
            
            # Validation phase
            val_acc = 0
            val_loss_avg = 0
            if val_loader:
                self.model.eval()
                val_loss = 0
                val_correct = 0
                val_total = 0
                
                with torch.no_grad():
                    for batch_X, batch_Y in val_loader:
                        outputs = self.model(batch_X)
                        
                        if self.loss == 'SqrHinge':
                            target = batch_Y.unsqueeze(1)
                            target_onehot = torch.zeros(target.size(0), 2, device=self.device)
                            target_onehot.fill_(-1)
                            target_onehot.scatter_(1, target, 1)
                            targets = target_onehot
                        else:
                            targets = batch_Y
                        
                        loss = self.criterion(outputs, targets)
                        val_loss += loss.item()
                        
                        if self.loss == 'SqrHinge':
                            pred = outputs.argmax(1).round()
                        else:
                            pred = outputs.argmax(1)
                        val_correct += (pred == batch_Y).sum().item()
                        val_total += batch_Y.size(0)
                
                val_acc = val_correct / val_total
                val_loss_avg = val_loss / len(val_loader)
                
                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    best_model_state = copy.deepcopy(self.model.state_dict())
                
                self.model.train()
            
            # Update scheduler
            if self.scheduler:
                if val_loader:
                    self.scheduler.step(val_loss_avg)
                else:
                    self.scheduler.step(train_loss_avg)
            
            # Print progress
            if verbose:
                if val_loader:
                    print(f"Epoch {epoch+1:2d}/{self.epochs} | Train Acc: {train_acc:.4f} | Val Acc: {val_acc:.4f} | Val Loss: {val_loss_avg:.6f}")
                else:
                    print(f"Epoch {epoch+1:2d}/{self.epochs} | Train Acc: {train_acc:.4f} | Train Loss: {train_loss_avg:.6f}")
        
        # Load best model if validation was used
        if best_model_state is not None:
            self.model.load_state_dict(best_model_state)
        
        self.model.eval()
        
        final_acc = best_val_acc if val_loader else train_acc
        final_loss = val_loss_avg if val_loader else train_loss_avg
        
        return {
            'final_accuracy': final_acc,
            'final_loss': final_loss,
            'best_val_accuracy': best_val_acc if val_loader else None,
            'train_accuracies': train_accs
        }
    
    def cross_validate_and_full_training(self, X, Y, n_folds=5, verbose=True):
        """
        Perform cross-validation followed by training on full dataset.
        
        Args:
            X (array-like): Input features
            Y (array-like): Target labels
            n_folds (int): Number of cross-validation folds
            verbose (bool): Whether to print progress
            
        Returns:
            dict: Results with CV accuracy and final model accuracy
        """
        X = np.array(X)
        Y = np.array(Y)
        
        # Initialize model with correct input size if not already done
        if self.model is None:
            self.reset_model(X.shape[1])
        
        # Cross-validation
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=self.random_seed)
        fold_accuracies = []
        best_fold_acc = 0
        best_fold_weights = None
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, Y)):
            if verbose:
                print(f"\n********** CROSS VALIDATION FOLD {fold+1} **********")
            
            X_fold_train, X_fold_val = X[train_idx], X[val_idx]
            Y_fold_train, Y_fold_val = Y[train_idx], Y[val_idx]
            
            # Reset model for this fold
            self.reset_model(X.shape[1])
            
            # Train on fold
            self.train(X_fold_train, Y_fold_train, with_validation=False, verbose=verbose)
            
            # Evaluate on validation
            val_results = self.eval_model(X_fold_val, Y_fold_val, verbose=False)
            fold_acc = val_results['accuracy']
            fold_accuracies.append(fold_acc)
            
            if fold_acc > best_fold_acc:
                best_fold_acc = fold_acc
                best_fold_weights = copy.deepcopy(self.model.state_dict())
            
            if verbose:
                print(f"Fold {fold+1} Validation Accuracy: {fold_acc:.4f}")
        
        cv_mean = np.mean(fold_accuracies)
        cv_std = np.std(fold_accuracies)
        
        if verbose:
            print(f"\nCross-validation results: {cv_mean:.4f} ± {cv_std:.4f}")
        
        # Train final model on full dataset with extended epochs
        if verbose:
            print("\nFinal model training on full dataset:")
        
        self.reset_model(X.shape[1])
        original_epochs = self.epochs
        self.epochs = self.final_epochs
        
        final_results = self.train(X, Y, with_validation=False, verbose=verbose)
        
        self.epochs = original_epochs
        
        return {
            'cv_accuracy_mean': cv_mean,
            'cv_accuracy_std': cv_std,
            'cv_accuracies': fold_accuracies,
            'best_fold_accuracy': best_fold_acc,
            'final_accuracy': final_results['final_accuracy'],
            'final_loss': final_results['final_loss']
        }
    
    def eval_model(self, X, Y, verbose=True):
        """
        Evaluate the model on provided data.
        
        Args:
            X (array-like): Input features
            Y (array-like): Target labels
            verbose (bool): Whether to print results
            
        Returns:
            dict: Evaluation results with accuracy, loss, and confusion matrix
        """
        if self.model is None:
            raise ValueError("Model not initialized. Call reset_model() first.")
        
        X_tensor = torch.tensor(X, dtype=torch.float32, device=self.device)
        Y_tensor = torch.tensor(Y, dtype=torch.long, device=self.device)
        
        dataset = TensorDataset(X_tensor, Y_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)
        
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for batch_X, batch_Y in dataloader:
                outputs = self.model(batch_X)
                
                # Prepare targets based on loss function
                if self.loss == 'SqrHinge':
                    target = batch_Y.unsqueeze(1)
                    target_onehot = torch.zeros(target.size(0), 2, device=self.device)
                    target_onehot.fill_(-1)
                    target_onehot.scatter_(1, target, 1)
                    targets = target_onehot
                else:
                    targets = batch_Y
                
                loss = self.criterion(outputs, targets)
                total_loss += loss.item()
                
                # Calculate predictions
                if self.loss == 'SqrHinge':
                    pred = outputs.argmax(1).round()
                else:
                    pred = outputs.argmax(1)
                
                correct += (pred == batch_Y).sum().item()
                total += batch_Y.size(0)
                
                all_preds.extend(pred.cpu().numpy())
                all_targets.extend(batch_Y.cpu().numpy())
        
        accuracy = correct / total
        avg_loss = total_loss / len(dataloader)
        cm = confusion_matrix(all_targets, all_preds)
        
        if verbose:
            print(f"Evaluation Results:")
            print(f"  Accuracy: {accuracy:.4f}")
            print(f"  Loss: {avg_loss:.6f}")
            print(f"  Confusion Matrix:\n{cm}")
        
        return {
            'accuracy': accuracy,
            'loss': avg_loss,
            'confusion_matrix': cm,
            'predictions': all_preds,
            'targets': all_targets
        }
    
    def save_model(self, filepath=None, accuracy=None):
        """
        Save the current model weights.
        
        Args:
            filepath (str): Custom filepath for saving (optional)
            accuracy (float): Model accuracy for filename (optional)
            
        Returns:
            str: Path where model was saved
        """
        if self.model is None:
            raise ValueError("No model to save. Call reset_model() first.")
        
        if filepath is None:
            weights_dir = os.path.join(self.results_dir, 'weights')
            os.makedirs(weights_dir, exist_ok=True)
            
            if accuracy is not None:
                filename = f"model_acc{accuracy:.3f}.pth"
            else:
                filename = f"model_{self._get_model_identifier()}.pth"
            
            filepath = os.path.join(weights_dir, filename)
        
        torch.save(self.model.state_dict(), filepath)
        print(f"Model saved: {filepath}")
        return filepath
    
    def load_model(self, filepath):
        """
        Load model weights from file.
        
        Args:
            filepath (str): Path to the weights file
        """
        if self.model is None:
            raise ValueError("Model not initialized. Call reset_model() first.")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Weight file not found: {filepath}")
        
        weights = torch.load(filepath, map_location=self.device)
        self.model.load_state_dict(weights)
        self.model.eval()
        print(f"Model weights loaded from: {filepath}")
    
    def copy_model(self):
        """
        Create a copy of the current trainer with the same model state.
        
        Returns:
            SimpleTrainer: Copy of this trainer
        """
        if self.model is None:
            raise ValueError("No model to copy. Call reset_model() first.")
        
        # Create new trainer instance
        new_trainer = SimpleTrainer(self.model_name, self.arch, self.device)
        new_trainer.reset_model(self.nn_input_size)
        
        # Copy model weights
        new_trainer.model.load_state_dict(copy.deepcopy(self.model.state_dict()))
        new_trainer.model.eval()
        
        return new_trainer
    
    def shap_model(self, background_data, explain_data=None, explain_size=None, force_recompute=False, method="kernel"):
        """
        Compute SHAP values for the model.
        
        Args:
            background_data (array-like): Background dataset for SHAP
            explain_data (array-like): Data to explain (optional, uses background if None)
            explain_size (int): Number of samples to explain (optional)
            force_recompute (bool): Whether to force recomputation
            method (str): SHAP method ('kernel', 'deep', etc.)
            
        Returns:
            dict: SHAP results with feature indices and importance
        """
        if self.model is None:
            raise ValueError("Model not initialized. Call reset_model() first.")
        
        # Prepare temporary trainer-like object for ShapExplainer
        temp_trainer = type('TempTrainer', (), {})()
        temp_trainer.model = self.model
        temp_trainer.model_name = self.model_name
        temp_trainer.arch = self.arch
        temp_trainer.dataset = 'temp'  # Placeholder
        temp_trainer.results_dir = self.results_dir
        temp_trainer.shap_background_size = len(background_data) if len(background_data) < self.shap_background_size else self.shap_background_size
        temp_trainer.shap_explain_size = explain_size or self.shap_explain_size
        temp_trainer.X_tr = torch.tensor(background_data, dtype=torch.float32)
        temp_trainer.X_te = torch.tensor(explain_data if explain_data is not None else background_data, dtype=torch.float32)
        
        # Compute SHAP
        shap_result, indices_file = ShapExplainer.run_from_trainer(
            temp_trainer,
            use_eval=(explain_data is not None),
            method=method,
            force_recompute=force_recompute,
            background_size=temp_trainer.shap_background_size,
            explain_size=temp_trainer.shap_explain_size
        )
        
        # Load indices
        indices_data = ShapExplainer.load_shap_indices(indices_file)
        
        return {
            'feature_indices': indices_data['feature_indices'],
            'shap_result': shap_result,
            'indices_file': indices_file
        }
    
    # Plotting methods (same as Trainer)
    def plot_training_curves(self):
        """Plot training and validation accuracy and loss curves."""
        if hasattr(self.metrics_manager, 'displayTrainEvalAcc'):
            self.metrics_manager.displayTrainEvalAcc()
        if hasattr(self.metrics_manager, 'displayLosses'):
            self.metrics_manager.displayLosses()
    
    def plot_confusion_matrix(self, case_name, predictions, targets):
        """Plot confusion matrix for the given case."""
        if hasattr(self.metrics_manager, 'displayConfMatrixPlot'):
            # Create temporary case for confusion matrix
            if case_name not in self.metrics_manager.cases:
                self.metrics_manager.initCase(case_name)
            
            # Add predictions and targets to the case
            self.metrics_manager.cases[case_name]['predictions'] = predictions
            self.metrics_manager.cases[case_name]['targets'] = targets
            
            self.metrics_manager.displayConfMatrixPlot(case_name, 
                                                     dataset_name='simple', 
                                                     model_name=self.model_name)
    
    def plot_confidence_histogram(self, confidence_data):
        """Plot confidence histogram for predictions."""
        if hasattr(self.metrics_manager, 'plot_confidence_histogram'):
            self.metrics_manager.plot_confidence_histogram(
                confidence_data, 
                self.model_name, 
                self.arch, 
                'simple',  # dataset placeholder
                self.results_dir
            )
    
    def get_metrics_manager(self):
        """Get the metrics manager for custom plotting."""
        return self.metrics_manager
    
    def get_model_info(self):
        """Get information about the current model."""
        if self.model is None:
            return None
        
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        return {
            'model_name': self.model_name,
            'architecture': self.arch,
            'input_size': self.nn_input_size,
            'model_identifier': self._get_model_identifier(),
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'device': str(self.device),
            'model_id': id(self.model)  # Useful for debugging model replacement
        }
    
    def predict(self, X):
        """
        Make predictions on input data.
        
        Args:
            X (array-like): Input features
            
        Returns:
            dict: Predictions with probabilities and class predictions
        """
        if self.model is None:
            raise ValueError("Model not initialized. Call reset_model() first.")
        
        X_tensor = torch.tensor(X, dtype=torch.float32, device=self.device)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X_tensor)
            
            if self.loss == 'SqrHinge':
                # For SqrHinge, outputs are raw logits
                probabilities = torch.softmax(outputs, dim=1)
                predictions = outputs.argmax(1)
            else:
                # For CrossEntropy, outputs are already logits
                probabilities = torch.softmax(outputs, dim=1)
                predictions = outputs.argmax(1)
        
        return {
            'predictions': predictions.cpu().numpy(),
            'probabilities': probabilities.cpu().numpy(),
            'raw_outputs': outputs.cpu().numpy()
        }