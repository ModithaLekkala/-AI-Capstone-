
import pandas as pd
import numpy as np
import os
from ml_helpers import data_binarization, data_preprocess
from helpers import get_cfg
from imblearn.under_sampling import RandomUnderSampler


# global data definitions
DATA_PATH = 'data'
CICIDS2017_PATH = f'MachineLearningCVE'

MONDAY = f'{CICIDS2017_PATH}/Monday-WorkingHours.pcap_ISCX.csv'
TUESDAY = f'{CICIDS2017_PATH}/Tuesday-WorkingHours.pcap_ISCX.csv'
WEDNESDAY = f'{CICIDS2017_PATH}/Wednesday-workingHours.pcap_ISCX.csv'
THURSDAY1 =  f'{CICIDS2017_PATH}/Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv'
THURSDAY2 =  f'{CICIDS2017_PATH}/Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv'
FRIDAY1 = f'{CICIDS2017_PATH}/Friday-WorkingHours-Morning.pcap_ISCX.csv'
FRIDAY2 = f'{CICIDS2017_PATH}/Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv'
FRIDAY3 = f'{CICIDS2017_PATH}/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv'

CIC_UNSW_NB15_SAMPLES = 'Data.csv'
CIC_UNSW_NB15_LABELS = 'Label.csv'

RENAME_MAP = {
    'Total Fwd Packets': 'Total Fwd Packet',
    'Total Backward Packets': 'Total Bwd Packets',
    'Total Length of Fwd Packets' : 'Total Length of Fwd Packet',
    'Total Length of Bwd Packets' : 'Total Length of Bwd Packet',
    'Total Bwd packets': 'Total Bwd Packets',
    "CWE Flag Count": "CWR Flag Count"
}

FEATURE_MAP = {
    "Total Length of Fwd Packet": "sbytes",
    "Total Length of Bwd Packet": "dbytes",
    "Total Fwd Packet": "spkts",
    "Total Bwd Packets": "dpkts",
    "Flow IAT Mean": "iat_mean",
    "Fwd Packet Length Mean": "smeansz",
    "Bwd Packet Length Mean": "dmeansz",
    "Fwd Packet Length Max": "smaxbytes",
    "Bwd Packet Length Max": "dmaxbytes",
    "Fwd Packet Length Min": "sminbytes",
    "Bwd Packet Length Min": "dminbytes",
    "FIN Flag Count": "fin_cnt",
    "SYN Flag Count": "syn_cnt",
    "RST Flag Count": "rst_cnt",
    "PSH Flag Count": "psh_cnt",
    "ACK Flag Count": "ack_cnt",
    "ECE Flag Count": "ece_cnt",
    "URG Flag Count": "urg_cnt",
    "CWR Flag Count": "cwr_cnt",
    "Label": "label"
}

def main():
# read datasets
    if os.path.exists(CICIDS2017_PATH):
        print('Reading CICIDS2017 files...')
        mon = pd.read_csv(MONDAY, skipinitialspace=True)
        thu = pd.read_csv(TUESDAY, skipinitialspace=True)
        wed = pd.read_csv(WEDNESDAY, skipinitialspace=True)
        thu1 = pd.read_csv(THURSDAY1, skipinitialspace=True)
        thu2 = pd.read_csv(THURSDAY2, skipinitialspace=True)
        fri1 = pd.read_csv(FRIDAY1, skipinitialspace=True)
        fri2 = pd.read_csv(FRIDAY2, skipinitialspace=True)
        fri3 = pd.read_csv(FRIDAY3, skipinitialspace=True)
        cic_ids_2017 = pd.DataFrame(pd.concat([mon, thu, wed, thu1, thu2, fri1, fri2, fri3], ignore_index=True))

        print('Starting CIC-IDS-2017 process...')
        cic_ids_2017 = preprocess_df(cic_ids_2017)
        bin_cic_ids_2017 = binarize_df(cic_ids_2017)
        bin_cic_ids_2017 = undersample_df(bin_cic_ids_2017)
        cic_ids_2017.to_csv(f'{DATA_PATH}/CICIDS2017/full_cicids2017.csv', index=False)
        bin_cic_ids_2017.to_csv(f'{DATA_PATH}/CICIDS2017/bin_cicids2017_168b.csv', index=False)
        print('CICIDS2017 processed datasets saved.')

    if os.path.exists(CIC_UNSW_NB15_SAMPLES):
        print('Reading CIC_UNSW_NB15 files...')
        data = pd.read_csv(CIC_UNSW_NB15_SAMPLES, skipinitialspace=True)
        labels = pd.read_csv(CIC_UNSW_NB15_LABELS, skipinitialspace=True)
        assert len(data)==len(labels)
        cic_unsw_nb15 = pd.DataFrame(pd.concat([data, labels], axis=1))

        print('Starting CIC_UNSW_NB15 process...')
        cic_unsw_nb15 = preprocess_df(cic_unsw_nb15)
        bin_cic_unsw_nb15 = binarize_df(cic_unsw_nb15)
        cic_unsw_nb15.to_csv(f'{DATA_PATH}/CIC_UNSW_NB15/full_cic_unsw_nb15.csv', index=False)
        bin_cic_unsw_nb15.to_csv(f'{DATA_PATH}/CIC_UNSW_NB15/bin_cic_unsw_nb15_168b.csv', index=False)
        print('CIC_UNSW_NB15 processed dataset saved.')

