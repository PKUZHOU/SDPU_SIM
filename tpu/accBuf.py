from sim.simobj import SimObj
from sim.event import Event
from sim.sram import SRAM
from .defines import *

class ACC_Buffer(SRAM):
    def __init__(self,name):
        super(ACC_Buffer,self).__init__(name)
        self.eventQueue = None
        self.acc_config = None 

    def configure(self,acc_config):
        self.acc_config = acc_config
        self.size = acc_config["ACC_BUF_SIZE"]

    def startup(self, eventQueue):
        if(self.eventQueue is None):
            self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)