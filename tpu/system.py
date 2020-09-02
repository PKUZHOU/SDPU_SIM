from .tpu import TPU
from sim.task_queue import TaskQueue

class System:
    def __init__(self, acc_config):
        self.acc_config = acc_config
        self.accelerator = TPU("TPU")
        self.task_queue = TaskQueue()

    def add_task(self, nn):
        self.task_queue.add_task(nn)

    def add_tasks(self, nns):
        for nn in nns:
            self.add_task(nn)    

    def simulate(self):
        # config the accelerator
        self.accelerator.load_acc_config(self.acc_config)
        # build the accelerator
        self.accelerator.build()
        # load the task to the accelerator
        self.accelerator.load_tasks(self.task_queue)
        # simulate the execution
        self.accelerator.simulate()

    def profiling(self):
        self.accelerator.profiling()
