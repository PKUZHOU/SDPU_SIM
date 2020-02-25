from .simobj import SimObj
from .event import Event
from .router import Router

class SRAM(SimObj):
    def __init__(self,name):
        super(SRAM, self).__init__(name)
        self.event = Event(self.processEvent)
        # the depth of the SRAM
        self.depth = 0
        # the width of the SRAM
        self.width = 0
        # the occupied capacity
        self.used = 0

    def get_type(self):
        return "SRAM"

    def set_depth(self, depth):
        self.depth = depth
    
    def set_width(self, width):
        self.width = width

    def read(self, addr):
        raise NotImplementedError
    
    def write(self, addr):
        if(self.used + 1 > self.depth):
            #the SRAM is full
            return -1
        else:
            #write success
            return 0

    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)
        eventQueue.schedule(self.event, 100)
    
    def processEvent(self):
        print("Hello from ", self.name())