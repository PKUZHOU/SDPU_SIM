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
NN.add('fc4', FCLayer(1000, 1000))
NN.add('fc5', FCLayer(1000, 1000))
NN.add('fc6', FCLayer(1000, 1000))
NN.add('fc7', FCLayer(1000, 1000))
NN.add('fc8', FCLayer(1000, 1000))
NN.add('fc9', FCLayer(1000, 1000))
NN.add('fc10', FCLayer(1000, 1000))
NN.add('fc11', FCLayer(1000, 1000))
NN.add('fc12', FCLayer(1000, 1000))
NN.add('fc13', FCLayer(1000, 1000))
NN.add('fc14', FCLayer(1000, 1000))
NN.add('fc15', FCLayer(1000, 1000))
NN.add('fc16', FCLayer(1000, 1))
