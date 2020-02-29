from .simobj import SimObj
from .event import Event
from .router import Router
import math 
from .defines import *

class SRAM(SimObj):
    def __init__(self,name):
        super(SRAM, self).__init__(name)
        self.eventQueue = None
        # the depth of the SRAM
        self.depth = 0
        # the width of the SRAM
        self.width = 0
        # the occupied capacity
        self.used = 0

    def get_type(self):
        return SRAM_

    def set_depth(self, depth):
        self.depth = depth
    
    def set_width(self, width):
        self.width = width

    def read(self, read_bytes = 0, decremental = True):
        read_depth = math.ceil(read_bytes/self.width)
        if(decremental and self.used-read_depth > 0):
            self.used -= read_depth
            return 0
        else:
            return -1

    def empty(self):
        if(self.used == 0):
            return True
        return False

    def write(self,  write_bytes = 0, incremental = True ):
        occupied_depth = math.ceil(write_bytes/self.width)
        if(incremental):
            if(self.used + occupied_depth > self.depth):
                #the SRAM is full
                return -1
            else:
                self.used += occupied_depth
                #write success
                return 0
        else:
            if(occupied_depth > self.depth):
                return -1
            else:
                return 0

    def startup(self, eventQueue):
        self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)
        # eventQueue.schedule(self.event, 100)
    