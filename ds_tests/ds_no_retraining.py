#!/usr/bin/env python3

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import torch
import torch.nn.functional as F
from sklearn.model_selection import train_test_split
from ml_helpers.simple_trainer import SimpleTrainer
from ml_helpers.utils import get_cfg, softmax_temp
from helpers.utils import load_dataset
import random
import argparse

np.random.seed(42)
torch.manual_seed(42)
random.seed(42)

EXPERIMENT_NAME = 'DS_NO_RETRAINING'

def main():
    parser = argparse.ArgumentParser(description="Distribition Shift Without Retraining Experiment | config options in configs/experiments.ini")
    parser.add_argument("--model", required=True, 
                       choices=["quark", "netbeacon"], help="Architecture to test")

    args = parser.parse_args()
    RES_DIR = f'results/simple_cross_dataset_eval_{args.model}'
    
    experiment_cfg = get_cfg('experiments')
    MAX_UNSW_FRACTION = experiment_cfg.getfloat(EXPERIMENT_NAME, 'MAX_UNSW_FRACTION')
    DATASET_SWITCH_START = experiment_cfg.getint(EXPERIMENT_NAME, 'DATASET_SWITCH_START')
    DATASET_SWITCH_END = experiment_cfg.getint(EXPERIMENT_NAME, 'DATASET_SWITCH_END')
    BATCH_SIZE = experiment_cfg.getint(EXPERIMENT_NAME, 'BATCH_SIZE')
    N_BATCHES = experiment_cfg.getint(EXPERIMENT_NAME, 'N_BATCHES')

    print('Create results dir...',end='')
    os.makedirs(RES_DIR, exist_ok=True)
    print(' OK\n')
    print("🧪 DISTRIBUTION SHIFT TEST")
    print(f"Architecture: {args.model}")

    # Load datasets
    print("\nLoading CICIDS2017...")
    X_cic, Y_cic = load_dataset('CICIDS2017', args.model)
    X_cic_train, X_cic_test, Y_cic_train, Y_cic_test = train_test_split(
        X_cic, Y_cic, train_size=0.8, random_state=42, stratify=Y_cic)
    
    # Create validation set from CICIDS2017
    X_cic_test, X_cic_val, Y_cic_test, Y_cic_val = train_test_split(
        X_cic_test, Y_cic_test, train_size=0.9, random_state=42, stratify=Y_cic_test)
    
    print("Loading CIC_UNSW_NB15...")
    X_unsw, Y_unsw = load_dataset('CIC_UNSW_NB15', args.model)
    X_unsw_train, X_unsw_test, Y_unsw_train, Y_unsw_test = train_test_split(
        X_unsw, Y_unsw, train_size=0.03, random_state=42, stratify=Y_unsw)

    # Create validation set from UNSW
    X_unsw_test, X_unsw_val, Y_unsw_test, Y_unsw_val = train_test_split(
        X_unsw_test, Y_unsw_test, train_size=0.9, random_state=42, stratify=Y_unsw_test)

    X_tr, Y_tr = np.vstack([X_cic_train, X_unsw_train]), np.hstack([Y_cic_train, Y_unsw_train])
    X_val, Y_val = np.vstack([X_cic_val, X_unsw_val]), np.hstack([Y_cic_val, Y_unsw_val])

    # shuffle validation set
    val_shuffle_indices = np.random.permutation(len(X_val))
    X_val = X_val[val_shuffle_indices]
    Y_val = Y_val[val_shuffle_indices]

    # Print dataset statistics
    print(f"\nDataset Statistics:")
    print(f"Training samples: {len(X_tr):,} ({len(X_cic_train):,} CICIDS2017 + {len(X_unsw_train):,} UNSW-NB15)")
    print(f"Validation samples: {len(X_val):,} ({len(X_cic_val):,} CICIDS2017 + {len(X_unsw_val):,} UNSW-NB15)")
    print(f"Test samples (CICIDS2017): {len(X_cic_test):,}")
    print(f"Test samples (UNSW-NB15): {len(X_unsw_test):,}")
    print(f"Features: {X_tr.shape[1]}")

    print(f"\nTraining {args.model}...")
    if args.model == 'quark':
        model = SimpleTrainer(args.model, 'cpu')
        model.reset_model(X_tr.shape[1])
        model.train(X_tr, Y_tr, verbose=True)
    elif args.model == 'netbeacon':
        model = RandomForestClassifier(n_estimators=2, random_state=42, max_depth=9)
        model.fit(X_tr, Y_tr)
    else:
        raise ValueError(f"Unsupported architecture: {args.model}")

    # Prepare evaluation batches with gradual distribution shift
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
    
    preds = []
    targets = []
    batches = []

    for i in range(N_BATCHES):
        batch_X = eval_batches_X[i]
        batch_Y = eval_batches_Y[i]
        targets.extend(batch_Y)
        batches.extend([i+1]*len(batch_Y))
    
        if args.model == 'quark':
            evals = model.eval_model(batch_X, batch_Y, verbose=False)['predictions']
        elif args.model == 'netbeacon':
            evals = model.predict(batch_X)

        preds.extend(evals)
        acc = (evals == batch_Y).sum() / len(batch_Y)
        
        unsw_pct = unsw_fractions[i] * 100
        print(f"Batch {i+1:2d} ({unsw_pct:.1f}% UNSW) - CNN: {acc:.3f} accuracy")

    os.makedirs(RES_DIR, exist_ok=True)

    teacher_results = {
        'batch': batches,
        'targets': targets,
        'predictions': preds,
    }
    pd.DataFrame(teacher_results).to_csv(f'{RES_DIR}/{args.model}_results.csv', index=False)

    with open(f'{RES_DIR}/config.json', 'w') as f:
        curr_config = {
            'MAX_UNSW_FRACTION': MAX_UNSW_FRACTION,
            'DATASET_SWITCH_START': DATASET_SWITCH_START,
            'DATASET_SWITCH_END':DATASET_SWITCH_END,
            'N_BATCHES': N_BATCHES,
            'BATCH_SIZE': BATCH_SIZE
        }
        import json
        json.dump(curr_config, f)

if __name__ == "__main__":
    main()
