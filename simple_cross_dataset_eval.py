#!/usr/bin/env python3

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn.functional as F
from sklearn.model_selection import train_test_split
from ml_helpers.simple_trainer import SimpleTrainer
from ml_helpers.utils import get_cfg, softmax_temp
import random
import argparse

np.random.seed(42)
torch.manual_seed(42)
random.seed(42)

MAX_UNSW_FRACTION = 0.4
DATASET_SWITCH_START = 20
DATASET_SWITCH_END = 40
# CRITICAL_SAMPLES_WINDOW = 10000 # wide
# CRITICAL_SAMPLES_WINDOW = 30000 # tiny
CRITICAL_SAMPLES_WINDOW = 40000 # dense
BATCH_SIZE = 1000
N_BATCHES = 170
RES_DIR = ''


def load_dataset(dataset_name):
    """Load dataset directly"""
    dataset_cfg = get_cfg(dataset_name)
    dataset_path = dataset_cfg.get('DATASET', 'PATH')
    dataset_dir = os.path.dirname(dataset_path)
    bin_dataset_path = f'{dataset_dir}/bin_{dataset_cfg.get("DATASET", "NAME")}_168b.csv'
    
    if os.path.exists(bin_dataset_path):
        data = pd.read_csv(bin_dataset_path)
        X = data.iloc[:, :-1].values
        Y = data.iloc[:, -1].values
        return X, Y
    
    raise FileNotFoundError(f"Dataset {dataset_name} not found")

def get_confidence_safe(trainer, x):
    """Safe confidence calculation with tensor validation - adapted from trainer.py"""
    import torch
    if not isinstance(x, torch.Tensor):
        x = torch.tensor(x, dtype=torch.float32, device=trainer.device)
    if x.device != trainer.device:
        x = x.to(trainer.device)
    
    x = x.view(x.shape[0], -1)
    x = 2.0 * x - torch.tensor([1.0], device=x.device)
    
    # Apply model layers up to penultimate layer
    if hasattr(trainer.model, 'features'):
        # For BNN models with features attribute - apply all but last 3 layers
        for mod in trainer.model.features[:-3]:
            x = mod(x)
    else:
        # Alternative approach if model structure is different
        return torch.zeros(x.shape[0])  # Placeholder
    
    x = x.cpu()
    # For binary activations: convert {-1, +1} to {0, +1} then sum
    x[x == -1] = 0
    confidence_scores = x.sum(dim=1)
    return confidence_scores

