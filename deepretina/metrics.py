"""
Metrics comparing predicted and recorded firing rates

"""

from __future__ import absolute_import, division, print_function
import numpy as np
from scipy.stats import pearsonr
from functools import wraps

__all__ = ['cc', 'lli', 'rmse', 'fev']


def multicell(metric):
    """Decorator for turning a function that takes two 1-D numpy arrays, and
    makes it work for when you have a list of 1-D arrays or a 2-D array, where
    the metric is applied to each item in the list or each matrix row.
    """
    @wraps(metric)
    def multicell_wrapper(r, rhat):

        # ensure that the arguments have the right shape / dimensions
        for arg in (r, rhat):
            assert isinstance(arg, (np.ndarray, list, tuple)), \
                "Arguments must be a numpy array or list of numpy arrays"

        # convert arguments to matrices
        true_rates = np.atleast_2d(r)
        model_rates = np.atleast_2d(rhat)

        assert true_rates.ndim == 2, "Arguments have too many dimensions"
        assert true_rates.shape == model_rates.shape, "Shapes must be equal"

        # compute scores for each pair
        scores = [metric(true_rate, model_rate)
                  for true_rate, model_rate in zip(true_rates, model_rates)]

        # return the mean across cells and the full list
        return np.nanmean(scores), scores

    return multicell_wrapper


@multicell
def cc(r, rhat):
    """Pearson's correlation coefficient

    If r, rhat are matrices, cc() computes the average pearsonr correlation
    of each column vector
    """
    return pearsonr(r, rhat)[0]


@multicell
def lli(r, rhat):
    """Log-likelihood (arbitrary units)"""
    epsilon = 1e-9
    return np.mean(r * np.log(rhat + epsilon) - rhat)


@multicell
def rmse(r, rhat):
    """Root mean squared error"""
    return np.sqrt(np.mean((rhat - r) ** 2))


@multicell
def fev(r, rhat):
    """Fraction of explained variance

    https://wikipedia.org/en/Fraction_of_variance_unexplained
    """
    return 1.0 - rmse(r, rhat)[0]**2 / r.var()
