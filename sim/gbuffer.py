from .simobj import SimObj
from .event import Event
from .router import Router

class GlobalBuffer(SimObj):
    def __init__(self, name):
        super(GlobalBuffer,self).__init__(name)
        self.event = Event(self.processEvent)
        self.insts = []

    def get_type(self):
        return "GBUF"

    def load_insts(self, insts):
        self.insts += insts

    def configure(self, acc_config):
        router_name = self.name().replace("GBUF","ROUTER-GBUF")
        router = Router(router_name)
        self.add_module(router)

    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)
        eventQueue.schedule(self.event, 100)

    def get_router(self):
        router = self.modules[self.name().replace("GBUF","ROUTER-GBUF")]
        return router

    def connect_to(self, neighbor, direction):
        """
        Set the router to connect the neighbor PEs
        Args: 
            neighbor_pe: the neighbor pe to connect
            direction: "N","S","W","E" 
        Returns:
            No returns
        """
        router = self.get_router()
        neighbor_router = neighbor.get_router()
        router.set_neighbor(neighbor_router, direction)

    def processEvent(self):
        print("Hello from ", self.name())

    