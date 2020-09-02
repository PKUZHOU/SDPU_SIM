from sim.simobj import SimObj
from sim.event import Event
from .defines import *

class Systolic_Array(SimObj):
    def __init__(self,name):
        super(Systolic_Array,self).__init__(name)
        self.eventQueue = None
        self.acc_config = None 

        self.array_size = 0

        # control regs
        self.IA_shape = []
        self.W_shape = []

        self.activated_MACs = 0

    def configure(self,acc_config):
        self.acc_config = acc_config
        self.array_size = acc_config["ARRAY_SIZE"]

    def compute(self):
        assert len(self.IA_shape) == 2
        assert len(self.W_shape) == 2

        # activation
        a_rows = self.IA_shape[0]
        a_cols = self.IA_shape[1]

        # weight
        b_rows = self.W_shape[0]
        b_cols = self.W_shape[1]

        SW = b_cols
        SH = b_rows
        ACC = a_rows

        latency = SW + SH + ACC

        # record the activated MACs
        self.activated_MACs += SH * ACC * SW 

        controller = self.get_global_module(CONTROLLER_)
        self.add_event(controller.finish_gemm, latency)

    def startup(self, eventQueue):
        if(self.eventQueue is None):
            self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)