#!/usr/bin/env python3

import os
import time
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from ml_helpers.simple_trainer import SimpleTrainer
from ml_helpers.utils import analyze_confidence_distribution, get_confidence_safe
from helpers.utils import load_dataset, get_cfg
import random
import argparse
from ml_helpers.shap_explainer import ShapExplainer


np.random.seed(42)
torch.manual_seed(42)
random.seed(42)

EXPERIMENT_NAME = 'DS_RETRAINING'

def main():
    parser = argparse.ArgumentParser(description="Distribition Shift Retraining Experiment | config options in configs/experiments.ini")
    parser.add_argument("-m", default="binocular_tiny", 
                       choices=["binocular_dense", "binocular_wide", "binocular_tiny"], help="Architecture to test")

    args = parser.parse_args()
    RES_DIR = f'results/simple_cross_dataset_eval_{args.m}'

    experiment_cfg = get_cfg('experiments')
    MAX_UNSW_FRACTION = experiment_cfg.getfloat(EXPERIMENT_NAME, 'MAX_UNSW_FRACTION')
    DATASET_SWITCH_START = experiment_cfg.getint(EXPERIMENT_NAME, 'DATASET_SWITCH_START')
    DATASET_SWITCH_END = experiment_cfg.getint(EXPERIMENT_NAME, 'DATASET_SWITCH_END')
    BATCH_SIZE = experiment_cfg.getint(EXPERIMENT_NAME, 'BATCH_SIZE')
    N_BATCHES = experiment_cfg.getint(EXPERIMENT_NAME, 'N_BATCHES')
    CRITICAL_RETRAIN_SAMPLES = experiment_cfg.getint(f'{EXPERIMENT_NAME}-{args.m.upper()}', 'CRITICAL_RETRAIN_SAMPLES')
    OG_RETRAIN_SAMPLES = experiment_cfg.getint(f'{EXPERIMENT_NAME}-{args.m.upper()}', 'OG_RETRAIN_SAMPLES')
    EMPIRICAL_RETRAIN_SAMPLES = experiment_cfg.getint(f'{EXPERIMENT_NAME}-{args.m.upper()}', 'EMPIRICAL_RETRAIN_SAMPLES')
    RETRAINING_EPOCHS = experiment_cfg.getint(f'{EXPERIMENT_NAME}-{args.m.upper()}', 'RETRAINING_EPOCHS')

    print('Create results dirs...',end='')
    os.makedirs(RES_DIR, exist_ok=True)
    os.makedirs(f'{RES_DIR}/weights', exist_ok=True)
    print(' OK\n')
    print("🧪 DISTRIBUTION SHIFT TEST")
    print(f"Model: {args.m}\n")

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

    X_tr, Y_tr = np.vstack([X_cic_train, X_unsw_train]), np.hstack([Y_cic_train, Y_unsw_train])
    X_val, Y_val = np.vstack([X_cic_val, X_unsw_val]), np.hstack([Y_cic_val, Y_unsw_val])

    # shuffle validation set
    val_shuffle_indices = np.random.permutation(len(X_val))
    X_val, Y_val = X_val[val_shuffle_indices], Y_val[val_shuffle_indices]

    # Print dataset statistics
    print(f"\nDS DATASET STATISTICS:")
    print(f"Training samples: {len(X_tr):,} ({len(X_cic_train):,} CICIDS2017 + {len(X_unsw_train):,} UNSW-NB15)")
    print(f"Validation samples: {len(X_val):,} ({len(X_cic_val):,} CICIDS2017 + {len(X_unsw_val):,} UNSW-NB15)")
    print(f"Test samples (CICIDS2017): {len(X_cic_test):,}")
    print(f"Test samples (UNSW-NB15): {len(X_unsw_test):,}")
    print(f"Features: {X_tr.shape[1]}")

    print("\nInit TF BNN Random")
    binocular_rand = SimpleTrainer(f'{args.m}', 'cpu')
    binocular_rand.reset_model()  # Use default BNN input size
    
    print("\nInit TF BNN SHAP")
    binocular_shap = SimpleTrainer(f'{args.m}', 'cpu')
    binocular_shap.reset_model()  # This will use the default BNN input size
    
    print("\nInit MLP teacher")
    teacher = SimpleTrainer(f'binocular_teacher', 'cpu')
    teacher.reset_model(X_tr.shape[1])
    
    print(f'BNN random model input size: {binocular_rand.nn_input_size} features')
    print(f'BNN SHAP model input size: {binocular_shap.nn_input_size} features')
    print(f'MLP model input size: {X_tr.shape[1]} features')

    # Select random features for random BNN
    random_feat_idx = np.random.choice(X_tr.shape[1], binocular_rand.nn_input_size, replace=False)
    print(f"Selected random features: {random_feat_idx[:10]}...")  # Show first 10

    print("\nTraining BNN random model (random features)")
    res=binocular_rand.train(X_tr[:, random_feat_idx], Y_tr, verbose=True)  # Use random features
    pd.DataFrame(res['train_accuracies'], columns=['batch_accuracies']).to_csv(f'{RES_DIR}/{args.m}_train_rand_accuracies.csv')

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
    shap_X_tr, shap_Y_tr = shap_X_tr[shuffle_indices], shap_Y_tr[shuffle_indices]

    teacher.X_tr, teacher.Y_tr = shap_X_tr, shap_Y_tr

    # Use MLP teacher for SHAP computation
    print("\nUsing MLP teacher for SHAP computation...")
    _, indices_file = ShapExplainer.run_from_trainer(teacher, force_recompute=True, use_eval=False, out_dir=f'{RES_DIR}/shap_results')
    import json
    with open(indices_file, 'r') as f:
        shap_data = json.load(f)
    shap_feat_idx = shap_data['feature_indices'][:binocular_shap.nn_input_size]
    
    print(f"Selected {len(shap_feat_idx)} SHAP features for BNN SHAP model")
    print(f"SHAP feature indices: {shap_feat_idx[:10]}...")  # Show first 10
    
    print(f"\nTraining BNN student (SHAP features)")
    base_training_start = time.perf_counter()
    res = binocular_shap.train(X_tr[:,shap_feat_idx], Y_tr, verbose=True)
    base_training_time = time.perf_counter() - base_training_start
    pd.DataFrame(res['train_accuracies'], columns=['batch_accuracies']).to_csv(f'{RES_DIR}/{args.m}_train_accuracies.csv')
    
    # Save pre-retraining models
    teacher.save_model(f'{RES_DIR}/weights/pre_retraining_teacher.pth')
    binocular_rand.save_model(f'{RES_DIR}/weights/pre_retraining_bnn_rand.pth')
    binocular_shap.save_model(f'{RES_DIR}/weights/pre_retraining_bnn_shap.pth')

    print("\nAnalyzing BNN SHAP confidence distribution...")
    X_val_shaped_shap = X_val[:, shap_feat_idx]
    _, _, confident_score_array_shap = analyze_confidence_distribution(binocular_shap, X_val_shaped_shap, Y_val, RES_DIR)

    # Initialize critical sample collection for SHAP BNN retraining
    critical_samples_X = []
    critical_samples_Y = []
    retraining_completed = False
    shift_duration = DATASET_SWITCH_END - DATASET_SWITCH_START
    
    print(f"Gradual distribution shift:")
    print(f"- Batches 1-{DATASET_SWITCH_START}: 100% CICIDS2017")
    print(f"- Batches {DATASET_SWITCH_START+1}-{DATASET_SWITCH_END}: Gradual increase to {MAX_UNSW_FRACTION*100:.0f}% UNSW-NB15")
    print(f"- Batches {DATASET_SWITCH_END+1}-{N_BATCHES}: Constant {MAX_UNSW_FRACTION*100:.0f}% UNSW-NB15")
    
    # Pre-calculate samples needed for each batch
    total_cic_needed = 0
    total_unsw_needed = 0
    unsw_fractions = []
    
    for i in range(N_BATCHES):
        if i < DATASET_SWITCH_START:
            unsw_fraction = 0.0
        elif i < DATASET_SWITCH_END:
            progress = (i - DATASET_SWITCH_START) / shift_duration
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
    
    rand_preds = []
    shap_preds = []
    teacher_preds = []
    shap_no_conf_preds = []
    targets = []
    batches = []

    X_evaluation_samples_so_far = []
    Y_evaluation_samples_so_far = []

    retrain_batch = 0
    for batch_no in range(N_BATCHES):
        batch_X = eval_batches_X[batch_no]
        batch_Y = eval_batches_Y[batch_no]
        targets.extend(batch_Y)
        batches.extend([batch_no+1]*len(batch_Y))

        if not retraining_completed:
            X_evaluation_samples_so_far.extend(batch_X)
            Y_evaluation_samples_so_far.extend(batch_Y)

        rand_eval = binocular_rand.eval_model(batch_X[:, random_feat_idx], batch_Y, verbose=False)
        rand_preds.extend(rand_eval['predictions'])
        
        teacher_eval = teacher.eval_model(batch_X, batch_Y, verbose=False)
        teacher_preds.extend(teacher_eval['predictions'])

        # Collect enough samples before retraining
        # if not retraining_completed and len(critical_samples_X) < CRITICAL_SAMPLES_WINDOW:
        if not retraining_completed:
            with torch.no_grad():
                batch_tensor = torch.tensor(batch_X[:, shap_feat_idx], dtype=torch.float32, device=binocular_shap.device)
                confidences = get_confidence_safe(binocular_shap, batch_tensor)
                
                for j, conf in enumerate(confidences.numpy()):
                    # if conf not in confident_score_array_shap and len(critical_samples_X) < CRITICAL_SAMPLES_WINDOW:
                    if conf not in confident_score_array_shap:

                        critical_samples_X.append(batch_X[j])
                        # Label critical sample with MLP prediction instead of ground truth
                        with torch.no_grad():
                            mlp_logits = teacher.model(torch.tensor(batch_X[j:j+1], dtype=torch.float32, device=teacher.device))
                            mlp_label = mlp_logits.argmax().item()
                        critical_samples_Y.append(mlp_label)

        # Retrain SHAP BNN when enough critical samples are gathered
        if (not retraining_completed and len(critical_samples_X) >= CRITICAL_RETRAIN_SAMPLES 
            and len(X_evaluation_samples_so_far) >= CRITICAL_RETRAIN_SAMPLES+EMPIRICAL_RETRAIN_SAMPLES
            and batch_no >= N_BATCHES//2):

            print(f"\nCritical samples samples gathered {len(critical_samples_X)} at batch {batch_no}, keep most recent {CRITICAL_RETRAIN_SAMPLES} for retraining.")
            critical_samples_X = critical_samples_X[-CRITICAL_RETRAIN_SAMPLES:]
            critical_samples_Y = critical_samples_Y[-CRITICAL_RETRAIN_SAMPLES:]

            retrain_batch = batch_no + 1
            retraining_completed = True

            # Copy predictions and accuracies up to this point since retrained_bnn_shap and retrained_bnn_shap_no_conf will diverge after retraining only
            shap_no_conf_preds = shap_preds.copy()

            # Take OG_RETRAIN_SAMPLES samples from original training data
            if len(X_tr) >= OG_RETRAIN_SAMPLES:
                retrain_indices = np.random.choice(len(X_tr), OG_RETRAIN_SAMPLES, replace=False)
                retrain_og_X = X_tr[retrain_indices]
                retrain_og_Y = Y_tr[retrain_indices]
            else:
                retrain_og_X = X_tr
                retrain_og_Y = Y_tr

            add_retrain_ids = np.random.choice(len(X_evaluation_samples_so_far), EMPIRICAL_RETRAIN_SAMPLES, replace=False)
            add_retrain_samples_X = np.array(X_evaluation_samples_so_far)[add_retrain_ids]
            add_retrain_samples_Y = np.array(Y_evaluation_samples_so_far)[add_retrain_ids]
            
            # Combine selected original training data with critical samples
            retrain_X = np.vstack([retrain_og_X, np.array(critical_samples_X), add_retrain_samples_X])
            retrain_Y = np.hstack([retrain_og_Y, np.array(critical_samples_Y), add_retrain_samples_Y])

            print(f"Retraining dataset composition:")
            print(f"  Original training subset: {len(retrain_og_X):,} samples (from {len(X_tr):,} total)")
            print(f"  Empirical training subset: {len(add_retrain_samples_X):,} samples (from {len(X_evaluation_samples_so_far):,} total)")
            print(f"  Critical samples: {len(critical_samples_X):,} samples (MLP-labeled)")
            print(f"  Total retraining: {len(retrain_X):,} samples")
            
            # Shuffle combined dataset
            shuffle_idx = np.random.permutation(len(retrain_X))
            retrain_X = retrain_X[shuffle_idx]
            retrain_Y = retrain_Y[shuffle_idx]
            
            # Create new trainer instance for retraining
            print("\nCreating new SHAP BNN trainer instance for retraining...")
            retraining_start = time.perf_counter()
            retrained_bnn_shap = SimpleTrainer(f'{args.m}', 'cpu')
            retrained_bnn_shap.reset_model()
            retrained_bnn_shap.epochs = RETRAINING_EPOCHS
            res=retrained_bnn_shap.train(retrain_X[:, shap_feat_idx], retrain_Y, verbose=True)
            retraining_time = time.perf_counter() - retraining_start
            pd.DataFrame(res['train_accuracies'], columns=['batch_accuracies']).to_csv(f'{RES_DIR}/{args.m}_retrain_accuracies.csv')

            # Save timing measurements
            timing_data = {
                'phase': ['base_student_bnn_training', 'teacher_label_student_retraining'],
                'time_seconds': [base_training_time, retraining_time],
                'epochs': [binocular_shap.epochs, RETRAINING_EPOCHS]
            }
            pd.DataFrame(timing_data).to_csv(f'{RES_DIR}/{args.m}_time.csv', index=False)
            print(f"\nTiming saved to {RES_DIR}/{args.m}_time.csv")
            print(f"  Base student BNN training: {base_training_time:.2f}s ({binocular_shap.epochs} epochs)")
            print(f"  Teacher label + student retraining: {retraining_time:.2f}s ({RETRAINING_EPOCHS} epochs)")

            # Create new trainer instance for retraining
            print("\nCreating new SHAP BNN trainer instance NO CONFIDENCE for retraining...")
            X_evaluation_samples_so_far = np.array(X_evaluation_samples_so_far)
            Y_evaluation_samples_so_far = np.array(Y_evaluation_samples_so_far)
            no_conf_indices = np.random.choice(len(X_evaluation_samples_so_far), CRITICAL_RETRAIN_SAMPLES+EMPIRICAL_RETRAIN_SAMPLES, replace=False)
            X_retrain_no_conf = X_evaluation_samples_so_far[no_conf_indices]
            Y_retrain_no_conf = Y_evaluation_samples_so_far[no_conf_indices]
            X_retrain_no_conf = np.vstack([retrain_og_X, np.array(X_retrain_no_conf)])
            Y_retrain_no_conf = np.hstack([retrain_og_Y, np.array(Y_retrain_no_conf)])
            shuffle_idx = np.random.permutation(len(X_retrain_no_conf))
            X_retrain_no_conf = X_retrain_no_conf[shuffle_idx]
            Y_retrain_no_conf = Y_retrain_no_conf[shuffle_idx]
            
            retrained_bnn_shap_no_conf = SimpleTrainer(f'{args.m}', 'cpu')
            retrained_bnn_shap_no_conf.reset_model()
            retrained_bnn_shap_no_conf.epochs = RETRAINING_EPOCHS
            res=retrained_bnn_shap_no_conf.train(X_retrain_no_conf[:, shap_feat_idx], Y_retrain_no_conf, verbose=True)
            pd.DataFrame(res['train_accuracies'], columns=['batch_accuracies']).to_csv(f'{RES_DIR}/{args.m}_retrain_no_conf_accuracies.csv')

            # Save post-retraining models
            retrained_bnn_shap_no_conf.save_model(f'{RES_DIR}/weights/post_retraining_bnn_shap_no_conf.pth')
            retrained_bnn_shap.save_model(f'{RES_DIR}/weights/post_retraining_bnn_shap.pth')
        
        # Evaluate SHAP BNN (use retrained model if available)
        if retraining_completed:
            shap_no_conf_eval = retrained_bnn_shap_no_conf.eval_model(batch_X[:, shap_feat_idx], batch_Y, verbose=False)
            shap_no_conf_preds.extend(shap_no_conf_eval['predictions'])
            
            print('Retrained model available. Take it')
            current_shap_model = retrained_bnn_shap
        else:
            current_shap_model = binocular_shap
        shap_eval = current_shap_model.eval_model(batch_X[:, shap_feat_idx], batch_Y, verbose=False)
        shap_preds.extend(shap_eval['predictions'])

        retrain_flag = "[RETRAINED]" if batch_no + 1 == retrain_batch else ""
        critical_count_info = f"(Critical: {len(critical_samples_X)})" if not retraining_completed else ""
        unsw_pct = unsw_fractions[batch_no] * 100
        
        print(f"Batch {batch_no+1:2d} ({unsw_pct:.1f}% UNSW) - BNN Random: {rand_eval['accuracy']:.3f}, BNN SHAP: {shap_eval['accuracy']:.3f}, MLP: {teacher_eval['accuracy']:.3f} {critical_count_info} {retrain_flag}")

    shap_results = {
        'batch': batches,
        'targets': targets,
        'predictions': shap_preds,
    }
    shap_no_conf_results = {
        'batch': batches,
        'targets': targets,
        'predictions': shap_no_conf_preds,
    }
    teacher_results = {
        'batch': batches,
        'targets': targets,
        'predictions': teacher_preds,
    }
    rand_results = {
        'batch': batches,
        'targets': targets,
        'predictions': rand_preds,
    }
    pd.DataFrame(shap_results).to_csv(f'{RES_DIR}/{args.m}_results.csv', index=False)
    pd.DataFrame(shap_no_conf_results).to_csv(f'{RES_DIR}/{args.m}_no_conf_results.csv', index=False)
    pd.DataFrame(teacher_results).to_csv(f'{RES_DIR}/teacher_results.csv', index=False)
    pd.DataFrame(rand_results).to_csv(f'{RES_DIR}/{args.m}_random_results.csv', index=False)

    # Save timing if retraining didn't happen (fallback)
    if not retraining_completed:
        timing_data = {
            'phase': ['base_student_bnn_training', 'teacher_label_student_retraining'],
            'time_seconds': [base_training_time, None],
            'epochs': [binocular_shap.epochs, None]
        }
        pd.DataFrame(timing_data).to_csv(f'{RES_DIR}/{args.m}_time.csv', index=False)
        print(f"\nTiming saved to {RES_DIR}/{args.m}_time.csv")
        print(f"  Base student BNN training: {base_training_time:.2f}s ({binocular_shap.epochs} epochs)")
        print(f"  Teacher label + student retraining: N/A (retraining threshold not met)")

    with open(f'{RES_DIR}/config.json', 'w') as f:
        curr_config = {
            'MAX_UNSW_FRACTION': MAX_UNSW_FRACTION,
            'DATASET_SWITCH_START': DATASET_SWITCH_START,
            'DATASET_SWITCH_END':DATASET_SWITCH_END,
            'CRITICAL_SAMPLES_WINDOW': CRITICAL_RETRAIN_SAMPLES,
            'N_BATCHES': N_BATCHES,
            'BATCH_SIZE': BATCH_SIZE,
            'RETRAIN_BATCH': retrain_batch,
        }
        json.dump(curr_config, f)


if __name__ == "__main__":
    main()
