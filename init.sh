set -e

echo "Download CIC-IDS-2017..."

PRIMARY_CICIDS_URL="http://cicresearch.ca/CICDataset/CIC-IDS-2017/Dataset/CIC-IDS-2017/CSVs/MachineLearningCSV.zip"
FALLBACK_CICIDS_URL="https://www.kaggle.com/api/v1/datasets/download/chethuhn/network-intrusion-dataset"

if ! wget --timeout=15 --tries=2 --show-progress -O MachineLearningCSV.zip "$PRIMARY_CICIDS_URL"; then
    echo "Primary download failed. Trying fallback endpoint..."
    wget --timeout=15 --tries=2 --show-progress -O MachineLearningCSV.zip "$FALLBACK_CICIDS_URL"
fi

echo "Download CIC_UNSW_NB15 samples..."
wget --timeout=15 --tries=2 --show-progress \
http://cicresearch.ca/CICDataset/CIC-UNSW/Dataset/Data.csv

echo "Download CIC_UNSW_NB15 labels..."
wget --timeout=15 --tries=2 --show-progress \
http://cicresearch.ca/CICDataset/CIC-UNSW/Dataset/Label.csv

mkdir -p data/CICIDS2017
mkdir -p data/CIC_UNSW_NB15

echo "Extracting CIC-IDS-2017..."
tar -xvzf MachineLearningCSV.zip
rm MachineLearningCSV.zip

echo "Processing CIC-IDS-2017 and CIC_UNSW_NB15..."
python full_dataset_prep.py

rm -rf MachineLearningCVE
rm -f Data.csv Label.csv

echo "Datasets preparation terminated successfully."
