from configparser import ConfigParser
import os
from pathlib import Path
import warnings
import numpy as np
import matplotlib.pyplot as plt
import json
import pandas as pd
from matplotlib.patches import Patch
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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

def get_cfg(config_file):
    cfg = ConfigParser()
    config_path = os.path.join('configs', config_file.lower() + '.ini')
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

def load_dataset(dataset_name, model='binocular'):
    """Load dataset directly"""
    dataset_cfg = get_cfg(dataset_name)
    dataset_path = dataset_cfg.get('DATASET', f'{model.upper()}_PATH')
    
    if os.path.exists(dataset_path):
        data = pd.read_csv(dataset_path)
        X = data.iloc[:, :-1].values
        Y = data.iloc[:, -1].values
        return X, Y

    raise FileNotFoundError(f"Dataset {dataset_name} for model {model} not found")

def load_models_results(dir, model):
    shap_res = pd.read_csv(f'{dir}/{model}_results.csv')
    rand_res = pd.read_csv(f'{dir}/{model}_random_results.csv')
    teacher_res = pd.read_csv(f'{dir}/teacher_results.csv')
    shap_no_conf_res = pd.read_csv(f'{dir}/{model}_no_conf_results.csv')
    return shap_res, rand_res, teacher_res, shap_no_conf_res

def load_config(dir):
    config_path = os.path.join(dir, 'config.json')
    if os.path.isfile(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        raise FileNotFoundError(f"Config file not found in {dir}")
    return config

def plot_distribution_shift_bnn(dir, model, filename=None, enable_bnn_random_plot=False, enable_bnn_no_conf_plot=False, rolling_window=10):
    model_results_dir = f'{dir}/simple_cross_dataset_eval_{model}'
    
    config = load_config(model_results_dir)
    MAX_UNSW_FRACTION = config['MAX_UNSW_FRACTION']
    DATASET_SWITCH_START = config['DATASET_SWITCH_START']
    N_BATCHES = config['N_BATCHES']
    RETRAIN_BATCH = config['RETRAIN_BATCH']
    ENABLE_RANDOM_BNN = enable_bnn_random_plot
    ENABLE_NO_CONF_BNN = enable_bnn_no_conf_plot

    plt.rcParams.update({
        'font.size': 26,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    })
    fig, ax = plt.subplots(figsize=(9, 6))

    color_no=0
    model_results = {
        f'{model_results_dir}/{model}_random_results.csv': 'BNN rand',
        f'{model_results_dir}/{model}_results.csv': 'BNN shap',
        f'{model_results_dir}/teacher_results.csv': 'Teacher',
        f'{model_results_dir}/{model}_no_conf_results.csv': 'BNN no conf'
    }
    for model_result_path, label in model_results.items():
        if not os.path.isfile(model_result_path):
            raise FileNotFoundError(f"Required results file {model_result_path} not found.")
        if 'rand' in model_result_path and not ENABLE_RANDOM_BNN:
            continue
        if 'no_conf' in model_result_path and not ENABLE_NO_CONF_BNN:
            continue

        model_res= pd.read_csv(model_result_path)
        model_metric = (model_res['predictions'] == model_res['targets']).groupby(model_res['batch']).mean().to_list()

        # Apply rolling average of last 5 batches for smoother plotting
        rolling_window = 10
        model_acc_smooth = []
        batch_nums = []
        
        for i in range(N_BATCHES):
            start_idx = max(0, i - rolling_window + 1)
            end_idx = i + 1
            model_acc_avg = np.mean(model_metric[start_idx:end_idx])
            model_acc_smooth.append(model_acc_avg)
            batch_nums.append(i + 1)

        ax.plot(batch_nums, model_acc_smooth, '--' if 'rand' in model_result_path else '-', linewidth=2, markersize=6, label=label, color=f'C{color_no}')
        color_no+=1

    if filename is not None:
        out_path = f'{model_results_dir}/{filename}_ablation.pdf'
    else:
        out_path = f'{model_results_dir}/{model}_ds_test_ablation.pdf'
    ax.set_xlabel('Batch Number')
    ax.set_ylabel('Accuracy')
    ax.set_ylim(0.65, 1)
    ax.grid(False)
    ax.axvline(x=DATASET_SWITCH_START+1, color='orange', linestyle=':', alpha=0.7, linewidth=3)
    if RETRAIN_BATCH > 0: ax.axvline(x=RETRAIN_BATCH, color='red', linestyle=':', alpha=0.7, linewidth=3)
    ax.legend(loc='lower left', fontsize=24, ncol=2)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"DS ablation plot saved to {out_path}")

