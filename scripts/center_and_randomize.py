# script to center weights
import matplotlib
matplotlib.use('Agg')
import numpy as np
from os.path import expanduser
import os
import pyret.filtertools as ft
from keras.models import model_from_json
from deepretina.toolbox import load_model
import h5py

f = input("Please enter the model hash + name, e.g. 3520cd convnet. ")
mdl_dir = os.path.expanduser('~/deep-retina-results/database/%s/' %f)
weight_name = 'best_weights.h5'
model = load_model(mdl_dir, weight_name)
weights = model.get_weights()

new_weights = np.copy(weights[0])

# for each subunit filter type
for idw, w in enumerate(new_weights):
    space, time = ft.decompose(w)
    peak, widths, theta = ft.get_ellipse(np.arange(space.shape[0]), np.arange(space.shape[1]), space)
    peak = np.round(np.array(peak)).astype(int)[::-1]
    peak2 = np.unravel_index(np.argmax(abs(space)), space.shape)
    center = np.round([s/2 for s in space.shape]).astype('int')
    centered_w = np.copy(w)
    for ax, shift in enumerate(peak):
        # roll array elements according to (array, shift, axis)
        centered_w = np.roll(centered_w, center[ax]-shift-1, ax+1)
    
    new_weights[idw] = centered_w

# save new weights in an h5 file
new_weight_name = 'centered_weights.h5'
copy_command = 'cp "%s" "%s"' %(mdl_dir + weight_name, mdl_dir + new_weight_name)
os.system(copy_command)

weight_scale = 0.01

with h5py.File(mdl_dir + new_weight_name, 'r+') as h:
    data = h['layer_0/param_0']
    data[...] = new_weights

    # now randomize all higher weights
    for i, l in enumerate(model.layers):
        if 'param_0' in h['layer_%i' %i].keys():
            data = h['layer_%i/param_0' %i]
            random_weights = weight_scale * np.random.randn(*h['layer_%i/param_0' %i].shape)
            data[...] = random_weights