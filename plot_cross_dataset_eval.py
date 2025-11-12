from helpers.utils import plot_confidence_scores, plot_distribution_shift_bnn, plot_training_accuracies
import argparse
import os
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=str, required=True, help='Directory containing evaluation results.')
    args = parser.parse_args()

    if not os.path.exists(args.dir):
        raise FileNotFoundError(f"Directory {args.dir} does not exist.")
    
    plot_distribution_shift_bnn(args.dir)
    plot_confidence_scores(args.dir)
    plot_training_accuracies(args.dir)

if __name__ == "__main__":
    main()