def plot_distribution_shift_model(dir, filename, model_name):
    config = load_config(dir)
    model_res = pd.read_csv(f'{dir}/{model_name}_results.csv')
    model_accuracies = (model_res['predictions'] == model_res['targets']).groupby(model_res['batch']).mean().to_list()

    MAX_UNSW_FRACTION = config['MAX_UNSW_FRACTION']
    DATASET_SWITCH_START = config['DATASET_SWITCH_START']
    N_BATCHES = config['N_BATCHES']

    # Apply rolling average of last 5 batches for smoother plotting
    window_size = 10
    smoothed_model_accuracies = []
    batch_nums = []
    
    for i in range(N_BATCHES):
        start_idx = max(0, i - window_size + 1)
        end_idx = i + 1
        
        # Calculate rolling average
        avg_model_acc = np.mean(model_accuracies[start_idx:end_idx])
        smoothed_model_accuracies.append(avg_model_acc)

        batch_nums.append(i + 1)
    
    plt.rcParams.update({
        'font.size': 26,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    })
    
    # Single-axis plot: Model accuracies, vertical line at first mixed batch
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(batch_nums, smoothed_model_accuracies, '-', linewidth=3, markersize=6, label=model_name)
    ax.set_xlabel('Batch Number')
    ax.set_ylabel('Accuracy')
    ax.set_ylim(0.65, 1)
    ax.grid(False)

    # Vertical line at first mixed batch (1-based index)
    first_mixed_batch = DATASET_SWITCH_START + 1
    ax.axvline(x=first_mixed_batch, color='orange', linestyle=':', alpha=0.7, linewidth=3)

    ax.legend(loc='lower left', fontsize=26)
    plt.tight_layout()
    
    out_path = f'{dir}/{model_name}_gradual_shift_eval_to_{MAX_UNSW_FRACTION:.2f}_{filename}.pdf'
    plt.savefig(out_path, dpi=300, bbox_inches='tight')

    print(f"\nPlot saved to {out_path}")

def plot_distribution_shift_model(dir, filename, models,rw=10):
    plt.rcParams.update({
        'font.size': 26,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    })
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.set_xlabel('Batch Number')
    ax.set_ylabel('Accuracy')
    ax.set_ylim(0.65, 1)
    ax.grid(False)

    binocular_cnt = sum(m.startswith("binocular") for m in models)
    
    for model in models:
        base_res_path = f'{dir}/simple_cross_dataset_eval_{model}'
        model_res = pd.read_csv(f'{base_res_path}/{model}_results.csv')
        model_accuracies = (model_res['predictions'] == model_res['targets']).groupby(model_res['batch']).mean().to_list()
        config = load_config(base_res_path)
        MAX_UNSW_FRACTION = config['MAX_UNSW_FRACTION']
        DATASET_SWITCH_START = config['DATASET_SWITCH_START']
        N_BATCHES = config['N_BATCHES']
        RETRAIN_BATCH = config.get('RETRAIN_BATCH', -1)
        if binocular_cnt==1 and RETRAIN_BATCH > 0: ax.axvline(x=RETRAIN_BATCH, color='red', linestyle=':', alpha=0.7, linewidth=3)

        # Apply rolling average of last 5 batches for smoother plotting
        smoothed_model_accuracies = []
        batch_nums = []
    
        for i in range(N_BATCHES):
            start_idx = max(0, i - rw + 1)
            end_idx = i + 1
            
            # Calculate rolling average
            avg_model_acc = np.mean(model_accuracies[start_idx:end_idx])
            smoothed_model_accuracies.append(avg_model_acc)

            batch_nums.append(i + 1)
    
        # Single-axis plot: Model accuracies, vertical line at first mixed batch
        ax.plot(batch_nums, smoothed_model_accuracies, '-', linewidth=3, markersize=6, label=model)

    # Vertical line at first mixed batch (1-based index)
    first_mixed_batch = DATASET_SWITCH_START + 1
    ax.axvline(x=first_mixed_batch, color='orange', linestyle=':', alpha=0.7, linewidth=3)

    ax.legend(loc='lower left', fontsize=26)
    plt.tight_layout()
    
    out_path = f'{dir}/gradual_shift_eval_to_{MAX_UNSW_FRACTION:.2f}_{filename}.pdf'
    plt.savefig(out_path, dpi=300, bbox_inches='tight')

    print(f"\nPlot saved to {out_path}")


