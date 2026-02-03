import os
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from configparser import ConfigParser

from sklearn.metrics import accuracy_score
from sklearn.metrics import auc
from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import roc_curve

from pathlib import Path

import warnings

from sklearn.preprocessing import MinMaxScaler

def round_to_nearest(x, n_blocks=4):
    blocks_bound = 1/n_blocks
    return blocks_bound * round(x / blocks_bound)

def get_cfg(name='mbnn'):
    cfg = ConfigParser()
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join('configs', name.lower() + '.ini')
    assert os.path.exists(config_path), f"{config_path} not found."
    cfg.read(config_path)
    
    return cfg

def data_preprocess(data: pd.DataFrame, spec_dict, binarization=False):
    categorical_features_values, continuous_features_values, list_drop = spec_dict.values()

    data.drop(list_drop,axis=1,inplace=True, errors='ignore')

    # limit non-unique value for categorical features
    # cols_cat = data.select_dtypes(exclude=[np.number]).columns
    # if cols_cat.any():
    #     for feat in cols_cat: 
    #         if data[feat].nunique()>categorical_features_values:
    #             data[feat] = np.where(data[feat].isin(data[feat].value_counts().head(categorical_features_values).index), data[feat], '-')
            
    #         data[feat] = data[feat].astype('category')
    #         data[feat] = data[feat].cat.codes

    og_samples = data.copy()

    # clamping continuous values exceeding 95 quantile
    data_num = data.select_dtypes(include=[np.number])
    for feature in data_num.columns:
        if data_num[feature].max()>10*data_num[feature].median() and data_num[feature].max()>10 :
            data[feature] = np.where(data[feature]<data[feature].quantile(0.95), data[feature], data[feature].quantile(0.95))

    # from bool features to int
    bool_cols = data.select_dtypes(include=bool).columns
    if(len(bool_cols) > 0):
        data[bool_cols] = data[bool_cols].astype(int)

    return data, og_samples

def get_feature_from_bitno(bitno: int, binarization_cfg=None):
    """
    Given a global bit index, return:
    - feature name
    - bit index inside the feature (0 = MSB)

    bitno is 0-based.
    """
    if binarization_cfg is None:
        binarization_cfg = get_cfg('binarization')

    if bitno < 0:
        raise ValueError("bitno must be non-negative")

    cumulative_bits = 0

    for feature_name in binarization_cfg.options('FEATURE_BIT_WIDTHS'):
        bit_width = binarization_cfg.getint('FEATURE_BIT_WIDTHS', feature_name)

        if cumulative_bits <= bitno < cumulative_bits + bit_width:
            bit_idx = bitno - cumulative_bits
            return feature_name, bit_idx

        cumulative_bits += bit_width

    raise IndexError(f"bitno {bitno} exceeds total binarized feature length")


def data_binarization(samples: pd.DataFrame, selected_columns=None):
    # Load feature bit widths from configuration file
    binarization_cfg = get_cfg('binarization')
    feaures_bit_width = {}
    
    # Read all feature bit widths from the config file
    for feature_name in binarization_cfg.options('FEATURE_BIT_WIDTHS'):
        feaures_bit_width[feature_name] = binarization_cfg.getint('FEATURE_BIT_WIDTHS', feature_name)

    total_bits = sum(feaures_bit_width.values())
    Xbin = np.zeros((samples.shape[0], total_bits))
    
    for i in range(samples.shape[0]):
        write_ptr = 0
        
        for j, feature_name in enumerate(selected_columns):
            column_val = int(samples.iloc[i, j])
            
            # Clamp value to maximum representable value
            bit_width = feaures_bit_width[feature_name]
            max_val = (2 ** bit_width) - 1
            column_val = min(column_val, max_val)
            
            # Convert to binary and pad with zeros
            binary_str = bin(column_val)[2:]
            binary_list = [int(x) for x in binary_str]
            padded_binary = [0] * (bit_width - len(binary_list)) + binary_list
            
            # Write binary values to output array
            for bin_val in padded_binary:
                Xbin[i, write_ptr] = bin_val
                write_ptr += 1

    return Xbin

def suppress_warnings():
    # Suppress brevitas Warning
    warnings.filterwarnings(
        "ignore",
        message="Defining your `__torch_function__` as a plain method is deprecated",
        category=UserWarning,
    )

def metrics_binary_dataset(y_test, y_pred, y_score, is_bnn=False):
    
    if is_bnn:
        # Make y_test 1D
        y_test = np.argmax(y_test, axis=1)
        
    a = accuracy_score(y_test, y_pred)
    p = precision_score(y_test, y_pred, average='binary')
    r = recall_score(y_test, y_pred, average='binary')
    f1 = f1_score(y_test, y_pred, average='binary')

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    
    tpr = r
    fpr = fp / (fp+tn)
    fnr = fn / (fn+tp)
    tnr = tn / (tn+fp)
    
    y_score = pd.get_dummies(y_pred).values
    fpr_, tpr_, _ = roc_curve(y_test, y_score[:, 1])
    roc_auc = auc(fpr_, tpr_)

    return a, p, r, tpr, fpr, fnr, f1, roc_auc

def get_file_from_keyword(directory, keyword):
    path = Path(directory)
    for file in path.iterdir():
        if file.is_file() and keyword in file.name:
            return file
    return None

def softmax(x):
    return np.exp(x) / np.sum(np.exp(x), axis=0)

def softmax_temp(x, temp=1.0):
    """Compute softmax values for each sets of scores in x with temperature scaling."""
    x = x / temp
    e_x = np.exp(x - np.max(x))  # Subtract max for numerical stability
    return e_x / e_x.sum()

def multiple_temp_softmax(x, temps=[1.0, 2.0, 3.0]):
    """Compute softmax values for each sets of scores in x with multiple temperature scaling."""
    softmax_results = [softmax_temp(x, temp) for temp in temps]
    return softmax_results

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

def analyze_confidence_distribution(bnn_trainer, X_val_shaped, Y_val, RES_DIR):
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