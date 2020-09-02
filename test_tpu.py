
from util.config_reader import read_acc_config
from sim.task_queue import TaskQueue
from nn_dataflow.core import Network
from nn_dataflow.nns import import_network
from sim.task_queue import TaskQueue
from tpu.system import System

acc_cfg_file = "./tpu_cfg.yaml"
acc_cfg = read_acc_config(acc_cfg_file)

model_names = net_names = ['resnet50']

system = System(acc_cfg)

# each model is a task
for model_name in model_names:
    nn = import_network(model_name)
    system.add_task(nn)

system.simulate()
system.profiling()