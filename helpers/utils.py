from configparser import ConfigParser
import os
from pathlib import Path
import warnings
import numpy as np
import matplotlib.pyplot as plt
import json
import pandas as pd
from scipy.stats import norm
from matplotlib.patches import Patch 
import sklearn.metrics as metrics

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

def load_models_results(dir):
    shap_res = pd.read_csv(f'{dir}/bnn_shap_results.csv')
    rand_res = pd.read_csv(f'{dir}/bnn_random_results.csv')
    teacher_res = pd.read_csv(f'{dir}/mlp_results.csv')
    shap_no_conf_res = pd.read_csv(f'{dir}/bnn_shap_no_conf_results.csv')
    return shap_res, rand_res, teacher_res, shap_no_conf_res

def load_config(dir):
    config_path = os.path.join(dir, 'config.json')
    if os.path.isfile(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        raise FileNotFoundError(f"Config file not found in {dir}")
    return config

def plot_distribution_shift_bnn(dir, filename, enable_bnn_random_plot=False, enable_bnn_no_conf_plot=False):
    config = load_config(dir)
    shap_res, rand_res, teacher_res, shap_no_conf_res = load_models_results(dir)

    shap_accuracies = (shap_res['predictions'] == shap_res['targets']).groupby(shap_res['batch']).mean().to_list()
    rand_accuracies = (rand_res['predictions'] == rand_res['targets']).groupby(rand_res['batch']).mean().to_list()
    teacher_accuracies = (teacher_res['predictions'] == teacher_res['targets']).groupby(teacher_res['batch']).mean().to_list()
    shap_accuracies_no_conf = (shap_no_conf_res['predictions'] == shap_no_conf_res['targets']).groupby(shap_no_conf_res['batch']).mean().to_list()

    MAX_UNSW_FRACTION = config['MAX_UNSW_FRACTION']
    DATASET_SWITCH_START = config['DATASET_SWITCH_START']
    N_BATCHES = config['N_BATCHES']
    RETRAIN_BATCH = config['RETRAIN_BATCH']
    ENABLE_RANDOM_BNN = enable_bnn_random_plot
    ENABLE_NO_CONF_BNN = enable_bnn_no_conf_plot

    shap_accuracies = pd.read_csv(f'{dir}/bnn_shap_results.csv')
    shap_accuracies = (shap_accuracies['predictions'] == shap_accuracies['targets']).groupby(shap_accuracies['batch']).mean().to_list()
    
    rand_accuracies = pd.read_csv(f'{dir}/bnn_random_results.csv')
    if ENABLE_RANDOM_BNN:
        rand_accuracies = (rand_accuracies['predictions'] == rand_accuracies['targets']).groupby(rand_accuracies['batch']).mean().to_list()
    
    teacher_accuracies = pd.read_csv(f'{dir}/mlp_results.csv')
    teacher_accuracies = (teacher_accuracies['predictions'] == teacher_accuracies['targets']).groupby(teacher_accuracies['batch']).mean().to_list()

    shap_accuracies_no_conf = pd.read_csv(f'{dir}/bnn_shap_no_conf_results.csv')
    if ENABLE_NO_CONF_BNN:
        shap_accuracies_no_conf = (shap_accuracies_no_conf['predictions'] == shap_accuracies_no_conf['targets']).groupby(shap_accuracies_no_conf['batch']).mean().to_list()

    # Apply rolling average of last 5 batches for smoother plotting
    window_size = 10
    smoothed_rand_accuracies = []
    smoothed_shap_accuracies = []
    smoothed_teacher_accuracies = []
    smoothed_shap_accuracies_no_conf = []
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
        if ENABLE_NO_CONF_BNN:
            avg_shap_acc_no_conf = np.mean(shap_accuracies_no_conf[start_idx:end_idx])

        smoothed_shap_accuracies.append(avg_shap_acc)
        smoothed_teacher_accuracies.append(avg_teacher_acc)
        if ENABLE_NO_CONF_BNN:
            smoothed_shap_accuracies_no_conf.append(avg_shap_acc_no_conf)

        batch_nums.append(i + 1)
    
    plt.rcParams.update({
        'font.size': 26,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    })
    
    # Single-axis plot: BNN and MLP accuracies, vertical line at first mixed batch
    fig, ax = plt.subplots(figsize=(9, 6))
    if ENABLE_RANDOM_BNN:
        ax.plot(batch_nums, smoothed_rand_accuracies, '--', linewidth=2, markersize=6, label='BNN random', color='C0')
    ax.plot(batch_nums, smoothed_shap_accuracies, '-', linewidth=3, markersize=6, label='BNN shap' , color='C1')
    ax.plot(batch_nums, smoothed_teacher_accuracies, '-', linewidth=3, markersize=6, label='MLP', color='C2')
    if ENABLE_NO_CONF_BNN:
        ax.plot(batch_nums, smoothed_shap_accuracies_no_conf, '-', linewidth=3, markersize=6, label='BNN no conf', color='C3')
    ax.set_xlabel('Batch Number')
    ax.set_ylabel('Accuracy')
    ax.set_ylim(0.65, 1)
    ax.grid(False)

    # Vertical line at first mixed batch (1-based index)
    first_mixed_batch = DATASET_SWITCH_START + 1
    # ax.axvline(x=first_mixed_batch, color='orange', linestyle=':', alpha=0.7, linewidth=3, label='Domain Shift')
    ax.axvline(x=first_mixed_batch, color='orange', linestyle=':', alpha=0.7, linewidth=3)

    
    # Add retraining line
    if(RETRAIN_BATCH > 0):
        ax.axvline(x=RETRAIN_BATCH, color='red', linestyle=':', alpha=0.7, linewidth=3)

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

    ax.legend(loc='lower left', fontsize=26, ncol=2)
    plt.tight_layout()
    
    out_path = f'{dir}/bnn_gradual_shift_eval_to_{MAX_UNSW_FRACTION:.2f}_{filename}.png'
    plt.savefig(out_path, dpi=300, bbox_inches='tight')

    print(f"\nPlot saved to {out_path}")


def plot_training_accuracies(dir, filename, out):
    """
    Plot training accuracy per epoch with a rolling average (window=6).

    Args:
        accuracies (list or array-like): list of accuracy values, one per epoch.
    """
    accuracies = pd.read_csv(f'{dir}/{filename}')['batch_accuracies'].tolist()

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
    confidence_plot_path = f'{dir}/{out}_bnn_training_accuracies.png'
    plt.savefig(confidence_plot_path, dpi=300, bbox_inches='tight', edgecolor='black')
    plt.close()


def plot_confidence_scores(dir):
    
    unique_confs = pd.read_csv(f'{dir}/unique_confidences.csv')['confidence'].tolist()
    weighted_values_to_plot = pd.read_csv(f'{dir}/weighted_values.csv')['weighted_value'].tolist()
    weighted_prob = pd.read_csv(f'{dir}/weighted_probabilities.csv')['weighted_prob'].tolist()
    confident_scores = pd.read_csv(f'{dir}/confident_scores.csv')['confident_score'].tolist()

    # Create plot matching trainer.py style exactly
    plt.rcParams.update({
        'font.size': 30,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    })
    
    fig, ax1 = plt.subplots(figsize=(8, 5))
    
    # Primary y-axis: Weighted accuracy bars (accuracy × percentage)
    bars = ax1.bar(unique_confs, weighted_values_to_plot, width=0.9, alpha=0.7, 
                  color='green', edgecolor='black')
    plt.xticks(np.arange(min(unique_confs), max(unique_confs)+1, 3))

    # Add hatches to confident score bars
    for i, prob in enumerate(weighted_prob):
        if prob in confident_scores:
            bars[i].set_hatch('ooo')
    
    # ax1.set_xlabel('Confidence Score')
    ax1.set_xlabel('Active neurons')
    # ax1.set_ylabel('P(Correct|Confidence) × Sample %', color='black')
    ax1.set_ylabel('Confidence', color='black')

    max_weighted = max(weighted_values_to_plot) if len(weighted_values_to_plot) > 0 else 1
    max_confs = max(unique_confs)

    ax1.set_ylim([0, max_weighted * 1.1])
    ax1.set_xlim([0, max_confs-1])
    ax1.tick_params(axis='y', labelcolor='black')
    
    # --- ADDED LEGEND FOR HATCHED BARS ---
    # We create a manual patch to represent the hatched style in the legend
    legend_elements = [
        Patch(facecolor='green', edgecolor='black', alpha=0.85, 
              hatch='ooo', label='Confident Act')
    ]
    # Place legend (you can adjust loc='upper right' or 'upper left')
    ax1.legend(handles=legend_elements, loc='lower left', fontsize=27)
    # -------------------------------------

    # Style the plot borders
    for spine in ax1.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(0.7)
    
    plt.tight_layout()
    confidence_plot_path = f'{dir}/bnn_gradual_shift_confidence.png'
    plt.savefig(confidence_plot_path, dpi=300, bbox_inches='tight', edgecolor='black')
    plt.close()
    
    print(f"Confidence plot saved to {confidence_plot_path}")


def plot_retraining_comparison_bars(directory, filename):
    
    """
    Reads accuracy CSVs, splits data based on RETRAIN_BATCH, and plots
    a grouped bar chart.
    
    Style: 
    - Bars for the same model share the same base color.
    - Pre-Retrain: Lighter alpha + Hatched pattern.
    - Post-Retrain: Solid color.
    """
    
    # 1. Load Configuration
    config = load_config(directory)
    shap_res, rand_res, teacher_res, shap_no_conf_res = load_models_results(directory)

    RETRAIN_BATCH = config.get('RETRAIN_BATCH', 0)
    DATASET_SWITCH_END = config.get('DATASET_SWITCH_END', 0)
    
    split_index_end = max(0, RETRAIN_BATCH - 1)
    split_index_start = max(0, DATASET_SWITCH_END - 1)

    # 2. Load Data
    models_data = []

    # -- Teacher / MLP
    try:
        mlp_acc = (teacher_res['predictions'] == teacher_res['targets']).groupby(teacher_res['batch']).mean().to_list()
        models_data.append({'name': 'MLP', 'data': mlp_acc})
    except FileNotFoundError:
        print("Warning: mlp_accuracies.csv not found.")

    # -- BNN SHAP
    try:
        shap_acc = (shap_res['predictions'] == shap_res['targets']).groupby(shap_res['batch']).mean().to_list()
        models_data.append({'name': 'SHAP', 'data': shap_acc})
    except FileNotFoundError:
        print("Warning: bnn_shap_accuracies.csv not found.")

    # -- BNN Random
    try:
        rand_acc = (rand_res['predictions'] == rand_res['targets']).groupby(rand_res['batch']).mean().to_list()
        models_data.append({'name': 'RND', 'data': rand_acc})
    except FileNotFoundError:
        pass # Silent fail if disabled

    # -- BNN No Conf
    try:
        no_conf_acc = (shap_no_conf_res['predictions'] == shap_no_conf_res['targets']).groupby(shap_no_conf_res['batch']).mean().to_list()
        models_data.append({'name': 'No Conf', 'data': no_conf_acc})
    except FileNotFoundError:
        pass # Silent fail if disabled

    # 3. Calculate Stats
    labels = []
    means_before = []
    stds_before = []
    means_after = []
    stds_after = []

    for model in models_data:
        data = model['data']
        name = model['name']
        
        data_before = data[split_index_start:split_index_end]
        data_after = data[split_index_end:]

        if not data_before:
            mean_b, std_b = 0, 0
        else:
            mean_b, std_b = np.mean(data_before), np.std(data_before)

        if not data_after:
            mean_a, std_a = 0, 0
        else:
            mean_a, std_a = np.mean(data_after), np.std(data_after)

        labels.append(name)
        means_before.append(mean_b)
        stds_before.append(std_b)
        means_after.append(mean_a)
        stds_after.append(std_a)

    # 4. Plotting
    plt.rcParams.update({
        'font.size': 30,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    })
    
    fig, ax = plt.subplots(figsize=(8, 5))

    x = np.arange(len(labels))
    width = 0.4

    # --- DEFINE COLORS ---
    # Distinct colors for each model (Blue, Orange, Green, Red)
    # You can add more colors to this list if you have more than 4 models
    base_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    # Slice the color list to match the number of models we actually found
    model_colors = base_colors[:len(labels)]

    # --- PLOT BARS ---
    
    # 1. Pre-Retrain Bars (Left)
    # Style: Lower Alpha (lighter), Hatched pattern
    rects1 = ax.bar(x - width/2, means_before, width, 
                    yerr=stds_before, capsize=5, 
                    color=model_colors,      # Color by Model
                    alpha=0.6,               # Lighter transparency
                    hatch='///',             # Diagonal hatch
                    edgecolor='black',       # Sharp borders
                    # linewidth=1.5
                    )
    
    # 2. Post-Retrain Bars (Right)
    # Style: Full Alpha (darker/vibrant), No hatch
    rects2 = ax.bar(x + width/2, means_after, width, 
                    yerr=stds_after, capsize=5, 
                    color=model_colors,      # Color by Model
                    alpha=1.0,               # Full color
                    hatch='',                # Solid
                    edgecolor='black',       # Sharp borders
                    # linewidth=1.5
                    )

    # --- AESTHETICS ---
    ax.set_ylabel('Accuracy')
    ax.set_xlabel('Models')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0.55, 1.02) # Adjusted upper limit slightly for error bars
    
    # Grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, zorder=0)
    ax.set_axisbelow(True) # Puts grid behind bars

    # --- CUSTOM LEGEND ---
    # Since bars are multicolored, we create a neutral legend to explain the pattern
    legend_elements = [
        Patch(facecolor='white', edgecolor='black', hatch='///', label='Pre-Retrain'),
        Patch(facecolor='gray', edgecolor='black', label='Post-Retrain')
    ]
    
    ax.legend(handles=legend_elements, fontsize=28, loc='lower left')

    plt.tight_layout()

    save_path = os.path.join(directory, f'bnn_gradual_{filename}.png')
    plt.savefig(save_path)
    print(f"Plot saved to {save_path}")
    # plt.show()

