import numpy as np
import theano
import theano.tensor as T
import blocks

# plotting
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = (10.0, 8.0) # set default size of plots
plt.rcParams['image.interpolation'] = 'nearest'
plt.rcParams['image.cmap'] = 'gray'

# data handling
import os
import h5py
from nems.utilities import rolling_window

# LOAD DATA
from scipy.io import loadmat
import os.path as path
data_dir = '/Users/lmcintosh/Git/deepRGC/datasets/white_noise/'
metadata = np.load(path.join(data_dir, 'metadata.npz'))['metadata'].item()
stim  = np.memmap(path.join(data_dir, 'stim_norm.dat'), dtype=metadata['stim_norm_dtype'], 
                  mode='r', shape=metadata['stim_norm_shape'])
rates = np.memmap(path.join(data_dir, 'rates.dat'), dtype=metadata['rates_dtype'], 
                  mode='r', shape=metadata['rates_shape'])

times = np.linspace(0, 0.01*rates.shape[0], rates.shape[0])

# Smooth raw spike count with 10 ms std Gaussian to get PSTHs
from lnl_model_functions import gaussian
rates_filt = np.zeros(rates.shape)
filt       = gaussian(x=np.linspace(-5,5,10), sigma=1, mu=0)
for cell in xrange(rates.shape[1]):
    rates_filt[:,cell] = np.convolve(rates[:,cell], filt, mode='same')

# Store rolled stimulus and filtered rates as X and y
stim_sliced = stim[34:-34, 34:-34,:]
#stim_sliced = stim[52:64, 36:48]
X = rolling_window(stim_sliced, 40)
X = np.rollaxis(X, 2)
X = np.rollaxis(X, 3, 1)
y = rates_filt[X.shape[1]:]


# MAKE MODEL
from blocks.bricks.conv import Convolutional, ConvolutionalLayer, ConvolutionalActivation
from blocks.initialization import IsotropicGaussian, Constant
from blocks.bricks import Rectifier

# First convolutional layer
convlayer = ConvolutionalLayer(Rectifier().apply, filter_size=(11,11), num_filters=2, num_channels=40, batch_size=256, pooling_size=(10,10), image_size=(32,32), weights_init=IsotropicGaussian(), biases_init=Constant(0.01))
convlayer.initialize()

x = T.ftensor4('data')
y = convlayer.apply(x)

#f = theano.function(inputs=[x], outputs=[y])

#output = f(X[:64,:,:,:])

#fig = plt.imshow(np.squeeze(output[0][0,0,:,:]))
#plt.savefig('/Users/lmcintosh/Git/deepRGC/blocks/temp.png')


# SNAP ON THE LOSS FUNCTION
from blocks.bricks.cost import BinaryCrossEntropy
cost = BinaryCrossEntropy().apply(x, y)

from blocks.graph import ComputationGraph
cg = ComputationGraph(cost)


# TRAIN MODEL
from fuel.streams import DataStream
from fuel.datasets import IterableDataset
data_stream = DataStream(IterableDataset([X[:512,:,:,:]]))

from blocks.main_loop import MainLoop
from blocks.algorithms import GradientDescent, Scale
# from blocks.algorithms import RMSProp
from blocks.extensions import FinishAfter
from blocks.extensions.monitoring import TrainingDataMonitoring
from blocks.extensions.plot import Plot
main_loop = MainLoop(
        model=None, data_stream=data_stream,
        algorithm=GradientDescent(cost=cost, params=[convlayer.convolution.convolution.params[0]],
            step_rule=Scale(learning_rate=0.1)),
        extensions=[FinishAfter(after_n_epochs=1),
            TrainingDataMonitoring([cost, convlayer.convolution.convolution.params[0]], after_batch=True),
            Plot('Plotting example', channels=[['cost'], ['W']],
                after_batch=True)])

main_loop.run()