def plot_training_accuracies(dir, model, filename, out):
    """
    Plot training accuracy per epoch with a rolling average (window=6).

    Args:
        accuracies (list or array-like): list of accuracy values, one per epoch.
    """
    model_results_dir = f'{dir}/simple_cross_dataset_eval_{model}'
    accuracies = pd.read_csv(f'{model_results_dir}/{filename}')['batch_accuracies'].tolist()

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
    confidence_plot_path = f'{model_results_dir}/{model}_{out}_training.pdf'
    plt.savefig(confidence_plot_path, dpi=300, bbox_inches='tight', edgecolor='black')
    plt.close()
    print(f"Training accuracy plot saved to {confidence_plot_path}")


def plot_confidence_scores(dir, model):
    model_results_dir = f'{dir}/simple_cross_dataset_eval_{model}'

    unique_confs = pd.read_csv(f'{model_results_dir}/unique_confidences.csv')['confidence'].tolist()
    weighted_values_to_plot = pd.read_csv(f'{model_results_dir}/weighted_values.csv')['weighted_value'].tolist()
    weighted_prob = pd.read_csv(f'{model_results_dir}/weighted_probabilities.csv')['weighted_prob'].tolist()
    confident_scores = pd.read_csv(f'{model_results_dir}/confident_scores.csv')['confident_score'].tolist()

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
    confidence_plot_path = f'{model_results_dir}/bnn_gradual_shift_confidence.pdf'
    plt.savefig(confidence_plot_path, dpi=300, bbox_inches='tight', edgecolor='black')
    plt.close()
    
    print(f"Confidence score plot saved to {confidence_plot_path}")


def plot_retraining_comparison_bars(directory, model, filename):
    
    """
    Reads accuracy CSVs, splits data based on RETRAIN_BATCH, and plots
    a grouped bar chart.
    
    Style: 
    - Bars for the same model share the same base color.
    - Pre-Retrain: Lighter alpha + Hatched pattern.
    - Post-Retrain: Solid color.
    """
    directory = f'{directory}/simple_cross_dataset_eval_{model}'

    # 1. Load Configuration
    config = load_config(directory)
    shap_res, rand_res, teacher_res, shap_no_conf_res = load_models_results(directory, model)

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

    # -- BNN Random
    try:
        rand_acc = (rand_res['predictions'] == rand_res['targets']).groupby(rand_res['batch']).mean().to_list()
        models_data.append({'name': 'RND', 'data': rand_acc})
    except FileNotFoundError:
        pass # Silent fail if disabled
    
    # -- BNN SHAP
    try:
        shap_acc = (shap_res['predictions'] == shap_res['targets']).groupby(shap_res['batch']).mean().to_list()
        models_data.append({'name': 'SHAP', 'data': shap_acc})
    except FileNotFoundError:
        print("Warning: binocular_tiny_accuracies.csv not found.")

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

    save_path = os.path.join(directory, f'bnn_gradual_{filename}.pdf')
    plt.savefig(save_path)
    print(f"DS bar chart saved to {save_path}")
    # plt.show()

