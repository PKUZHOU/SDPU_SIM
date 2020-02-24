from .simobj import SimObj
from .event import Event

class Tile(SimObj):
    def __init__(self,name):
        super(Tile,self).__init__(name)
        self.event = Event(self.processEvent)

    def load_insts(self, tile_insts):
        for module_name, insts in tile_insts.items():
            self.modules[module_name].load_insts(insts)

    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)
        eventQueue.schedule(self.event, 100)
    
    def processEvent(self):
        print("Hello from ", self.name())