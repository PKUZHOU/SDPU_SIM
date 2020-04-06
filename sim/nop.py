from .simobj import SimObj
from .event import Event
from .router import Router
from .defines import * 

class NOP(SimObj):
    def __init__(self, name):
        super(NOP,self).__init__(name)
        self.eventQueue = None

    def get_type(self):
        return NOP_

    def configure(self, acc_config):
        router_name = self.name().replace(NOP_,"{}-{}".format(ROUTER_,NOP_))
        router = Router(router_name)
        router.configure(acc_config,NOP_)
        self.add_module(router)

    def get_router(self):
        router = self.modules[self.name().replace(NOP_,"{}-{}".format(ROUTER_,NOP_ ))]
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
        if(self.eventQueue is None):
            self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)
        
    