def basic_stats(dir, model):
    model_res_dir = f'{dir}/simple_cross_dataset_eval_{model}'
    config= load_config(model_res_dir)
    RETRAIN_BATCH = config.get('RETRAIN_BATCH', 0)-1
    DATASET_SWITCH_END = config.get('DATASET_SWITCH_END', 0)-1
    DATASET_SWITCH_START = config.get('DATASET_SWITCH_START', 0)-1
    model_results = {
        f'{model_res_dir}/{model}_results.csv': 'BNN shap',
        f'{model_res_dir}/{model}_no_conf_results.csv': 'BNN no conf',
        f'{model_res_dir}/{model}_random_results.csv': 'BNN rand',
        f'{model_res_dir}/teacher_results.csv': 'Teacher'
    }

    for model_result_path, label in model_results.items():
        if not os.path.isfile(model_result_path):
            raise FileNotFoundError(f"Required results file {model_result_path} not found.")
        model_res= pd.read_csv(model_result_path)
        # model_metric = (model_res['predictions'] == model_res['targets']).groupby(model_res['batch']).mean().to_list()
        model_f1 = (
            model_res.groupby("batch")
            .apply(lambda g: accuracy_score(g["targets"], g["predictions"]))
        ).to_list()
        model_acc = (
            model_res.groupby("batch")
            .apply(lambda g: f1_score(g["targets"], g["predictions"]))
        ).to_list()
        model_prec = (
            model_res.groupby("batch")
            .apply(lambda g: precision_score(g["targets"], g["predictions"]))
        ).to_list()
        model_rec = (
            model_res.groupby("batch")
            .apply(lambda g: recall_score(g["targets"], g["predictions"]))
        ).to_list()
        print()
        print(f'********* STATS for {label} *********')
        print(f'\tmean pre-DS\t\t| F1: {np.mean(model_f1[:DATASET_SWITCH_START]):.3f}, Acc: {np.mean(model_acc[:DATASET_SWITCH_START]):.3f}, Prec: {np.mean(model_prec[:DATASET_SWITCH_START]):.3f}, Rec: {np.mean(model_rec[:DATASET_SWITCH_START]):.3f}')
        print(f'\tmean post-DS pre-retr\t| F1: {np.mean(model_f1[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Acc: {np.mean(model_acc[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Prec: {np.mean(model_prec[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Rec: {np.mean(model_rec[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}')
        print(f'\t{bcolors.HEADER}mean post-DS post-retr\t| F1: {np.mean(model_f1[RETRAIN_BATCH:]):.3f}, Acc: {np.mean(model_acc[RETRAIN_BATCH:]):.3f}, Prec: {np.mean(model_prec[RETRAIN_BATCH:]):.3f}, Rec: {np.mean(model_rec[RETRAIN_BATCH:]):.3f}{bcolors.ENDC}')
        print(f'\tmax  pre-retr\t\t| F1: {np.max(model_f1[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Acc: {np.max(model_acc[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Prec: {np.max(model_prec[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Rec: {np.max(model_rec[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}')
        print(f'\tmax  post-retr\t\t| F1: {np.max(model_f1[RETRAIN_BATCH:]):.3f}, Acc: {np.max(model_acc[RETRAIN_BATCH:]):.3f}, Prec: {np.max(model_prec[RETRAIN_BATCH:]):.3f}, Rec: {np.max(model_rec[RETRAIN_BATCH:]):.3f}')
