from sim.event import EventQueue
from sim.simobj import SimObj
from .systolic_array import Systolic_Array
from .defines import *
from .wBuf import Weight_Buffer
from .iaBuf import IA_Buffer
from .accBuf import ACC_Buffer
from .compiler import Compiler
from .controller import Controller


class TPU(SimObj):
    def __init__(self, name):
        super(TPU,self).__init__(name)
        self.evetq = EventQueue()
        self.acc_config = None
        self.task_queue = []
        self.global_modules = {}
        self.compiler = Compiler()
        self.insts = {}

    def load_acc_config(self, acc_config):
        self.acc_config = acc_config
        self.compiler.load_acc_cfg(acc_config)

    def configure_and_add(self, module):
        module.configure(self.acc_config)
        module.set_global_modules(self.global_modules)
        self.add_module(module)

    def build(self):
        """
        Add all the top level modules to the system, and deal with the connections.
        """
        assert self.acc_config is not None
        # Add weight buffer
        self.configure_and_add(Weight_Buffer(W_BUF_))
        # Add IA buffer
        self.configure_and_add(IA_Buffer(IA_BUF_))
        # Add Acc buffer
        self.configure_and_add(ACC_Buffer(ACC_BUF_))
        # Add Systolic arrary
        self.configure_and_add(Systolic_Array(SYSTOLIC_ARRAY_))
        # Add Controller 
        self.configure_and_add(Controller(CONTROLLER_))

    def startup(self):
        """
        Initiate all the modules
        """
        controller = self.get_module(CONTROLLER_)
        controller.load_insts(self.insts)

        for module in self.modules.values():
            module.startup(self.evetq)

    def load_tasks(self, task_queue):
        self.task_queue = task_queue

    def simulate(self):
        """
        Run the simulation. This function fetch events from 
        the evenqueue and run them.
        """
        # First run
        for task in self.task_queue.tasks:
            instructions = self.compiler.compile(task)
            self.insts[task] = instructions
            
        # start up all the modules
        self.startup()

        while(True):
            curTick = self.evetq.nextTick()
            if(curTick < 0):
                return
            # print("Tick: ",curTick)
            self.evetq.setCurTick(curTick)
            cur_events = self.evetq.getEvents(curTick)
            # print(len(cur_events))
            for event in cur_events:
                event.process()
            #all the events within current cycle are processes
            #so we remove these events from the event queue
            self.evetq.removeEvents(curTick)

    def profiling(self):
        systolic_array = self.get_module(SYSTOLIC_ARRAY_)  
        activated_MACs = systolic_array.activated_MACs
        curTick = self.evetq.getCurTick()
        array_size = systolic_array.array_size
        MAC_utilization = activated_MACs / (curTick*array_size*array_size)
        print(MAC_utilization)
