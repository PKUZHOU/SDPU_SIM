from sim.simobj import SimObj
from sim.event import Event
from sim.sram import SRAM
from .defines import *

class Weight_Buffer(SRAM):
    def __init__(self,name):
        super(Weight_Buffer,self).__init__(name)
        self.eventQueue = None
        self.acc_config = None 
        self.DDR_bandwidth = 0
        self.DDR_latency = 0

        # FIFO
        self.weight_fifo = []

        # Control regs
        self.bytes_to_load = 0
        self.feteched = 0

    def configure(self,acc_config):
        self.acc_config = acc_config
        self.DDR_bandwidth = acc_config["DDR_BANDWIDTH"]
        self.DDR_latency = acc_config["DDR_LATENCY"]

    def load_from_ddr(self):
        assert self.DDR_bandwidth > 0
        
        bandwidth = self.DDR_bandwidth * 1e9 # Bps
        freq = self.acc_config["FREQUENCY"]
        cycles = self.bytes_to_load * freq * 1e6 // bandwidth + self.DDR_latency
        
        controller = self.get_global_module(CONTROLLER_)
        self.add_event(controller.finish_load_W,cycles)

    def startup(self, eventQueue):
        if(self.eventQueue is None):
            self.eventQueue = eventQueue

        for module in self.modules.values():
            module.startup(eventQueue)