def basic_stats_model(dir, model):
    model_res_path = f'{dir}/simple_cross_dataset_eval_{model}'
    config= load_config(model_res_path)
    model_res = pd.read_csv(f'{model_res_path}/{model}_results.csv')
    
    model_acc = ( 
        model_res.groupby("batch")
        .apply(lambda g: accuracy_score(g["targets"], g["predictions"]))
    ).to_list()
    model_f1 = (
        model_res.groupby("batch")
        .apply(lambda g: f1_score(g["targets"], g["predictions"]))
    ).to_list()
    model_prec = (
        model_res.groupby("batch")
        .apply(lambda g: precision_score(g["targets"], g["predictions"]))
    ).to_list()
    model_rec = (
        model_res.groupby("batch")
        .apply(lambda g: recall_score(g["targets"], g["predictions"]))
    ).to_list()

    RETRAIN_BATCH = config.get('RETRAIN_BATCH', 0)-1
    DATASET_SWITCH_END = config.get('DATASET_SWITCH_END', 0)-1
    DATASET_SWITCH_START = config.get('DATASET_SWITCH_START', 0)-1

    hasBeenRetrained = RETRAIN_BATCH > 0

    print()
    print(f'********* STATS for {model} *********')
    print(f'\tmean pre-DS\t\t| F1: {np.mean(model_f1[:DATASET_SWITCH_START]):3f}, Acc: {np.mean(model_acc[:DATASET_SWITCH_START]):3f}, Prec: {np.mean(model_prec[:DATASET_SWITCH_START]):3f}, Rec: {np.mean(model_rec[:DATASET_SWITCH_START]):3f}')
    if hasBeenRetrained:
        print(f'\tmean post-DS pre-retr\t| F1: {np.mean(model_f1[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Acc: {np.mean(model_acc[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Prec: {np.mean(model_prec[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Rec: {np.mean(model_rec[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}')
        print(f'\t{bcolors.HEADER}mean post-DS post-retr \t| F1: {np.mean(model_f1[RETRAIN_BATCH:]):3f}, Acc: {np.mean(model_acc[RETRAIN_BATCH:]):3f}, Prec: {np.mean(model_prec[RETRAIN_BATCH:]):3f}, Rec: {np.mean(model_rec[RETRAIN_BATCH:]):3f}{bcolors.ENDC}')
    else:
        print(f'\t{bcolors.HEADER}mean post-DS \t\t| F1: {np.mean(model_f1[DATASET_SWITCH_END:RETRAIN_BATCH]):3f}, Acc: {np.mean(model_acc[DATASET_SWITCH_END:RETRAIN_BATCH]):3f}, Prec: {np.mean(model_prec[DATASET_SWITCH_END:RETRAIN_BATCH]):3f}, Rec: {np.mean(model_rec[DATASET_SWITCH_END:RETRAIN_BATCH]):3f}{bcolors.ENDC}')
    print(f'\tmax  pre-retr\t\t| F1: {np.max(model_f1[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Acc: {np.max(model_acc[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Prec: {np.max(model_prec[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}, Rec: {np.max(model_rec[DATASET_SWITCH_END:RETRAIN_BATCH]):.3f}')
    print(f'\tmax  post-retr\t\t| F1: {np.max(model_f1[RETRAIN_BATCH:]):.3f}, Acc: {np.max(model_acc[RETRAIN_BATCH:]):.3f}, Prec: {np.max(model_prec[RETRAIN_BATCH:]):.3f}, Rec: {np.max(model_rec[RETRAIN_BATCH:]):.3f}')
    print()

def get_model_size_in_bits(models):

    def compute_model_size(model_class, arch):
        cfg = get_cfg('models')
        input_size = cfg.getint(arch.upper(), 'INPUT_LAYER')
        model = model_class(cfg, input_size, arch)
        weight_bits = model.features[0].weight_quant.bit_width()
        total_params = sum(p.numel() for p in model.parameters())
        total_size_bits = total_params * weight_bits
        print(f"Model: {model.__class__.__name__}, Arch: {arch}, Total Params: {total_params}, Weight Bits: {weight_bits}, Total Size (bits): {total_size_bits}")

    print("\nCalculating model sizes in bits:\n")
    for model in models:
        model_class = model['model_class']
        arch = model['arch']
        assert model_class is not None, f"Model class for {model} is not defined."
        assert arch is not None, f"Model arch for {model} is not defined."

        compute_model_size(model_class=model_class, arch=arch)