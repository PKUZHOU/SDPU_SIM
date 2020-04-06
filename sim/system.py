import sys
sys.path.insert(0,"/home/zhou/SDPU_SIM")
from sim.defines import *
from sim.sdpu_scheduler import SDPU_Scheduler
from sim.sdpu_accelerator import SDPU_Accelerator
from sim.task_queue import TaskQueue
from metric import STP,Fairness,ANTT

class System:
    def __init__(self, acc_config):
        self.acc_config = acc_config
        self.sdpu_scheduler = SDPU_Scheduler()
        self.accelerator = SDPU_Accelerator(acc_config)
        self.task_queue = TaskQueue()

    def add_task(self, nn):
        self.task_queue.add_task(nn)

    def add_tasks(self, nns):
        for nn in nns:
            self.add_task(nn)    

    def simulate(self, target,baseline = False):
        # config the scheduler
        self.sdpu_scheduler.load_acc_cfg(self.acc_config)
        # coarse-grained scheduling
        self.sdpu_scheduler.schedule(self.task_queue,target,baseline)
        # load the task to the accelerator
        self.accelerator.load_tasks(self.task_queue)
        # simulate the execution
        self.accelerator.simulate()

if __name__ == "__main__":
    from util import read_acc_config
    from sim.task_queue import TaskQueue
    from nn_dataflow.core import Network
    from nn_dataflow.nns import import_network
    from sim.task_queue import TaskQueue
    from metric import *

    acc_cfg_file = "./accelerator_cfg.yaml"
    acc_cfg = read_acc_config(acc_cfg_file)

    model_names = net_names = ['alex_net','vgg','resnet50','mlp_m','mlp_l','lstm_m','lstm_l']

    system = System(acc_cfg)
    for model_name in model_names:
        nn = import_network(model_name)
        system.add_task(nn)
    
    # system.instantiate()
    system.simulate(ANTT)