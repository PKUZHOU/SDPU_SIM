from sim import PE
from sim import System
from compiler import Compiler
from util import read_acc_config
from nn_dataflow.core import Network
from nn_dataflow.nns import import_network
from util import read_acc_config
from sim.task_queue import TaskQueue
from nn_dataflow.core import Network
from nn_dataflow.nns import import_network
from sim.task_queue import TaskQueue
from metric import ANTT, Fairness, STP

acc_cfg_file = "./accelerator_cfg.yaml"
acc_cfg = read_acc_config(acc_cfg_file)

# model_names = net_names = ['alex_net']
# model_names = net_names = ['alex_net','vgg','resnet50']
model_names = net_names = ['alex_net','vgg','resnet50','mlp_m','mlp_l']
# model_names = net_names = ['alex_net','vgg','resnet50','mlp_m','mlp_l','lstm_m','lstm_l']

system = System(acc_cfg)
for model_name in model_names:
    nn = import_network(model_name)
    system.add_task(nn)

system.simulate(Fairness, baseline = False)