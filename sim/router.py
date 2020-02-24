from .simobj import SimObj
from .event import Event

class Router(SimObj):
    def __init__(self,name):
        super(Router,self).__init__(name)
        self.event = Event(self.processEvent)

    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)
        eventQueue.schedule(self.event, 100)
    
    def processEvent(self):
        print("Hello from ", self.name())