def binarize_df(df: pd.DataFrame):
    df_Y=df[df.columns[-1]]
    x_tmp=df[df.columns[:-1]]

    binarizable_features_map = list(get_cfg('binarization').options('FEATURE_BIT_WIDTHS'))
    Xbin = data_binarization(x_tmp.astype('int'), selected_columns=binarizable_features_map)
    Xbin=pd.DataFrame(Xbin)
    return pd.concat([Xbin, df_Y], axis=1)

def preprocess_df(df: pd.DataFrame):
    print('Filter dataset by computable features by Tofino.')
    df = df.rename(columns=RENAME_MAP)
    df = df[list(FEATURE_MAP.keys())]
    df = df.rename(columns=FEATURE_MAP)
    print('Dataset filtered.')

    # Fix duplicates
    duplicate_count = df.duplicated().sum()
    print(f"{duplicate_count} duplicate entries have been found in the dataset over {df.shape[0]}\n")
    df.drop_duplicates(inplace=True)  # or df_data = df_data.drop_duplicates()
    print(f"All duplicates have been removed\n")

    # remove invalid values
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    print(f"Row with at least one NaN in df dataset: {df[df.isna().any(axis=1)].shape[0]}")
    df.dropna(inplace=True)
    print(f"✔ NaN values removed, new shape: {df.shape}")

    # replace -1 values with 0
    num_cols = df.select_dtypes(include="number").columns
    mask = df[num_cols] < 0
    df[num_cols] = df[num_cols].mask(mask, 0) 
    print(f"✔ Negative values replaced with 0")

    df_cat_cols = df.select_dtypes(exclude=[np.number]).columns
    if 'label' in df_cat_cols:
        df['label'] = (df['label'] != 'BENIGN').astype(int)  # Convert 'BENIGN' to 1 and others to 0
    else:
        df['label'] = (df['label'] == 0).astype(int)
    print('New values in label column:', df['label'].unique())

    dict = {
        'categorical_features_values': 6,
        'continuous_features_values': 50,
        'list_drop': [
            'id',
            'attack_cat'
        ]
    }
    df_Y=df[df.columns[-1]]
    df,  _ = data_preprocess(df[df.columns[:-1]], dict)
    df = pd.concat([df, df_Y], axis=1)
    df = df.reset_index(drop=True)

    return df

def undersample_df(df: pd.DataFrame, target_col: str = "label", ratio: float = 1.4):
    def print_stats(y, title: str):
        """Print basic statistics of class distribution."""
        print(f"\n[STATS] {title}")
        total = len(y)
        counts = y.value_counts()
        for cls, count in counts.items():
            pct = 100.0 * count / total
            print(f"  Class {cls}: {count} samples ({pct:.2f}%)")
        print(f"  Total samples: {total}\n")

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in input CSV.")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    print_stats(y, "Before undersampling")

    # Count classes
    counts = y.value_counts().to_dict()
    if 0 not in counts or 1 not in counts:
        raise ValueError("Dataset must contain both class 0 and class 1.")

    n_minority = counts[1]
    n_majority = int(n_minority * ratio)

    # Define sampling strategy
    strategy = {0: n_majority, 1: n_minority}

    rus = RandomUnderSampler(sampling_strategy=strategy, random_state=42)
    X_res, y_res = rus.fit_resample(X, y)

    df = pd.concat([X_res, y_res], axis=1)

    print_stats(y_res, "After undersampling")

    return df

if __name__ == '__main__':
    main()