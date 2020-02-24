from nn_dataflow.core import Network
from nn_dataflow.nns import import_network


if __name__ == "__main__":
    alex_net = import_network('alex_net')
    resnet50 = import_network('resnet50')

    # print(alex_net)
    print(alex_net.layer_dict)
    print(alex_net[alex_net.INPUT_LAYER_KEY])