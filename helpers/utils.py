from configparser import ConfigParser
import os
from pathlib import Path
import warnings
import numpy as np
import matplotlib.pyplot as plt
import json
import pandas as pd
from scipy.stats import norm
import torch

def suppress_warnings():
    # Suppress brevitas Warning
    warnings.filterwarnings(
        "ignore",
        message="Defining your `__torch_function__` as a plain method is deprecated",
        category=UserWarning,
    )

def generate_14bit():
    """
    Yields (binary14, hex4, popcount_int) for all 14-bit values 0..(2^14-1).
    """
    for i in range(1 << 14):                            # 0..16383
        bin_str = format(i, '014b')                     # 14-bit binary with leading zeros
        hex_str = format(i, '04X')                      # 4-digit uppercase hex (up to 3FFF)
        popcnt  = format(bin(i).count('1'), '01X')      # integer popcount
        yield bin_str, hex_str, popcnt

def generate_16bit_hex():
    """
    Yields (binary16, hex4, popcount_hex1) for all values 1..(2^16-2).
    """
    for i in range(1, (1 << 16) - 1):
        bin_str = format(i, '016b')    # 16-bit binary
        hex_str = format(i, '04X')     # 4-digit uppercase hex
        popcnt  = format(bin(i).count('1'), '01X')
        yield bin_str, hex_str, popcnt

def hex_lists_to_ints(*hex_lists):
    return [[int(h, 16) for h in lst] for lst in hex_lists]

def get_cfg(name='cicisds2017'):
    cfg = ConfigParser()
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join('configs', name.lower() + '.ini')
    assert os.path.exists(config_path), f"{config_path} not found."
    cfg.read(config_path)
    
    return cfg

def none_or_str(value):
    if value == "None":
        return None
    return value

def none_or_int(value):
    if value == "None":
        return None
    return int(value)

def get_file_from_keyword(directory, keyword):
    path = Path(directory)
    for file in path.iterdir():
        if file.is_file() and keyword in file.name:
            return file
    return None

