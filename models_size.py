from helpers.utils import get_model_size_in_bits, plot_confidence_scores, plot_distribution_shift_bnn, plot_training_accuracies, plot_retraining_comparison_bars, basic_stats

from ml_helpers.models import *
def main():
    models = [
        {
            'arch': 'binocular_tiny',
            'model_class': student,
        },
        {
            'arch': 'binocular_dense',
            'model_class': student,
        },
        {
            'arch': 'binocular_wide',
            'model_class': student,
        },
        {
            'arch': 'quark',
            'model_class': quark
        }
    ]
    get_model_size_in_bits(models)

    
if __name__ == "__main__":
    main()