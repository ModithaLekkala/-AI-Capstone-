from helpers.utils import plot_distribution_shift_model, basic_stats_model
import argparse
import os
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--res_dir', type=str, default='results', help='Directory containing evaluation results.')
    parser.add_argument('-m', nargs='+', required=True, help='Model to visualize comparison for.')
    parser.add_argument('-o', type=str, default='comparison', help='Output plot filename.')
    parser.add_argument('-rw', type=int, default=10, help='Rolling window size for smoothing.')

    args = parser.parse_args()

    if not os.path.exists(args.res_dir):
        raise FileNotFoundError(f"Directory {args.res_dir} does not exist.")
    
    print('\nGenerating plots and evaluation...')
    plot_distribution_shift_model(args.res_dir, filename=args.o, models=args.m, rw=args.rw)
    for model in args.m:
        print(f'\nGenerating basic stats for {model}...')
        basic_stats_model(args.res_dir, model=model)

if __name__ == "__main__":
    main()