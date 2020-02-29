from .simobj import SimObj
from .event import Event
from .router import Router
from .defines import * 

class Ext_Memory(SimObj):
    def __init__(self,name):
        super(Ext_Memory,self).__init__(name)
        self.bandwidth = 0
        self.channels = 0

    def add_router(self, acc_config):
        router = Router(self.name().replace(EXT_MEM_,"-".join([ROUTER_, EXT_MEM_])))
        router.set_latency(acc_config["NOC_LATENCY"])
        router.set_bandwidth(acc_config["NOC_BANDWIDTH"])
        self.add_module(router)
        return router
    
    def get_router(self):
        router_name = self.name().replace(EXT_MEM_,"-".join([ROUTER_, EXT_MEM_]))
        return self.modules[router_name]

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth

    def set_channels(self, channels):
        self.channels = channels
    
    def configure(self, acc_config):
        self.set_bandwidth(acc_config["EXT_MEM_BANDWIDTH"])
        self.set_channels(acc_config["EXT_MEM_CHANNELS"])
        self.add_router(acc_config)

    def connect_to(self, neighbor, direction):
        """
        Set the router to connect the neighbor tile
        Args: 
            neighbor_tile: the neighbor tile to connect
            direction: "N","S","W","E" 
        Returns:
            No returns
        """
        router = self.get_router() 
        neighbor_router = neighbor.get_router()
        router.set_neighbor(neighbor_router, direction)
        
    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)