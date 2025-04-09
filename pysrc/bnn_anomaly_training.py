import sys
import argparse
import torch
import kagglehub

from trainer import Trainer

torch.set_printoptions(precision=10)

def add_bool_arg(parser, name, default):
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--" + name, dest=name, action="store_true")
    group.add_argument("--no_" + name, dest=name, action="store_false")
    parser.set_defaults(**{name: default})

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
    parser.add_argument(
        "--evaluate", dest="evaluate", action="store_true", help="evaluate model on validation set")
    parser.add_argument("--log_freq", type=int, default=40)
    # Hyperparams
    parser.add_argument("--batch_size", default=512, type=int, help="batch size")
    parser.add_argument("--lr", default=0.01, type=float, help="Learning rate")
    parser.add_argument("--optim", type=none_or_str, default="ADAM", help="Optimizer to use")
    parser.add_argument("--loss", type=none_or_str, default="CrossEntropy", help="Loss function to use")
    parser.add_argument("--scheduler", default="PLATEAU", type=none_or_str, help="LR Scheduler")
    parser.add_argument("--patience", default=5, type=int, help="Scheduler step after that number of epochs without loss decrease")
    parser.add_argument("--momentum", default=0.9, type=float, help="Momentum")
    parser.add_argument("--weight_decay", default=0, type=float, help="Weight decay")
    parser.add_argument("--epochs", default=10, type=int, help="Number of epochs")
    
    # Cfgs
    parser.add_argument("--quantized", default=False, type=bool, help="Neural network")
    return parser.parse_args(args)


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