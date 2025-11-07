#!/usr/bin/env python3
"""
Standalone Model Comparison Plotter

This script reads all_model_results.csv and generates comparison plots 
for all available architecture-dataset combinations.

Usage:
    python plot_model_comparison.py
    python plot_model_comparison.py --arch dense --dataset CICIDS2017
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
from collections import defaultdict

def create_comparison_plot(arch, dataset):
    """Create comparison plot for a specific architecture and dataset"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "results")
    all_results_file = os.path.join(results_dir, "all_model_results.csv")
    
    print(f"Reading evaluation metrics from {all_results_file}")
    
    if not os.path.exists(all_results_file):
        print(f"❌ All model results file not found: {all_results_file}")
        return False
    
    # Read the CSV and filter by dataset
    df = pd.read_csv(all_results_file)
    dataset_results = df[df['dataset'] == dataset]
    
    if dataset_results.empty:
        print(f"❌ No results found for dataset {dataset} in all_model_results.csv")
        return False
    
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
        return False
    
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
        return False
    
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
    print(f"✅ Comparison plot saved: {plot_path}")
    return True

def discover_available_combinations():
    """Discover all available architecture-dataset combinations from all_model_results.csv"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "results")
    all_results_file = os.path.join(results_dir, "all_model_results.csv")
    
    if not os.path.exists(all_results_file):
        print(f"❌ All model results file not found: {all_results_file}")
        return []
    
    df = pd.read_csv(all_results_file)
    
    # Define which architectures correspond to which logical names
    arch_reverse_mapping = {
        '168-42-2': 'dense',    # Base models
        '132-42-2': 'dense',    # SHAP models
        '168-32-8-2': 'wide',   # Base models  
        '128-32-8-2': 'wide',   # SHAP models
        '168-21-2': 'tiny',     # Base models
        '98-21-2': 'tiny'       # SHAP models
    }
    
    # Find combinations that have both base and SHAP models
    combinations = set()
    datasets = df['dataset'].unique()
    
    for dataset in datasets:
        dataset_df = df[df['dataset'] == dataset]
        
        # Check each logical architecture
        for logical_arch in ['dense', 'wide', 'tiny']:
            # Check if we have both base models and SHAP models for this logical architecture
            has_base = False
            has_shap = False
            
            for _, row in dataset_df.iterrows():
                model_arch = row['model_arch']
                if model_arch in arch_reverse_mapping:
                    mapped_arch = arch_reverse_mapping[model_arch]
                    if mapped_arch == logical_arch:
                        if row['model_name'] in ['mlp', 'bnn']:
                            has_base = True
                        elif row['model_name'] in ['tf_bnn_from_shap_mlp', 'tf_bnn_from_shap_bnn']:
                            has_shap = True
            
            # Only add combination if we have both base and SHAP models
            if has_base and has_shap:
                combinations.add((logical_arch, dataset))
    
    return list(combinations)

def main():
    parser = argparse.ArgumentParser(description='Generate model comparison plots from all_model_results.csv')
    parser.add_argument('--arch', type=str, help='Specific architecture to plot (dense, wide, tiny)')
    parser.add_argument('--dataset', type=str, help='Specific dataset to plot (CICIDS2017, UNSW-NB15-custom)')
    parser.add_argument('--list', action='store_true', help='List all available combinations')
    
    args = parser.parse_args()
    
    print("🎨 MODEL COMPARISON PLOTTER")
    print("="*50)
    
    # Discover available combinations
    combinations = discover_available_combinations()
    
    if not combinations:
        print("❌ No data found in all_model_results.csv")
        return
    
    if args.list:
        print("Available architecture-dataset combinations:")
        for arch, dataset in sorted(combinations):
            print(f"  - {arch} on {dataset}")
        return
    
    # Filter combinations based on arguments
    if args.arch or args.dataset:
        filtered_combinations = []
        for arch, dataset in combinations:
            if args.arch and arch != args.arch:
                continue
            if args.dataset and dataset != args.dataset:
                continue
            filtered_combinations.append((arch, dataset))
        combinations = filtered_combinations
    
    if not combinations:
        print(f"❌ No combinations found for arch={args.arch}, dataset={args.dataset}")
        return
    
    # Remove duplicates and plot
    unique_combinations = list(set(combinations))
    print(f"Generating plots for {len(unique_combinations)} combinations:")
    
    success_count = 0
    for arch, dataset in sorted(unique_combinations):
        print(f"\n📊 Plotting {arch} on {dataset}")
        if create_comparison_plot(arch, dataset):
            success_count += 1
    
    print(f"\n✅ Successfully generated {success_count}/{len(unique_combinations)} plots")
    print("📁 Plots saved in results/ directory")

if __name__ == "__main__":
    main()