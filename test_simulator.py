from sim import PE
from sim import System
from compiler import Compiler
from util import read_acc_config
from nn_dataflow.core import Network
from nn_dataflow.nns import import_network

#get the accelerator config
acc_cfg_file = "./accelerator_cfg.yaml"
acc_cfg = read_acc_config(acc_cfg_file)
compiler = Compiler()

#get the network 
resnet50 = import_network('resnet50')

#load the cfg and network
compiler.load_acc_cfg(acc_cfg)
compiler.load_nn(resnet50)

#compile the network
layers_insts = compiler.compile()

sys = System(acc_cfg)

for per_layer_insts in layers_insts:
    sys.load_insts(per_layer_insts)
    break 

sys.instantiate()
sys.simulate()


