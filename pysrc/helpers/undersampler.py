#!/usr/bin/env python3
"""
undersample_flows.py

Undersample an imbalanced CSV dataset:
- All class `1` samples are kept
- Class `0` samples are randomly undersampled according to a given ratio

Usage:
    python undersample_flows.py -i flows_test.csv -o flows_balanced.csv -t label --ratio 1.0
"""

import argparse
import pandas as pd
from imblearn.under_sampling import RandomUnderSampler

def print_stats(y, title: str):
    """Print basic statistics of class distribution."""
    print(f"\n[STATS] {title}")
    total = len(y)
    counts = y.value_counts()
    for cls, count in counts.items():
        pct = 100.0 * count / total
        print(f"  Class {cls}: {count} samples ({pct:.2f}%)")
    print(f"  Total samples: {total}\n")

def undersample_csv(infile: str, outfile: str, target_col: str = "label", ratio: float = 1.0):
    print(f"[INFO] Loading dataset from {infile} ...")
    df = pd.read_csv(infile)

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

    df_res = pd.concat([X_res, y_res], axis=1)

    print_stats(y_res, "After undersampling")

    df_res.to_csv(outfile, index=False)
    print(f"[INFO] Balanced dataset saved to {outfile}")

def main():
    parser = argparse.ArgumentParser(description="Undersample majority class (0) while keeping all class 1 samples.")
    parser.add_argument("-i", "--input", required=True, help="Input CSV file (imbalanced dataset)")
    parser.add_argument("-o", "--output", required=True, help="Output CSV file (undersampled dataset)")
    parser.add_argument("-t", "--target", default="label", help="Target column name (default: 'label')")
    parser.add_argument("--ratio", type=float, default=1.0,
                        help="Undersampling ratio: majority = ratio × minority (default: 1.0 = balance)")
    args = parser.parse_args()

    undersample_csv(args.input, args.output, args.target, args.ratio)

if __name__ == "__main__":
    main()
