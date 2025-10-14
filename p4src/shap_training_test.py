#!/usr/bin/env python3

import os
import sys
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from ml_helpers.trainer import Trainer

def load_base_models(arch, dataset, train_base=False):
    if train_base:
        print(f"Training base models for {arch} on {dataset}")
        # Create trainers without eval_only flag
        mlp_trainer = Trainer(model_name='mlp', dataset_name=dataset, arch=arch)
        bnn_trainer = Trainer(model_name='bnn', dataset_name=dataset, arch=arch)
        
        # Train the models
        print("Training MLP base model...")
        mlp_trainer.train_model()
        print("Training BNN base model...")
        bnn_trainer.train_model()
    else:
        print(f"Loading existing base models for {arch} on {dataset}")
        # Use eval_only=True to ensure base model weights exist - will break if not found
        mlp_trainer = Trainer(model_name='mlp', dataset_name=dataset, arch=arch, eval_only=True)
        bnn_trainer = Trainer(model_name='bnn', dataset_name=dataset, arch=arch, eval_only=True)
        
        # Run evaluation to add results to all_model_results.csv
        print("Running evaluation for base models to populate all_model_results.csv")
        mlp_trainer.eval_model()
        bnn_trainer.eval_model()
    
    return mlp_trainer, bnn_trainer

def get_shap_paths(trainer, model_type):
    expected_path = trainer.get_expected_shap_path()
    
    if not os.path.exists(expected_path):
        print(f"SHAP file not found: {expected_path}")
        print(f"Computing SHAP indices for {trainer.model_name}...")
        
        _ = trainer.compute_shap_indices(force_recompute=True)
        
        if not os.path.exists(expected_path):
            raise RuntimeError(f"Failed to compute SHAP indices for {trainer.model_name}")
            
        print(f"✅ SHAP computation completed: {expected_path}")
    
    return expected_path.replace(trainer.model_name, model_type)


def cross_validate_tf_models(arch, dataset, mlp_trainer, bnn_trainer):
    print(f'\n{"*" * 40}')
    print(f"Cross-validating TF models for {arch} on {dataset}")
    
    mlp_shap_path = get_shap_paths(mlp_trainer, 'mlp')
    bnn_shap_path = get_shap_paths(bnn_trainer, 'bnn')
    
    best_acc = -1
    best_model = None
    best_path = None
    
    # Train TF model from MLP SHAP
    print(f"Cross-validating tf_bnn_from_shap_mlp with {mlp_shap_path}")
    tf_mlp_trainer = Trainer(model_name='tf_bnn_from_shap_mlp', 
                            dataset_name=dataset, 
                            arch=arch, 
                            shap_indeces_path=mlp_shap_path)
    tf_mlp_trainer.train_model(cross_validate=True)
    tf_mlp_trainer.eval_model()  # Add evaluation to populate eval_results
    
    if hasattr(tf_mlp_trainer, 'eval_results') and 'accuracy' in tf_mlp_trainer.eval_results:
        mlp_acc = tf_mlp_trainer.eval_results['accuracy']
        if mlp_acc > best_acc:
            best_acc = mlp_acc
            best_model = 'tf_bnn_from_shap_mlp'
            best_path = mlp_shap_path
    
    # Train TF model from BNN SHAP
    print(f"Cross-validating tf_bnn_from_shap_bnn with {bnn_shap_path}")
    tf_bnn_trainer = Trainer(model_name='tf_bnn_from_shap_bnn', 
                            dataset_name=dataset, 
                            arch=arch, 
                            shap_indeces_path=bnn_shap_path)
    tf_bnn_trainer.train_model(cross_validate=True)
    tf_bnn_trainer.eval_model()  # Add evaluation to populate eval_results
    
    if hasattr(tf_bnn_trainer, 'eval_results') and 'accuracy' in tf_bnn_trainer.eval_results:
        bnn_acc = tf_bnn_trainer.eval_results['accuracy']
        if bnn_acc > best_acc:
            best_acc = bnn_acc
            best_model = 'tf_bnn_from_shap_bnn'
            best_path = bnn_shap_path
    
    return best_model, best_path, best_acc

