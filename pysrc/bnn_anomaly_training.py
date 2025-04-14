import sys
import argparse
import torch
import kagglehub

from trainer import Trainer

torch.set_printoptions(precision=10)

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

    # execution modes
    parser.add_argument("--evaluate", dest="evaluate", action="store_true", help="evaluate model on validation set")
    parser.add_argument("--log_freq", type=int, default=40)
    parser.add_argument("--balance_dataset", action="store_true", help="if dataset is unbalanced from a classes distribution pov, balance it")

    # Hyperparams
    parser.add_argument("--batch_size", default=1024, type=int, help="batch size")
    parser.add_argument("--lr", default=0.01, type=float, help="Learning rate")
    parser.add_argument("--optim", type=none_or_str, default="ADAM", help="Optimizer to use")
    parser.add_argument("--loss", type=none_or_str, default="CrossEntropy", help="Loss function to use")
    parser.add_argument("--scheduler", default="PLATEAU", type=none_or_str, help="LR Scheduler")
    parser.add_argument("--patience", default=3, type=int, help="Scheduler step after that number of epochs without loss decrease")
    parser.add_argument("--momentum", default=0.9, type=float, help="Momentum")
    parser.add_argument("--weight_decay", default=0, type=float, help="Weight decay")
    parser.add_argument("--epochs", default=30, type=int, help="Number of epochs")
    
    # Cfgs
    parser.add_argument("--quantized", action="store_true", help="Neural network")
    parser.add_argument("--checkpoints_path", type=none_or_str,  default="pysrc/models", help="Directory where model checkpoitns will be saved")

    parsed_args = parser.parse_args(args)

    # Conditional check: if scheduler is not PLATEAU and patience was provided, raise an error.
    if parsed_args.scheduler.upper() != "PLATEAU" and parsed_args.patience is not None:
        parser.error("--patience is only allowed when --scheduler is PLATEAU")

    return parsed_args


def main():
    args = parse_args(sys.argv[1:])
    trainer = Trainer(args)

    if args.evaluate:
        with torch.no_grad():
            trainer.eval_model()
    else:
        trainer.train_model()
    return

if __name__ == '__main__':
    main()