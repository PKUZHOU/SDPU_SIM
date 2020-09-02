from sim.simobj import SimObj
from sim.event import Event
from sim.sram import SRAM
from .defines import *

class IA_Buffer(SRAM):
    def __init__(self,name):
        super(IA_Buffer,self).__init__(name)
        self.eventQueue = None
        self.acc_config = None 

        self.host_bandwidth = 0

        # control regs
        self.bytes_to_load = 0
        self.loaded_bytes = 0

    def configure(self,acc_config):
        self.acc_config = acc_config
        self.size = acc_config["IA_BUF_SIZE"]
        self.host_bandwidth = acc_config["HOST_BANDWIDTH"]

    def load_from_host(self):
        assert self.host_bandwidth > 0
        bandwidth = self.host_bandwidth * 1e9 # Bps
        freq = self.acc_config["FREQUENCY"]
        cycles = self.bytes_to_load * freq * 1e6 // bandwidth + self.acc_config["HOST_LATENCY"]
        controller = self.get_global_module(CONTROLLER_)
        self.add_event(controller.finish_load_IA,cycles)

    def send_to_host(self):
        pass
    
    def load_from_acc(self):
        pass

    def send_to_array(self):
        pass

    def startup(self, eventQueue):
        if(self.eventQueue is None):
            self.eventQueue = eventQueue

        for module in self.modules.values():
            module.startup(eventQueue)