from .simobj import SimObj
from .event import Event
from .router import Router

class NOP(SimObj):
    def __init__(self, name):
        super(NOP,self).__init__(name)
        self.eventQueue = None

    def get_type(self):
        return "NOP"

    def configure(self, acc_config):
        router_name = self.name().replace("NOP","NOP-ROUTER")
        router = Router(router_name)
        router.configure(acc_config,"NOP")
        self.add_module(router)

    def get_router(self):
        router = self.modules[self.name().replace("NOP","NOP-ROUTER")]
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

    def startup(self, eventQueue):
        self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)
        

    def processEvent(self):
        print("Hello from ", self.name())

    