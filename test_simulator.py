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
exit
#get the network 
model = import_network('alex_net')

#load the cfg and network
compiler.load_acc_cfg(acc_cfg)
compiler.load_nn(model)

#compile the network
layers_config_regs = compiler.compile()

sys = System(acc_cfg)

for per_layer_config_regs in layers_config_regs:
    sys.load_config_regs(per_layer_config_regs)
    break 

sys.instantiate()
sys.simulate()
print("Simulation Finished!")