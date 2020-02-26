from .simobj import SimObj
from .event import Event

class MAC_Vector(SimObj):
    def __init__(self,name):
        super(MAC_Vector,self).__init__(name)
        self.event = Event(self.processEvent)
        #add router
        self.lanes = 0

    def get_type(self):
        return "MAC"

    def set_lanes(self, lanes):
        self.lanes = lanes

    def startup(self, eventQueue):
        pass
        # for module in self.modules.values():
        #     module.startup(eventQueue)
        # eventQueue.schedule(self.event, 100)
    def processEvent(self):
        print("Hello from ", self.name())