def analyze_confidence_distribution(bnn_trainer: SimpleTrainer, X_val_shaped, Y_val):
    """Analyze confidence distribution matching trainer.py plot_confidence_histogram style"""
    
    print(f"Computing confidence scores for {len(X_val_shaped)} validation samples...")
    
    bnn_trainer.model.eval()
    confidence_data = []  # Store (confidence, prediction, truth) tuples
    
    with torch.no_grad():
        val_tensor = torch.tensor(X_val_shaped, dtype=torch.float32, device=bnn_trainer.device)
        
        # Get all predictions at once
        logits = bnn_trainer.model(val_tensor)
        if hasattr(bnn_trainer, 'loss') and bnn_trainer.loss == 'SqrHinge':
            predictions = logits.argmax(1).round()
        else:
            import torch.nn.functional as F
            probabilities = F.softmax(logits, dim=1)
            predictions = probabilities.argmax(1)
        
        # Get all confidence scores at once
        confidences = get_confidence_safe(bnn_trainer, val_tensor)
        
        # Store the data as tuples
        for conf, pred, truth in zip(confidences.numpy(), predictions.cpu().numpy(), Y_val):
            confidence_data.append((conf, pred, truth))
    
    # Extract data for analysis
    confidences = np.array([conf for conf, _, _ in confidence_data])
    predictions = np.array([pred for _, pred, _ in confidence_data])
    truths = np.array([truth for _, _, truth in confidence_data])
    
    # Get unique confidence scores
    unique_confs = np.unique(confidences)
    total_samples = len(confidence_data)
    
    # Calculate accuracy and percentage for each confidence score
    conf_means = []
    conf_percentages = []
    confidence_counts = {}
    
    for conf in unique_confs:
        mask = confidences == conf
        count = np.sum(mask)
        confidence_counts[conf] = count
        
        if count > 0:
            accuracy = np.mean(predictions[mask] == truths[mask])
            conf_means.append(accuracy)
        else:
            conf_means.append(0)
        
        # Calculate percentage for this confidence score
        percentage = (count / total_samples) * 100 if total_samples > 0 else 0
        conf_percentages.append(percentage)
    
    conf_means = np.array(conf_means)
    conf_percentages = np.array(conf_percentages)
    
    # Calculate weighted values (accuracy × percentage) - matching trainer.py
    weighted_values = conf_means * (conf_percentages)
    weighted_values_to_plot = conf_means * (conf_percentages/100)
    
    weighted_prob = softmax_temp(weighted_values, temp=3.0)
    mean_weighted_prob = np.percentile(weighted_prob, 80)
    confident_scores = weighted_prob[weighted_prob >= mean_weighted_prob]
    
    # Print summary statistics
    overall_accuracy = np.mean(predictions == truths)
    mean_confidence = np.mean(confidences)
    
    print(f"Overall validation accuracy: {overall_accuracy:.3f}")
    print(f"Confidence range: {min(confidences):.0f} - {max(confidences):.0f}")
    print(f"Mean confidence: {mean_confidence:.2f}")
    print(f"Total unique confidence scores: {len(unique_confs)}")
    
    # Extract actual confident score values (not range)
    confident_score_indices = np.where(np.isin(weighted_prob, confident_scores))[0]
    if len(confident_score_indices) > 0:
        confident_score_values = unique_confs[confident_score_indices]
        print(f"Confident scores: {confident_score_values}")
    else:
        confident_score_values = np.array([])

    pd.DataFrame(unique_confs, columns=['confidence']).to_csv(f'{RES_DIR}/unique_confidences.csv')
    pd.DataFrame(weighted_values_to_plot, columns=['weighted_value']).to_csv(f'{RES_DIR}/weighted_values.csv')
    pd.DataFrame(confidence_counts.items(), columns=['confidence', 'count']).to_csv(f'{RES_DIR}/confidence_counts.csv')
    pd.DataFrame(weighted_prob, columns=['weighted_prob']).to_csv(f'{RES_DIR}/weighted_probabilities.csv')
    pd.DataFrame(confident_scores, columns=['confident_score']).to_csv(f'{RES_DIR}/confident_scores.csv')
    
    return confidences, (predictions == truths), confident_score_values

