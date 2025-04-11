import os
import torch
import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix

from configparser import ConfigParser

from models import deeper, smaller

def data_preprocess(rawdata: pd.DataFrame, spec_dict):
    categorical_features_values, continuous_features_values, list_drop = spec_dict.values()

    data = pd.concat([rawdata])
    data.drop(list_drop,axis=1,inplace=True, errors='ignore')
    samples_before_process = data.copy()

    # clamping continuous values
    data_num = data.select_dtypes(include=[np.number])
    for feature in data_num.columns:
        if data_num[feature].max()>10*data_num[feature].median() and data_num[feature].max()>10 :
            data[feature] = np.where(data[feature]<data[feature].quantile(0.95), data[feature], data[feature].quantile(0.95))

    # unskew data applying log
    data_num = data.select_dtypes(include=[np.number])
    for feature in data_num.columns:
        if data_num[feature].nunique()>continuous_features_values:
            if data_num[feature].min()==0:
                data[feature] = np.log(data[feature]+1)
            else:
                data[feature] = np.log(data[feature])

    # limit non-unique value for categorical features
    data_cat = data.select_dtypes(exclude=[np.number])
    for feature in data_cat.columns:
        if data_cat[feature].nunique()>categorical_features_values:
            data[feature] = np.where(data[feature].isin(data[feature].value_counts().head(categorical_features_values).index), data[feature], '-')

    # split features and labels
    samples = data[data.columns[:-1]]
    labels = data[data.columns[-1]]

    # one hot encoding of categorical features
    print(f'Feature count before one-hot encoding: {samples.shape[1]}')
    one_hot = pd.get_dummies(data=samples, columns=data_cat.columns)
    old_samples = samples
    print(f'Feature count after one-hot encoding: {one_hot.shape[1]}')
    print(f'Added   features: {one_hot[one_hot.columns.difference(old_samples.columns)].columns.to_list()}')
    print(f'Removed features: {old_samples[old_samples.columns.difference(one_hot.columns)].columns.to_list()}')
    samples=one_hot

    # from bool features to int
    bool_cols = samples.select_dtypes(include=bool).columns
    samples[bool_cols] = samples[bool_cols].astype(int)

    # normalize float column
    scaler = StandardScaler()
    data_num = samples.select_dtypes(include=np.number)
    samples[data_num.columns] = scaler.fit_transform(data_num)

    # X_bin = torch.tensor(data_binarization(samples), dtype=torch.float32)
    X = torch.tensor(samples.values, dtype=torch.float32)
    Y = torch.tensor(labels.values, dtype=torch.long)

    return X, Y, 0, samples_before_process, samples

def get_features_size(tr_samples: pd.DataFrame):
    Xint = tr_samples.astype('int')
    for feat in tr_samples.columns:
        quantile_99 = tr_samples[feat].quantile(0.99)        

    return

def data_binarization(samples):
    feats_size = get_features_size(samples)

    samples_int = samples.astype('int')

    Xbin = np.zeros( (samples_int.shape[0], sum(feats_size.values())) )
    for i, feature_row in enumerate(samples_int):
        # the index at which the next binary value should be written
        write_ptr = 0
        for j, column_val in enumerate(feature_row):
            # Transforming in KB sbytes, dbytes, sload, dload
            if j in [2,3,6,7]:
                column_val = int(column_val/1000) 
            # Setting to maximum any value above the max given the number of b
            if (column_val > 2**feats_size[j] - 1):
                column_val = 2**feats_size[j] - 1
            tmp = list(bin(column_val)[2:])
            tmp = [int(x) for x in tmp]
            # zero padding to the left
            tmp = [0]*(feats_size[j] - len(tmp)) + tmp
            for k, bin_val in enumerate(tmp):
                Xbin[i,write_ptr] = bin_val
                write_ptr += 1

    return Xbin

def get_model_cfg(quantized, name='default'):
    cfg = ConfigParser()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'cfgs', name.lower() + '.ini')
    assert os.path.exists(config_path), f"{config_path} not found."
    cfg.read(config_path)

    if quantized:
        model = smaller(cfg)
    else:
        model = deeper(cfg)

    return model, cfg
