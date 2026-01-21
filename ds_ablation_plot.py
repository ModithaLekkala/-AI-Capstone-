from helpers.utils import plot_confidence_scores, plot_distribution_shift_bnn, plot_training_accuracies, plot_retraining_comparison_bars, basic_stats
import argparse
import os
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--res_dir', type=str, default='results', help='Directory containing evaluation results.')
    parser.add_argument('--model','-m', type=str, required=True, help='Model architecture being evaluated.')
    parser.add_argument('-o', type=str, required=False, help='Output plot filename.')
    parser.add_argument('-rw', type=int, default=10, help='Rolling window size for smoothing.')
    args = parser.parse_args()

    if not os.path.exists(args.res_dir):
        raise FileNotFoundError(f"Directory {args.res_dir} does not exist.")
    
    plot_distribution_shift_bnn(dir=args.res_dir, model=args.model, enable_bnn_random_plot=True, enable_bnn_no_conf_plot=True, filename=args.o, rolling_window=args.rw)
    plot_confidence_scores(args.res_dir, args.model)
    plot_retraining_comparison_bars(args.res_dir, args.model, filename='comparison')

    plot_training_accuracies(args.res_dir, args.model, filename=f'{args.model}_train_accuracies.csv', out='bnn_shap')
    plot_training_accuracies(args.res_dir, args.model, filename=f'{args.model}_train_rand_accuracies.csv', out='bnn_rand')

    basic_stats(args.res_dir, args.model)

if __name__ == "__main__":
    main()