def main():
    parser = argparse.ArgumentParser(description="Retraining under Distribution Shift Test")
    parser.add_argument("--arch", default="tiny", 
                       choices=["dense", "wide", "tiny"], help="Architecture to test")
    # parser.add_argument("--eval-random-bnn", action="store_true", 
    #                    help="Train and evaluate a random featured bnn model for comparison.")

    args = parser.parse_args()
    global RES_DIR
    ARCH = args.arch
    RES_DIR = f'results/simple_cross_dataset_eval_{ARCH}'
    ENABLE_RANDOM_BNN = True

    
    print("🧪 DISTRIBUTION SHIFT TEST")
    print(f"Architecture: {ARCH}")
    print()

    # Load datasets
    print("Loading CICIDS2017...")
    X_cic, Y_cic = load_dataset('CICIDS2017')
    X_cic_train, X_cic_test, Y_cic_train, Y_cic_test = train_test_split(
        X_cic, Y_cic, train_size=0.8, random_state=42, stratify=Y_cic)
    
    # Create validation set from CICIDS2017
    X_cic_test, X_cic_val, Y_cic_test, Y_cic_val = train_test_split(
        X_cic_test, Y_cic_test, train_size=0.9, random_state=42, stratify=Y_cic_test)
    
    print("Loading CIC_UNSW_NB15...")
    X_unsw, Y_unsw = load_dataset('CIC_UNSW_NB15')
    X_unsw_train, X_unsw_test, Y_unsw_train, Y_unsw_test = train_test_split(
        X_unsw, Y_unsw, train_size=0.03, random_state=42, stratify=Y_unsw)

    # Create validation set from UNSW
    X_unsw_test, X_unsw_val, Y_unsw_test, Y_unsw_val = train_test_split(
        X_unsw_test, Y_unsw_test, train_size=0.9, random_state=42, stratify=Y_unsw_test)

    X_tr = np.vstack([X_cic_train, X_unsw_train])
    Y_tr = np.hstack([Y_cic_train, Y_unsw_train])
    
    # Merge validation sets
    X_val_merged = np.vstack([X_cic_val, X_unsw_val])
    Y_val_merged = np.hstack([Y_cic_val, Y_unsw_val])

    # shuffle validation set
    val_shuffle_indices = np.random.permutation(len(X_val_merged))
    X_val_merged = X_val_merged[val_shuffle_indices]
    Y_val_merged = Y_val_merged[val_shuffle_indices]

    # Print dataset statistics
    print(f"\nDataset Statistics:")
    print(f"Training samples: {len(X_tr):,} ({len(X_cic_train):,} CICIDS2017 + {len(X_unsw_train):,} UNSW-NB15)")
    print(f"Validation samples: {len(X_val_merged):,} ({len(X_cic_val):,} CICIDS2017 + {len(X_unsw_val):,} UNSW-NB15)")
    print(f"Test samples (CICIDS2017): {len(X_cic_test):,}")
    print(f"Test samples (UNSW-NB15): {len(X_unsw_test):,}")
    print(f"Features: {X_tr.shape[1]}")

    print("\nInit TF BNN Random")
    if ENABLE_RANDOM_BNN:
        bnn_rand = SimpleTrainer('tf_rand_bnn', ARCH, 'cpu')
        bnn_rand.reset_model()  # Use default BNN input size
    else:
        bnn_rand = None
    
    print("\nInit TF BNN SHAP")
    bnn_shap = SimpleTrainer('tf_bnn_shap', ARCH, 'cpu')
    bnn_shap.reset_model()  # This will use the default BNN input size
    
    print("\nInit MLP teacher")
    teacher = SimpleTrainer('mlp', ARCH, 'cpu')
    teacher.reset_model(X_tr.shape[1])
    
    if ENABLE_RANDOM_BNN:
        print(f'BNN random model input size: {bnn_rand.nn_input_size} features')
    print(f'BNN SHAP model input size: {bnn_shap.nn_input_size} features')
    print(f'MLP model input size: {X_tr.shape[1]} features')

    # Select random features for random BNN
    if ENABLE_RANDOM_BNN:
        random_feat_idx = np.random.choice(X_tr.shape[1], bnn_rand.nn_input_size, replace=False)
        print(f"Selected random features: {random_feat_idx[:10]}...")  # Show first 10

        print("\nTraining BNN random model (random features)")
        bnn_rand.train(X_tr[:, random_feat_idx], Y_tr, verbose=True)  # Use random features
    else:
        random_feat_idx = None

    # Train MLP teacher on the same training split
    print("\nTraining MLP teacher...")
    teacher.train(X_tr, Y_tr, verbose=True)
    
    # Set MLP teacher data for SHAP computation
    cic_random_idx = np.random.choice(X_cic_train.shape[0], 1000, replace=False)
    unsw_random_idx = np.random.choice(X_unsw_train.shape[0], 500, replace=False)
    shap_X_tr = np.concatenate([X_cic_train[cic_random_idx], X_unsw_train[unsw_random_idx]])
    shap_Y_tr = np.concatenate([Y_cic_train[cic_random_idx], Y_unsw_train[unsw_random_idx]])
    
    # Properly shuffle the combined dataset
    shuffle_indices = np.random.permutation(len(shap_X_tr))
    shap_X_tr = shap_X_tr[shuffle_indices]
    shap_Y_tr = shap_Y_tr[shuffle_indices]

    teacher.X_tr, teacher.Y_tr = shap_X_tr, shap_Y_tr

    # Use MLP teacher for SHAP computation
    print("\nUsing MLP teacher for SHAP computation...")
    from ml_helpers.shap_explainer import ShapExplainer
    shap_result, indices_file = ShapExplainer.run_from_trainer(teacher, force_recompute=True, use_eval=False, out_dir=f'{RES_DIR}/shap_results')
    import json
    with open(indices_file, 'r') as f:
        shap_data = json.load(f)
    shap_feat_idx = shap_data['feature_indices'][:bnn_shap.nn_input_size]
    
    print(f"Selected {len(shap_feat_idx)} SHAP features for BNN SHAP model")
    print(f"SHAP feature indices: {shap_feat_idx[:10]}...")  # Show first 10
    
    print(f"\nTraining BNN student (SHAP features)")
    res = bnn_shap.train(X_tr[:,shap_feat_idx], Y_tr, verbose=True)
    pd.DataFrame(res['train_accuracies'], columns=['batch_accuracies']).to_csv(f'{RES_DIR}/bnn_shap_train_accuracies.csv')

    print("\nAnalyzing BNN SHAP confidence distribution...")
    X_val_shaped_shap = X_val_merged[:, shap_feat_idx]
    confidences_shap, correct_preds_shap, confident_score_array_shap = analyze_confidence_distribution(bnn_shap, X_val_shaped_shap, Y_val_merged)

    # Initialize critical sample collection for SHAP BNN retraining
    critical_samples_X = []
    critical_samples_Y = []
    retrained_bnn_shap = None  # Will hold the retrained model
    retraining_completed = False

    # Prepare evaluation batches

    
    # distribution shift starting point
    shift_start_batch = DATASET_SWITCH_START
    # max distribution shift point
    max_percentage_batch = DATASET_SWITCH_END 
    shift_duration = max_percentage_batch - shift_start_batch
    
    print(f"Gradual distribution shift:")
    print(f"- Batches 1-{shift_start_batch}: 100% CICIDS2017")
    print(f"- Batches {shift_start_batch+1}-{max_percentage_batch}: Gradual increase to {MAX_UNSW_FRACTION*100:.0f}% UNSW-NB15")
    print(f"- Batches {max_percentage_batch+1}-{N_BATCHES}: Constant {MAX_UNSW_FRACTION*100:.0f}% UNSW-NB15")
    
    # Pre-calculate samples needed for each batch
    total_cic_needed = 0
    total_unsw_needed = 0
    unsw_fractions = []
    
    for i in range(N_BATCHES):
        if i < shift_start_batch:
            unsw_fraction = 0.0
        elif i < max_percentage_batch:
            progress = (i - shift_start_batch) / shift_duration
            unsw_fraction = progress * MAX_UNSW_FRACTION
        else:
            unsw_fraction = MAX_UNSW_FRACTION
        
        unsw_fractions.append(unsw_fraction)
        
        unsw_samples_in_batch = int(BATCH_SIZE * unsw_fraction)
        cic_samples_in_batch = BATCH_SIZE - unsw_samples_in_batch
        
        total_cic_needed += cic_samples_in_batch
        total_unsw_needed += unsw_samples_in_batch
    
    print(f"Total samples needed: {total_cic_needed} CICIDS2017, {total_unsw_needed} UNSW-NB15")
    print(f"Total monitoring samples: {total_cic_needed + total_unsw_needed:,} across {N_BATCHES} batches")
    
    cic_eval_samples = X_cic_test[:total_cic_needed]
    cic_eval_labels = Y_cic_test[:total_cic_needed]
    unsw_eval_samples = X_unsw_test[:total_unsw_needed]
    unsw_eval_labels = Y_unsw_test[:total_unsw_needed]
    
    eval_batches_X = []
    eval_batches_Y = []
    cic_idx = 0
    unsw_idx = 0
    
    for i in range(N_BATCHES):
        unsw_fraction = unsw_fractions[i]
        unsw_samples_in_batch = int(BATCH_SIZE * unsw_fraction)
        cic_samples_in_batch = BATCH_SIZE - unsw_samples_in_batch
        
        batch_cic_X = cic_eval_samples[cic_idx:cic_idx + cic_samples_in_batch]
        batch_cic_Y = cic_eval_labels[cic_idx:cic_idx + cic_samples_in_batch]
        cic_idx += cic_samples_in_batch
        
        if unsw_samples_in_batch > 0:
            batch_unsw_X = unsw_eval_samples[unsw_idx:unsw_idx + unsw_samples_in_batch]
            batch_unsw_Y = unsw_eval_labels[unsw_idx:unsw_idx + unsw_samples_in_batch]
            unsw_idx += unsw_samples_in_batch
            
            batch_X = np.vstack([batch_cic_X, batch_unsw_X])
            batch_Y = np.hstack([batch_cic_Y, batch_unsw_Y])
            
            shuffle_idx = np.random.permutation(len(batch_X))
            batch_X = batch_X[shuffle_idx]
            batch_Y = batch_Y[shuffle_idx]
        else:
            batch_X = batch_cic_X
            batch_Y = batch_cic_Y
        
        eval_batches_X.append(batch_X)
        eval_batches_Y.append(batch_Y)
    
    print(f"\nEvaluating on {N_BATCHES} batches ({BATCH_SIZE} samples each)")
    
    rand_accuracies = []
    shap_accuracies = []
    teacher_accuracies = []

    retrain_batch = 0
    for i in range(N_BATCHES):
        batch_X = eval_batches_X[i]
        batch_Y = eval_batches_Y[i]

        if ENABLE_RANDOM_BNN:
            rand_res = bnn_rand.eval_model(batch_X[:, random_feat_idx], batch_Y, verbose=False)
            rand_accuracies.append(rand_res['accuracy'])
        
        teacher_res = teacher.eval_model(batch_X, batch_Y, verbose=False)
        teacher_accuracies.append(teacher_res['accuracy'])

        # Collect critical samples for SHAP BNN before retraining
        if not retraining_completed and len(critical_samples_X) < CRITICAL_SAMPLES_WINDOW:
            with torch.no_grad():
                batch_tensor = torch.tensor(batch_X[:, shap_feat_idx], dtype=torch.float32, device=bnn_shap.device)
                confidences = get_confidence_safe(bnn_shap, batch_tensor)
                
                for j, conf in enumerate(confidences.numpy()):
                    if conf not in confident_score_array_shap and len(critical_samples_X) < CRITICAL_SAMPLES_WINDOW:
                        critical_samples_X.append(batch_X[j])
                        # Label critical sample with MLP prediction instead of ground truth
                        with torch.no_grad():
                            mlp_logits = teacher.model(torch.tensor(batch_X[j:j+1], dtype=torch.float32, device=teacher.device))
                            mlp_label = mlp_logits.argmax().item()
                        critical_samples_Y.append(mlp_label)

        # Retrain SHAP BNN when enough critical samples are gathered
        if not retraining_completed and len(critical_samples_X) >= CRITICAL_SAMPLES_WINDOW:
            retrain_batch = i + 1
            retraining_completed = True
            print(f"\nRetraining SHAP BNN with {len(critical_samples_X)} critical samples at batch {retrain_batch}...")
            
            # Take 100,000 samples from original training data
            retrain_samples = 95000
            # retrain_samples = 70000
            if len(X_tr) >= retrain_samples:
                retrain_indices = np.random.choice(len(X_tr), retrain_samples, replace=False)
                retrain_og_X = X_tr[retrain_indices]
                retrain_og_Y = Y_tr[retrain_indices]
            else:
                retrain_og_X = X_tr
                retrain_og_Y = Y_tr
            
            # Combine selected original training data with critical samples
            retrain_X = np.vstack([retrain_og_X, np.array(critical_samples_X)])
            retrain_Y = np.hstack([retrain_og_Y, np.array(critical_samples_Y)])
            
            print(f"Retraining dataset composition:")
            print(f"  Original training subset: {len(retrain_og_X):,} samples (from {len(X_tr):,} total)")
            print(f"  Critical samples: {len(critical_samples_X):,} samples (MLP-labeled)")
            print(f"  Total retraining: {len(retrain_X):,} samples")
            
            # Shuffle combined dataset
            shuffle_idx = np.random.permutation(len(retrain_X))
            retrain_X = retrain_X[shuffle_idx]
            retrain_Y = retrain_Y[shuffle_idx]
            
            # Create new trainer instance for retraining
            print("Creating new SHAP BNN trainer instance for retraining...")
            retrained_bnn_shap = SimpleTrainer('tf_bnn_shap_retrained', ARCH, 'cpu')
            retrained_bnn_shap.reset_model()
            retrained_bnn_shap.epochs += 40
            retrained_bnn_shap.train(retrain_X[:, shap_feat_idx], retrain_Y, verbose=True)

        # Evaluate SHAP BNN (use retrained model if available)
        if retraining_completed:
            print('Retrained model available. Take it')
            current_shap_model = retrained_bnn_shap
        else:
            current_shap_model = bnn_shap
        shap_res = current_shap_model.eval_model(batch_X[:, shap_feat_idx], batch_Y, verbose=False)
        shap_accuracies.append(shap_res['accuracy'])

        retrain_flag = "[RETRAINED]" if i + 1 == retrain_batch else ""
        critical_count_info = f"(Critical: {len(critical_samples_X)})" if not retraining_completed else ""
        unsw_pct = unsw_fractions[i] * 100
        
        if ENABLE_RANDOM_BNN:
            print(f"Batch {i+1:2d} ({unsw_pct:.1f}% UNSW) - BNN Random: {rand_res['accuracy']:.3f}, BNN SHAP: {shap_res['accuracy']:.3f}, MLP: {teacher_res['accuracy']:.3f} {critical_count_info} {retrain_flag}")
        else:
            print(f"Batch {i+1:2d} ({unsw_pct:.1f}% UNSW) - BNN SHAP: {shap_res['accuracy']:.3f}, MLP: {teacher_res['accuracy']:.3f} {critical_count_info} {retrain_flag}")

    os.makedirs(RES_DIR, exist_ok=True)
    pd.DataFrame(rand_accuracies, columns=['accuracy']).to_csv(f'{RES_DIR}/bnn_random_accuracies.csv')
    pd.DataFrame(teacher_accuracies, columns=['accuracy']).to_csv(f'{RES_DIR}/mlp_accuracies.csv')
    pd.DataFrame(shap_accuracies, columns=['accuracy']).to_csv(f'{RES_DIR}/bnn_shap_accuracies.csv')
    
    with open(f'{RES_DIR}/config.json', 'w') as f:
        curr_config = {
            'MAX_UNSW_FRACTION': MAX_UNSW_FRACTION,
            'DATASET_SWITCH_START': DATASET_SWITCH_START,
            'DATASET_SWITCH_END':DATASET_SWITCH_END,
            'CRITICAL_SAMPLES_WINDOW': CRITICAL_SAMPLES_WINDOW,
            'N_BATCHES': N_BATCHES,
            'BATCH_SIZE': BATCH_SIZE,
            'ENABLE_RANDOM_BNN': ENABLE_RANDOM_BNN,
            'RETRAIN_BATCH': retrain_batch,
        }
        json.dump(curr_config, f)
    
    # Summary by phase - Domain shift analysis without retraining
    if ENABLE_RANDOM_BNN:
        pure_cic_acc_rand = np.mean([acc for i, acc in enumerate(rand_accuracies) if i < shift_start_batch])
        gradual_shift_acc_rand = np.mean([acc for i, acc in enumerate(rand_accuracies) if shift_start_batch <= i < max_percentage_batch])
        max_shift_acc_rand = np.mean([acc for i, acc in enumerate(rand_accuracies) if i >= max_percentage_batch])
        
        print(f"\nBNN (random) Summary:")
        print(f"Pure CICIDS2017 accuracy: {pure_cic_acc_rand:.3f}")
        print(f"Gradual shift accuracy: {gradual_shift_acc_rand:.3f}")
        print(f"Max shift accuracy ({MAX_UNSW_FRACTION*100:.0f}% UNSW): {max_shift_acc_rand:.3f}")
        print(f"Total performance drop: {pure_cic_acc_rand - max_shift_acc_rand:.3f}")

    # BNN SHAP summary
    pure_cic_acc_shap = np.mean([acc for i, acc in enumerate(shap_accuracies) if i < shift_start_batch])
    gradual_shift_acc_shap = np.mean([acc for i, acc in enumerate(shap_accuracies) if shift_start_batch <= i < max_percentage_batch])
    max_shift_acc_shap = np.mean([acc for i, acc in enumerate(shap_accuracies) if i >= max_percentage_batch])
    
    # Calculate post-retraining metrics if retraining occurred
    if retrain_batch > 0 and retrain_batch < len(shap_accuracies):
        post_retrain_accuracies = [acc for i, acc in enumerate(shap_accuracies) if i >= retrain_batch]
        post_retrain_avg_acc = np.mean(post_retrain_accuracies)
        post_retrain_max_acc = np.max(post_retrain_accuracies)
        avg_accuracy_increase = post_retrain_avg_acc - max_shift_acc_shap
    else:
        post_retrain_avg_acc = None
        post_retrain_max_acc = None
        avg_accuracy_increase = None
    
    print(f"\nBNN (SHAP) Summary:")
    print(f"Pure CICIDS2017 accuracy: {pure_cic_acc_shap:.3f}")
    print(f"Gradual shift accuracy: {gradual_shift_acc_shap:.3f}")
    print(f"Max shift accuracy ({MAX_UNSW_FRACTION*100:.0f}% UNSW): {max_shift_acc_shap:.3f}")
    if post_retrain_avg_acc is not None:
        print(f"Post-retraining average accuracy: {post_retrain_avg_acc:.3f}")
        print(f"Post-retraining maximum accuracy: {post_retrain_max_acc:.3f}")
        print(f"Average accuracy increase after retraining: {avg_accuracy_increase:+.3f}")
    print(f"Total performance drop: {pure_cic_acc_shap - max_shift_acc_shap:.3f}")

    pure_cic_acc_teacher = np.mean([acc for i, acc in enumerate(teacher_accuracies) if i < shift_start_batch])
    gradual_shift_acc_teacher = np.mean([acc for i, acc in enumerate(teacher_accuracies) if shift_start_batch <= i < max_percentage_batch])
    max_shift_acc_teacher = np.mean([acc for i, acc in enumerate(teacher_accuracies) if i >= max_percentage_batch])
    print(f"\nMLP Summary:")
    print(f"Pure CICIDS2017 accuracy: {pure_cic_acc_teacher:.3f}")
    print(f"Gradual shift accuracy: {gradual_shift_acc_teacher:.3f}")
    print(f"Max shift accuracy ({MAX_UNSW_FRACTION*100:.0f}% UNSW): {max_shift_acc_teacher:.3f}")
    print(f"Total performance drop: {pure_cic_acc_teacher - max_shift_acc_teacher:.3f}")


if __name__ == "__main__":
    main()
