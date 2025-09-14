
import pandas as pd
import numpy as np

# global data definitions
CICIDS2017_PATH = '/home/sgeraci/Desktop/datasets/CICIDS2017'
DATASETS_PATH = f'{CICIDS2017_PATH}/MachineLearningCVE'

MONDAY = f'{DATASETS_PATH}/Monday-WorkingHours.pcap_ISCX.csv'
TUESDAY = f'{DATASETS_PATH}/Tuesday-WorkingHours.pcap_ISCX.csv'
WEDNESDAY = f'{DATASETS_PATH}/Wednesday-workingHours.pcap_ISCX.csv'
THURSDAY1 =  f'{DATASETS_PATH}/Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv'
THURSDAY2 =  f'{DATASETS_PATH}/Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv'
FRIDAY1 = f'{DATASETS_PATH}/Friday-WorkingHours-Morning.pcap_ISCX.csv'
FRIDAY2 = f'{DATASETS_PATH}/Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv'
FRIDAY3 = f'{DATASETS_PATH}/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv'

# read datasets
mon = pd.read_csv(MONDAY, skipinitialspace=True)
thu = pd.read_csv(TUESDAY, skipinitialspace=True)
wed = pd.read_csv(WEDNESDAY, skipinitialspace=True)
thu1 = pd.read_csv(THURSDAY1, skipinitialspace=True)
thu2 = pd.read_csv(THURSDAY2, skipinitialspace=True)
fri1 = pd.read_csv(FRIDAY1, skipinitialspace=True)
fri2 = pd.read_csv(FRIDAY2, skipinitialspace=True)
fri3 = pd.read_csv(FRIDAY3, skipinitialspace=True)

print(f"File: {MONDAY} has {mon.shape[0]} rows and {mon.shape[1]} columns")
print(f"File: {TUESDAY} has {thu.shape[0]} rows and {thu.shape[1]} columns")
print(f"File: {WEDNESDAY} has {wed.shape[0]} rows and {wed.shape[1]} columns")
print(f"File: {THURSDAY1} has {thu1.shape[0]} rows and {thu1.shape[1]} columns")
print(f"File: {THURSDAY2} has {thu2.shape[0]} rows and {thu2.shape[1]} columns")
print(f"File: {FRIDAY1} has {fri1.shape[0]} rows and {fri1.shape[1]} columns")
print(f"File: {FRIDAY2} has {fri2.shape[0]} rows and {fri2.shape[1]} columns")
print(f"File: {FRIDAY3} has {fri3.shape[0]} rows and {fri3.shape[1]} columns")

weekdays = pd.DataFrame(pd.concat([mon, thu, wed, thu1, thu2, fri1, fri2, fri3], ignore_index=True))


selected_features=[
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets", 
    "Total Fwd Packets",
    "Total Backward Packets",
    "Fwd Packet Length Mean",
    "Bwd Packet Length Mean",
    "Flow IAT Mean",
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Bwd Packet Length Max",
    "Bwd Packet Length Min",
    "FIN Flag Count",
    "SYN Flag Count",
    "RST Flag Count",
    "PSH Flag Count",
    "ACK Flag Count",
    "URG Flag Count",
    "CWE Flag Count",
    "ECE Flag Count",
    "Label"
]


print('Filter dataset by computable features by Tofino.')
weekdays = weekdays[selected_features]
print('Dataset filtered.')

# Find and handle duplicates
duplicate_count = weekdays.duplicated().sum()
# Print the numer of duplicate entries
print(f"{duplicate_count} duplicate entries have been found in the dataset over {weekdays.shape[0]}\n")
# Remove duplicates
weekdays.drop_duplicates(inplace=True)  # or df_data = df_data.drop_duplicates()
# Display relative message
print(f"All duplicates have been removed\n")

# # remove NaN and ±Inf values
weekdays.replace([np.inf, -np.inf], np.nan, inplace=True)
print(f"Row with at least one NaN in weekdays dataset: {weekdays[weekdays.isna().any(axis=1)].shape[0]}")
weekdays.dropna(inplace=True)
print(f"✔ NaN values removed, new shape: {weekdays.shape}")

# remove -1 values with 0
num_cols = weekdays.select_dtypes(include="number").columns
mask = weekdays[num_cols] < 0
weekdays[num_cols] = weekdays[num_cols].mask(mask, 0) 

# weekdays.replace(-1, 0, inplace=True)
# weekdays.clip(lower=0, inplace=True)
print(f"✔ -1 values replace with 0")

weekdays['Label'] = (weekdays['Label'] != 'BENIGN').astype(int)  # Convert 'BENIGN' to 1 and others to 0
print('New values in Label column:', weekdays['Label'].unique())

weekdays.to_csv(f'{CICIDS2017_PATH}/full_cicids2017.csv')
print('Tofino computable full dataset saved.')