def plot_distribution_shift_bnn(dir):
    if os.path.isfile(f'{dir}/config.json'):
        with open(f'{dir}/config.json', 'r') as f:
            config = json.load(f)

    MAX_UNSW_FRACTION = config['MAX_UNSW_FRACTION']
    DATASET_SWITCH_START = config['DATASET_SWITCH_START']
    N_BATCHES = config['N_BATCHES']
    RETRAIN_BATCH = config['RETRAIN_BATCH']
    ENABLE_RANDOM_BNN = config['ENABLE_RANDOM_BNN']

    rand_accuracies = pd.read_csv(f'{dir}/bnn_random_accuracies.csv')['accuracy'].tolist() if ENABLE_RANDOM_BNN else []
    shap_accuracies = pd.read_csv(f'{dir}/bnn_shap_accuracies.csv')['accuracy'].tolist()
    teacher_accuracies = pd.read_csv(f'{dir}/mlp_accuracies.csv')['accuracy'].tolist()

    # Apply rolling average of last 5 batches for smoother plotting
    window_size = 10
    smoothed_rand_accuracies = []
    smoothed_shap_accuracies = []
    smoothed_teacher_accuracies = []
    batch_nums = []
    
    for i in range(N_BATCHES):
        start_idx = max(0, i - window_size + 1)
        end_idx = i + 1
        
        # Calculate rolling average
        if ENABLE_RANDOM_BNN:
            avg_rand_acc = np.mean(rand_accuracies[start_idx:end_idx])
            smoothed_rand_accuracies.append(avg_rand_acc)
        
        avg_shap_acc = np.mean(shap_accuracies[start_idx:end_idx])
        avg_teacher_acc = np.mean(teacher_accuracies[start_idx:end_idx])

        smoothed_shap_accuracies.append(avg_shap_acc)
        smoothed_teacher_accuracies.append(avg_teacher_acc)
        batch_nums.append(i + 1)
    
    plt.rcParams.update({
        'font.size': 34,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    })
    
    # Single-axis plot: BNN and MLP accuracies, vertical line at first mixed batch
    fig, ax = plt.subplots(figsize=(14, 8))
    if ENABLE_RANDOM_BNN:
        ax.plot(batch_nums, smoothed_rand_accuracies, '--', linewidth=2, markersize=6, label='BNN random')
    ax.plot(batch_nums, smoothed_shap_accuracies, '-', linewidth=3, markersize=6, label='BNN shap')
    ax.plot(batch_nums, smoothed_teacher_accuracies, '-', linewidth=3, markersize=6, label='MLP')
    ax.set_xlabel('Batch Number')
    ax.set_ylabel('Accuracy')
    ax.set_ylim(0.65, 1)
    ax.grid(False)

    # Vertical line at first mixed batch (1-based index)
    first_mixed_batch = DATASET_SWITCH_START + 1
    ax.axvline(x=first_mixed_batch, color='orange', linestyle=':', alpha=0.7, linewidth=3, label='Distribution Shift')
    
    # Add retraining line
    if(RETRAIN_BATCH > 0):
        ax.axvline(x=RETRAIN_BATCH, color='red', linestyle=':', alpha=0.7, linewidth=3, label='SHAP Retraining')

    # Calculate accuracy gaps and add bidirectional arrows
    if ENABLE_RANDOM_BNN and RETRAIN_BATCH > 0:
        # Gap after retraining (from retraining to end)
        if RETRAIN_BATCH < len(smoothed_rand_accuracies):
            post_gap_rand = np.mean(smoothed_rand_accuracies[RETRAIN_BATCH:])
            post_gap_shap = np.mean(smoothed_shap_accuracies[RETRAIN_BATCH:])
            post_gap = abs(post_gap_rand - post_gap_shap)
            
            # Arrow after retraining
            mid_batch_post = (RETRAIN_BATCH + len(smoothed_rand_accuracies)) / 2
            y_pos_post = (post_gap_rand + post_gap_shap) / 2
            ax.annotate('', xy=(mid_batch_post, post_gap_rand), xytext=(mid_batch_post, post_gap_shap),
                       arrowprops=dict(arrowstyle='<->', lw=2))
            ax.text(mid_batch_post + 5, y_pos_post, f'{post_gap*100:.1f}%', fontsize=30)

    ax.legend(loc='lower left', fontsize=30, ncol=2)
    plt.tight_layout()
    
    out_path = f'{dir}/bnn_gradual_shift_eval_to_{MAX_UNSW_FRACTION:.2f}.png'
    plt.savefig(out_path, dpi=300, bbox_inches='tight')

    print(f"\nPlot saved to {out_path}")


def plot_training_accuracies(dir):
    """
    Plot training accuracy per epoch with a rolling average (window=6).

    Args:
        accuracies (list or array-like): list of accuracy values, one per epoch.
    """
    accuracies = pd.read_csv(f'{dir}/bnn_shap_train_accuracies.csv')['batch_accuracies'].tolist()

    if accuracies is None or len(accuracies) == 0:
        print("No accuracies to plot.")
        return

    # Convert to pandas Series for easy rolling average
    acc_series = pd.Series(accuracies)
    rolling_avg = acc_series.rolling(window=1, min_periods=1).mean()

    epochs = np.arange(1, len(accuracies) + 1)

    # Plot styling consistent with other plotting helpers
    plt.rcParams.update({
        'font.size': 34,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    })

    fig, ax = plt.subplots(figsize=(14, 8))

    # Raw accuracies (light) and rolling average (prominent)
    ax.plot(epochs, accuracies, '-', color='gray', linewidth=1.0, alpha=0.45, marker='o', markersize=6, label='Epoch accuracy')
    ax.plot(epochs, rolling_avg.values, '-', color='tab:blue', linewidth=3, markersize=6, label='Rolling avg (6)')

    ax.set_xlabel('Epoch')
    ax.set_ylabel('Accuracy')
    ax.set_ylim(0.0, 1.0)
    ax.grid(False)

    # Annotate final values for convenience
    final_acc = accuracies[-1]
    final_avg = rolling_avg.values[-1]
    ax.text(epochs[-1], final_avg, f" {final_avg:.3f}", fontsize=26, va='center')

    ax.legend(loc='lower right', fontsize=26)
    plt.tight_layout()
    confidence_plot_path = f'{dir}/bnn_gradual_training.png'
    plt.savefig(confidence_plot_path, dpi=300, bbox_inches='tight', edgecolor='black')
    plt.close()

