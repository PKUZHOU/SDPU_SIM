import sys
sys.path.insert(0,"/home/zhou/SDPU_SIM")
from sim.defines import *
import random
from sim.execution_models import ExecutionModels

class SDPU_Status:
    def __init__(self):
        self.available_tile = 36
    
    def set_available_tile(self,number):
        self.available_tile = number

    def get_available_tile(self):
        return self.available_tile

class SDPU_Scheduler:
    def __init__(self):
        self.acc_cfg = None
        self.execution_models = ExecutionModels()

        self.status = SDPU_Status()
        # how many samples per step
        self.K = 100
        # how many total steps
        self.total_step = 50
        # profiling table
        self.PT = []

    def load_acc_cfg(self, acc_cfg):
        """
        Load the accelerator config
        Args:
            acc_cfg: the accelerator config stored in a dict
        Returns:
            no returns
        """
        self.acc_cfg = acc_cfg
        # Also set the config to the execution model
        self.execution_models.set_acc_config(acc_cfg)

    def generate_PT(self, task_queue, total_tile):
        """
        generate the profiling table
        Args:
            task_queue: the input tasks
            total_tile: total tiles in SDPU
        Returns:
            No returns
        """
        total_tasks = task_queue.total_tasks
        for task_index in range(total_tasks):
            nn_task = task_queue.tasks[task_index]
            nn = nn_task.nn
            cycles = []
            for n_tile in range(total_tile):
                cycles.append(self.execution_models.estimate_nn(nn,n_tile+1))
            self.PT.append(cycles)

    def schedule(self, task_queue, target,baseline):
        """
        Get the best allocation
        Args:
            task_queue: the input tasks
            target: ANTT, STP or Fairness
        Returns:
            No returns
        """
        total_tasks = task_queue.total_tasks
        # available tiles
        nTile = self.status.get_available_tile()
        if(baseline):
            allocations = []
            remain = nTile % total_tasks
            each = nTile//total_tasks
            for task_id in range(total_tasks):
                allocations.append(each)
            for i in range(remain):
                allocations[i] += 1
            task_queue.assign_tiles(allocations)
            return 
        # available tiles
        # nTile = self.status.get_available_tile()
        # total tiles
        total_tile = self.acc_cfg["TOTAL_TILE"]
        # genenrate PT
        self.generate_PT(task_queue, total_tile)

        def sample_k():
            """
            Randomly generate legal allocation
            """
            remain_tile = nTile - total_tasks
            tmp = []
            for i in range(total_tasks):
                tmp.append(random.randint(1,100))
            sum_alloc = sum(tmp)
            allocation = [int(remain_tile*x/(sum_alloc)+1) for x in tmp]
            margin = nTile-sum(allocation)
            for _ in range(margin):
                index = random.randint(0,total_tasks-1)
                allocation[index] += 1
            return allocation

        if(target() == "ANTT"):
            # ANTT is a less-is-better metric
            best_v = 1e16
        else:
            # Fairness and STP are higher-is-better
            best_v = 0

        # record the best allocation
        best_a = None
        # cycles running in single mode
        single_cycles = []
        for task_id in range(total_tasks):
            single_cycles.append(self.PT[task_id][total_tile-1])

        for _ in range(self.total_step):
            # random allocating
            allocations = []
            for _ in range(self.K):
                allocation = sample_k()
                allocations.append(allocation)

            for a in allocations:
                multi_cycles = []
                for task_id, allocated_tile in enumerate(a):
                    multi_cycles.append(self.PT[task_id][allocated_tile-1])
                
                # evaluate the allocation
                v = target(single_cycles, multi_cycles)
                # update the best allocation?
                if(target() == "ANTT"):
                    if(v<best_v):
                        best_v = v
                        best_a = a
                else:
                    if(v>best_v):
                        best_v = v
                        best_a = a
        # assign the result of coarse-grained allocation to the task_queue
        task_queue.assign_tiles(best_a)

if __name__ == "__main__":
    import sys
    sys.path.insert(0,"/home/zhou/SDPU_SIM")
    from util import read_acc_config
    from sim.task_queue import TaskQueue
    from nn_dataflow.core import Network
    from nn_dataflow.nns import import_network
    from sim.task_queue import TaskQueue
    from metric import *

    model_names = net_names = ['alex_net','vgg','resnet50','mlp_m','mlp_l','lstm_m','lstm_l']
    TQ = TaskQueue()
    for model_name in model_names:
        nn = import_network(model_name)
        TQ.add_task(nn)
    
    acc_cfg_file = "./accelerator_cfg.yaml"
    acc_cfg = read_acc_config(acc_cfg_file)
    scheduler = SDPU_Scheduler()
    scheduler.load_acc_cfg(acc_cfg)
    scheduler.schedule(TQ,Fairness)