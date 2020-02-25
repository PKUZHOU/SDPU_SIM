from .simobj import SimObj
from .event import Event
from .router import Router

class Ext_Memory(SimObj):
    def __init__(self,name):
        super(Ext_Memory,self).__init__(name)
        self.event = Event(self.processEvent)
        self.bandwidth = 0
    
    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth

    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)
        # for module in self.modules.values():
        #     module.startup(eventQueue)
        # eventQueue.schedule(self.event, 100)
    
    def processEvent(self):
        print("Hello from ", self.name())