def plot_confidence_scores(dir):
    if os.path.isfile(f'{dir}/config.json'):
        with open(f'{dir}/config.json', 'r') as f:
            config = json.load(f)
    
    unique_confs = pd.read_csv(f'{dir}/unique_confidences.csv')['confidence'].tolist()
    weighted_values_to_plot = pd.read_csv(f'{dir}/weighted_values.csv')['weighted_value'].tolist()
    confidence_counts_df = pd.read_csv(f'{dir}/confidence_counts.csv')
    confidence_counts = dict(zip(confidence_counts_df['confidence'], confidence_counts_df['count']))
    weighted_prob = pd.read_csv(f'{dir}/weighted_probabilities.csv')['weighted_prob'].tolist()
    confident_scores = pd.read_csv(f'{dir}/confident_scores.csv')['confident_score'].tolist()

    # Create plot matching trainer.py style exactly
    plt.rcParams.update({
        'font.size': 30,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    })
    
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # Primary y-axis: Weighted accuracy bars (accuracy × percentage)
    bars = ax1.bar(unique_confs, weighted_values_to_plot, width=0.6, alpha=0.7, 
                  color='green', edgecolor='black', capsize=5)
    
    # Add hatches to confident score bars
    for i, prob in enumerate(weighted_prob):
        if prob in confident_scores:
            bars[i].set_hatch('ooo')
    
    ax1.set_xlabel('Confidence Score')
    ax1.set_ylabel('P(Correct|Confidence) × Sample %', color='black')
    max_weighted = max(weighted_values_to_plot) if len(weighted_values_to_plot) > 0 else 1
    ax1.set_ylim([0, max_weighted * 1.2])
    ax1.tick_params(axis='y', labelcolor='black')
    
    # Fit Gaussian model to confidence scores
    confidence_data_for_fitting = []
    for conf, count in confidence_counts.items():
        confidence_data_for_fitting.extend([conf] * count)
    
    if len(confidence_data_for_fitting) > 0:
        # Fit Gaussian distribution
        mu, sigma = norm.fit(confidence_data_for_fitting)
        
        # Create smooth curve for overlay
        x_smooth = np.linspace(min(unique_confs), max(unique_confs), 200)
        gaussian_curve = norm.pdf(x_smooth, mu, sigma)
        
        # Scale Gaussian curve to match the weighted values scale
        scale_factor = max_weighted * 0.8  # Scale to 80% of max for visibility
        gaussian_curve_scaled = gaussian_curve * scale_factor / max(gaussian_curve)
        
        # Plot Gaussian curve overlay
        ax1.plot(x_smooth, gaussian_curve_scaled, 'b-', linewidth=3, 
                label='Gaussian Fit', alpha=0.8)
        
        # Add legend
        ax1.legend(loc='upper right')
        
        print(f'Gaussian fit: μ = {mu:.4f}, σ = {sigma:.4f}')
    
    # Style the plot borders
    for spine in ax1.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(0.7)
    
    plt.tight_layout()
    confidence_plot_path = f'{dir}/bnn_gradual_shift_confidence.png'
    plt.savefig(confidence_plot_path, dpi=300, bbox_inches='tight', edgecolor='black')
    plt.close()
    
    print(f"Confidence plot saved: {confidence_plot_path}")