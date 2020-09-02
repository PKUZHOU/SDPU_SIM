from nn_dataflow.core import Network
from nn_dataflow.core import InputLayer, FCLayer

'''
MLP-L

PRIME, 2016
'''

NN = Network('LSTM-M')

NN.set_input_layer(InputLayer(1000, 1))

NN.add('fc1', FCLayer(1000, 1000))
NN.add('fc2', FCLayer(1000, 1000))
NN.add('fc3', FCLayer(1000, 1000))
NN.add('fc4', FCLayer(1000, 1))
