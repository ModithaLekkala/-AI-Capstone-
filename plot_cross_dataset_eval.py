from helpers.utils import plot_confidence_scores, plot_distribution_shift_bnn, plot_training_accuracies, plot_retraining_comparison_bars, basic_stats
import argparse
import os
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=str, required=True, help='Directory containing evaluation results.',)
    args = parser.parse_args()

    if not os.path.exists(args.dir):
        raise FileNotFoundError(f"Directory {args.dir} does not exist.")
    
    print('\nGenerating plots and evaluation...')
    plot_distribution_shift_bnn(args.dir, enable_bnn_random_plot=True, filename='with_random')
    plot_distribution_shift_bnn(args.dir, enable_bnn_no_conf_plot=True, filename='with_no_conf')

    print('\nPlotting confidence scores...')
    plot_confidence_scores(args.dir)

    print('\nPlotting training accuracies...')
    plot_training_accuracies(args.dir, filename='bnn_shap_train_accuracies.csv', out='bnn_shap')
    plot_training_accuracies(args.dir, filename='bnn_shap_train_rand_accuracies.csv', out='bnn_rand')

    print('\nPlotting retraining comparison bars...')
    plot_retraining_comparison_bars(args.dir, filename='comparison')

    basic_stats(args.dir)
    
if __name__ == "__main__":
    main()