def basic_stats(dir):
    config= load_config(dir)
    shap_res, rand_res, teacher_res, shap_no_conf_res = load_models_results(dir)

    shap_accuracies = (shap_res['predictions'] == shap_res['targets']).groupby(shap_res['batch']).mean().to_list()
    rand_accuracies = (rand_res['predictions'] == rand_res['targets']).groupby(rand_res['batch']).mean().to_list()
    teacher_accuracies = (teacher_res['predictions'] == teacher_res['targets']).groupby(teacher_res['batch']).mean().to_list()
    shap_accuracies_no_conf = (shap_no_conf_res['predictions'] == shap_no_conf_res['targets']).groupby(shap_no_conf_res['batch']).mean().to_list()

    RETRAIN_BATCH = config.get('RETRAIN_BATCH', 0)-1
    DATASET_SWITCH_END = config.get('DATASET_SWITCH_END', 0)-1
    DATASET_SWITCH_START = config.get('DATASET_SWITCH_START', 0)-1

    acc_list = {
        'teacher_accuracies':teacher_accuracies,
        'shap_accuracies': shap_accuracies,
        'shap_accuracies_no_conf': shap_accuracies_no_conf,
        'rand_accuracies': rand_accuracies
    }

    print()
    print(f'********* STATS *********')
    for acc_name,acc in acc_list.items():
        print(f'{acc_name}:')
        print(f'\tmean pre-distribution shift: {np.mean(acc[:DATASET_SWITCH_START])}')
        print(f'\tmean post-distribution shift pre-retraining: {np.mean(acc[DATASET_SWITCH_END:RETRAIN_BATCH])}')
        print(f'\tmean post-distribution shift post-retraining: {np.mean(acc[RETRAIN_BATCH:])}')
        print(f'\tmax  pre-retraining: {np.max(acc[DATASET_SWITCH_END:RETRAIN_BATCH])}')
        print(f'\tmax  post-retraining: {np.max(acc[RETRAIN_BATCH:])}')
        print()

