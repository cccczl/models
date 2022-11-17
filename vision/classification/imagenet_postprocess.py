# SPDX-License-Identifier: Apache-2.0

import mxnet as mx
import numpy as np

# Post-processing function for ImageNet models
def postprocess(scores):
    '''
    Postprocessing with mxnet gluon
    The function takes scores generated by the network and returns the class IDs in decreasing order
    of probability
    '''
    prob = mx.ndarray.softmax(scores).asnumpy()
    prob = np.squeeze(prob)
    return np.argsort(prob)[::-1]