def train_final_models(arch, dataset, best_model, best_path):
    print(f"Training final {best_model} for {arch} on {dataset}")
    
    final_trainer = Trainer(model_name=best_model, 
                           dataset_name=dataset, 
                           arch=arch, 
                           shap_indeces_path=best_path)
    final_trainer.train_model()
    
    return final_trainer

def create_comparison_plot(arch, dataset):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "results")
    all_results_file = os.path.join(results_dir, "all_model_results.csv")
    
    print(f"Reading evaluation metrics from {all_results_file}")
    
    if not os.path.exists(all_results_file):
        print(f"❌ All model results file not found: {all_results_file}")
        return
    
    # Read the CSV and filter by dataset
    df = pd.read_csv(all_results_file)
    dataset_results = df[df['dataset'] == dataset]
    
    if dataset_results.empty:
        print(f"❌ No results found for dataset {dataset} in all_model_results.csv")
        return
    
    print(f"Found {len(dataset_results)} results for dataset {dataset}")
    print(f"Available models: {dataset_results['model_name'].unique().tolist()}")
    
    # Define architecture mappings for base models and SHAP models
    arch_mappings = {
        'dense': {
            'base_arch': '168-42-2',     # MLP and BNN base models
            'shap_arch': '132-42-2'      # SHAP models with reduced features
        },
        'wide': {
            'base_arch': '168-32-8-2',   # MLP and BNN base models  
            'shap_arch': '128-32-8-2'    # SHAP models with reduced features
        },
        'tiny': {
            'base_arch': '168-21-2',     # MLP and BNN base models
            'shap_arch': '98-21-2'       # SHAP models with reduced features
        }
    }
    
    if arch not in arch_mappings:
        print(f"❌ Unknown architecture: {arch}")
        return
    
    base_arch = arch_mappings[arch]['base_arch']
    shap_arch = arch_mappings[arch]['shap_arch']
    
    models_data = []
    model_list = []
    
    # Get base models (MLP and BNN) with full feature set
    for model_name, display_name in [('mlp', 'MLP'), ('bnn', 'BNN')]:
        model_results = dataset_results[
            (dataset_results['model_name'] == model_name) & 
            (dataset_results['model_arch'] == base_arch)
        ]
        if not model_results.empty:
            result_row = model_results.iloc[-1]  # Most recent result
            models_data.append((display_name, result_row))
            model_list.append(model_name)
            print(f"✅ Found {display_name} base model ({base_arch}) - accuracy: {result_row['accuracy']:.4f}")
        else:
            print(f"❌ No results found for base model {model_name} with arch {base_arch}")
    
    # Get SHAP models with reduced feature set
    for model_name, display_name in [('tf_bnn_from_shap_mlp', 'TF_MLP_SHAP'), ('tf_bnn_from_shap_bnn', 'TF_BNN_SHAP')]:
        model_results = dataset_results[
            (dataset_results['model_name'] == model_name) & 
            (dataset_results['model_arch'] == shap_arch)
        ]
        if not model_results.empty:
            result_row = model_results.iloc[-1]  # Most recent result
            models_data.append((display_name, result_row))
            model_list.append(model_name)
            print(f"✅ Found {display_name} SHAP model ({shap_arch}) - accuracy: {result_row['accuracy']:.4f}")
        else:
            print(f"❌ No results found for SHAP model {model_name} with arch {shap_arch}")
    
    print(f"Found {len(models_data)} models for comparison: {[name for name, _ in models_data]}")
    
    if len(models_data) < 2:
        print(f"❌ Insufficient data for {arch} on {dataset} - need at least 2 models but found {len(models_data)}")
        return
    
    metrics = ['accuracy', 'precision', 'recall', 'f1_score']
    labels = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    
    plt.rcParams.update({
        'figure.facecolor': 'white',
        'figure.edgecolor': 'black',
        'axes.facecolor': 'white',
        'font.size': 22,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    })
    
    n_metrics = len(metrics)
    n_models = len(models_data)
    
    x = np.arange(n_metrics)
    group_width = 0.7
    bar_w = group_width / n_models
    
    # Increased figure size to accommodate legend
    fig, ax = plt.subplots(figsize=(12, 6))
    
    hatches = ['o', '//', 'o//', '...'][:n_models]  # Added 4th pattern for TF_BNN_SHAP
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:n_models]  # Distinct colors for each model
    
    for i, ((model_name, data), h, color) in enumerate(zip(models_data, hatches, colors)):
        means = [data[metric] for metric in metrics]
        ax.bar(
            x + (i - (n_models - 1) / 2) * (bar_w + 0.02),
            means,
            width=bar_w,
            capsize=5,
            label=model_name,
            hatch=h,
            color=color,
            alpha=0.8
        )
    
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(0.7)
    
    ax.margins(x=0.1, y=0.1)
    ax.set_ylim(0.4, 1.09)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    
    # Improved legend positioning - place it outside the plot area
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
    
    plt.tight_layout()
    
    plot_path = os.path.join(results_dir, f"comparison_{arch}_{dataset}.png")
    # Use bbox_inches='tight' to ensure legend is included in saved plot
    fig.savefig(plot_path, edgecolor='black', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Comparison plot saved: {plot_path}")

def run_experiment(arch, dataset, train_base=False):
    print(f"\n{'='*80}")
    print(f"EXPERIMENT: {arch.upper()} on {dataset}")
    print(f"{'='*80}")
    
    mlp_trainer, bnn_trainer = load_base_models(arch, dataset, train_base)
    
    best_model, best_path, best_acc = cross_validate_tf_models(arch, dataset, mlp_trainer, bnn_trainer)
    
    if best_model and best_path:
        print(f"Best model: {best_model} with accuracy: {best_acc:.4f}")
        # train_final_models(arch, dataset, best_model, best_path)
        print(f"✅ SUCCESS: {arch} | {dataset}")
        
        create_comparison_plot(arch, dataset)
    else:
        print(f"❌ FAILED: No valid SHAP paths found for {arch} on {dataset}")

def main():
    parser = argparse.ArgumentParser(description="Final Test Suite")
    parser.add_argument("--archs", nargs="+", default=["dense", "wide", "tiny"], 
                       choices=["dense", "wide", "tiny"], help="Architectures to test")
    parser.add_argument("--datasets", nargs="+", default=["UNSW-NB15-custom", 'CICIDS2017'], 
                       help="Datasets to test")
    parser.add_argument("--train-base", action="store_true", 
                       help="Train base models instead of loading existing ones")
    args = parser.parse_args()
    
    print("🧪 FINAL TEST SUITE")
    print(f"Architectures: {args.archs}")
    print(f"Datasets: {args.datasets}")
    print(f"Train base models: {args.train_base}")
    
    results = []
    
    for arch in args.archs:
        for dataset in args.datasets:
            try:
                run_experiment(arch, dataset, args.train_base)
                results.append(f"✅ {arch}-{dataset}")
            except Exception as e:
                import traceback
                print(f"❌ FAILED: {arch}-{dataset} - {str(e)}")
                print(f"Full traceback:")
                traceback.print_exc()
                results.append(f"❌ {arch}-{dataset}")
                continue
    
    print(f"\n{'='*80}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*80}")
    for result in results:
        print(result)
    
    success_count = len([r for r in results if r.startswith("✅")])
    total_count = len(results)
    print(f"🎯 SUCCESS RATE: {success_count}/{total_count} ({100*success_count/total_count:.1f}%)")

if __name__ == '__main__':
    main()