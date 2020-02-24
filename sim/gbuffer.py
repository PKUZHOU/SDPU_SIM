from .simobj import SimObj
from .event import Event

class GlobalBuffer(SimObj):
    def __init__(self, name):
        super(GlobalBuffer,self).__init__(name)
        self.event = Event(self.processEvent)
        self.insts = []
    def load_insts(self, insts):
        self.insts += insts

    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)
        eventQueue.schedule(self.event, 100)
    
    def processEvent(self):
        print("Hello from ", self.name())

    