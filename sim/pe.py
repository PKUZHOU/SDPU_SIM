from .simobj import SimObj
from .event import Event
from .router import Router

class PE(SimObj):
    def __init__(self,name):
        super(PE,self).__init__(name)
        self.event = Event(self.processEvent)
        #add router
        self.add_module(Router(self.obj_name.replace("PE","ROUTER")))
        self.insts = []
        
    def load_insts(self, pe_insts):
        self.insts += pe_insts

    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)
        eventQueue.schedule(self.event, 100)
    
    def processEvent(self):
        print("Hello from ", self.name())