import os
import numpy as np
import pandas as pd

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

def round_to_nearest(x, n_blocks=4):
    blocks_bound = 1/n_blocks
    return blocks_bound * round(x / blocks_bound)


def data_preprocess(data: pd.DataFrame, spec_dict, binarization=False):
    categorical_features_values, continuous_features_values, list_drop = spec_dict.values()

    data.drop(list_drop,axis=1,inplace=True, errors='ignore')

    # limit non-unique value for categorical features
    cols_cat = data.select_dtypes(exclude=[np.number]).columns
    if cols_cat.any():
        for feat in cols_cat: 
            if data[feat].nunique()>categorical_features_values:
                data[feat] = np.where(data[feat].isin(data[feat].value_counts().head(categorical_features_values).index), data[feat], '-')
            
            data[feat] = data[feat].astype('category')
            data[feat] = data[feat].cat.codes

    og_samples = data.copy()

    # clamping continuous values exceeding 95 quantile
    data_num = data.select_dtypes(include=[np.number])
    for feature in data_num.columns:
        if data_num[feature].max()>10*data_num[feature].median() and data_num[feature].max()>10 :
            data[feature] = np.where(data[feature]<data[feature].quantile(0.95), data[feature], data[feature].quantile(0.95))

    # unskew data applying log
    # data_num = data.select_dtypes(include=[np.number])
    # for feature in data_num.columns:
    #     if data_num[feature].nunique()>continuous_features_values:
    #         if data_num[feature].min()==0:
    #             data[feature] = np.log(data[feature]+1)
    #         else:
    #             data[feature] = np.log(data[feature])


    # one hot encoding of categorical features
    # print(f'Feature count before one-hot encoding: {samples.shape[1]}')
    # one_hot = pd.get_dummies(data=samples, columns=cols_cat)
    # old_samples = samples
    # print(f'Feature count after one-hot encoding: {one_hot.shape[1]}')
    # print(f'Added   features: {one_hot[one_hot.columns.difference(old_samples.columns)].columns.to_list()}')
    # print(f'Removed features: {old_samples[old_samples.columns.difference(one_hot.columns)].columns.to_list()}')
    # samples=one_hot

    # from bool features to int
    bool_cols = data.select_dtypes(include=bool).columns
    if(len(bool_cols) > 0):
        data[bool_cols] = data[bool_cols].astype(int)

    # standardize int features
    # if not binarization:
        # standardizer = StandardScaler()
        # data_int = samples.select_dtypes(include=np.number)
        # samples[data_int.columns] = standardizer.fit_transform(data_int)
        
        # normalize float features
        # normalizer = Normalizer()
        # data_float = samples.select_dtypes(include=np.number)
        # samples[data_float.columns] = normalizer.fit_transform(data_float)

        # normalizer = MinMaxScaler()
        # data_float = samples.select_dtypes(include=np.number)
        # samples[data_float.columns] = normalizer.fit_transform(data_float)
    
    # X = torch.tensor(samples.values, dtype=torch.float32)
    # Y = torch.tensor(labels.values, dtype=torch.long)

    # if(binarization):
    #     bin_tmp, bin_desc = data_binarization(samples.astype('int'))
    #     X_bin = torch.tensor(bin_tmp, dtype=torch.float32)
    # else:
    #     X_bin = bin_desc = -1
        
    
    # return samples, labels.values, og_samples
    return data, og_samples


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

def get_cfg(name='mbnn'):
    cfg = ConfigParser()
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join('/home/sgeraci/slu/inet-hynn/p4src', 'configs', name.lower() + '.ini')
    assert os.path.exists(config_path), f"{config_path} not found."
    cfg.read(config_path)
    
    return cfg

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
    p = precision_score(y_test, y_pred)
    r = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='macro')

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