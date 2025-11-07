echo "Download CIC-IDS-2017..."
wget http://cicresearch.ca/CICDataset/CIC-IDS-2017/Dataset/CIC-IDS-2017/CSVs/MachineLearningCSV.zip

echo "Download CIC-UNSW-NB15 samples..."
wget http://cicresearch.ca/CICDataset/CIC-UNSW/Dataset/Data.csv

echo "Download CIC-UNSW-NB15 labels..."
wget http://cicresearch.ca/CICDataset/CIC-UNSW/Dataset/Label.csv

mkdir data
mkdir data/CICIDS2017
mkdir data/CIC-UNSW-NB15

echo "Extracting CIC-IDS-2017..."
tar -xvzf MachineLearningCSV.zip
rm MachineLearningCSV.zip

echo "Processing CIC-IDS-2017 and CIC-UNSW-NB15..."
python full_dataset_prep.py

rm -r MachineLearningCVE
rm Data.csv
rm Label.csv

echo "Datasets preparation termined successfully."