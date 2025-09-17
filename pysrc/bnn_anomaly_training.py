import sys
import argparse
import torch

from trainer import Trainer
from utils import suppress_warnings

def none_or_str(value):
    if value == "None":
        return None
    return value

def none_or_int(value):
    if value == "None":
        return None
    return int(value)

def parse_args(args):
    parser = argparse.ArgumentParser(description="UNSW_NB15 Training")

    # Execution modes
    parser.add_argument("--evaluate", dest="evaluate", action="store_true", help="evaluate model on validation set")
    parser.add_argument("--log_freq", type=int, default=40)
    parser.add_argument("--balance_dataset", action="store_true", help="if dataset is unbalanced from a classes distribution pov, balance it")
    parser.add_argument("--distilled", action="store_true", help="train distilled model")
    parser.add_argument("--model", type=none_or_str, required=True, help="NN between tbnn, mbnn, fullmlp")


    # Hyperparams
    parser.add_argument("--batch_size", default=2048, type=int, help="batch size")
    parser.add_argument("--lr", default=5e-4, type=float, help="Learning rate")
    parser.add_argument("--optim", type=none_or_str, default="ADAM", help="Optimizer to use")
    parser.add_argument("--loss", type=none_or_str, default="SqrHinge", help="Loss function to use")
    parser.add_argument("--scheduler", default="FIXED", type=none_or_str, help="LR Scheduler")
    parser.add_argument("--patience", default=6, type=int, help="Scheduler step after that number of epochs without loss decrease")
    parser.add_argument("--momentum", default=0.9, type=float, help="Momentum")
    parser.add_argument("--weight_decay", default=1e-3, type=float, help="Weight decay")
    parser.add_argument("--epochs", default=2, type=int, help="Number of epochs")
    parser.add_argument("--folds", default=5, type=int, help="Number of fold for cross-validation")
    
    # Configurations
    parser.add_argument("--checkpoints_path", type=none_or_str,  default="pysrc/results", help="Directory where model checkpoitns will be saved")
    parser.add_argument("--subset_size", type=int, default=None, help="If set, get a random subset, to troubleshooting purpose")

    # Input dataset
    parser.add_argument("--dataset-name", type=none_or_str, help="Dataset")
    # parser.add_argument("--test-dataset-path", type=none_or_str, help="Test dataset path")

    parsed_args = parser.parse_args(args)

    return parsed_args


def main():
    suppress_warnings()
    args = parse_args(sys.argv[1:])

    trainer = Trainer(args)
    trainer.train_model()

    return

if __name__ == '__main__':
    main()