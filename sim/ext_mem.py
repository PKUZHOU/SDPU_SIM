from .simobj import SimObj
from .event import Event
from .router import Router
from .defines import * 

class Ext_Memory(SimObj):
    def __init__(self,name):
        super(Ext_Memory,self).__init__(name)
        self.bandwidth = 0
        self.channels = 0
        self.acc_config = None

    def add_router(self, acc_config):
        router = Router(self.name().replace(EXT_MEM_,"-".join([ROUTER_, EXT_MEM_])))
        router.set_latency(acc_config["NOC_LATENCY"])
        router.set_bandwidth(acc_config["NOC_BANDWIDTH"])
        router.handle_local_data_func = self.handle_local_data_func
        self.add_module(router)
        return router
    
    def handle_local_data_func(self, local_buffer):
        router = self.get_router()
        for packet in local_buffer:
            src, dst, packet_type = packet
            if(packet_type == MEM_READ_REQ_):
                for i in range (CACHE_LINE_BYTES_//8):
                    router.add_to_input_buffer(router.name, src, i + self.acc_config, EXT_MEM_DATA_, ['EXT_MEM_LATENCY'])

    def get_router(self):
        router_name = self.name().replace(EXT_MEM_,"-".join([ROUTER_, EXT_MEM_]))
        return self.modules[router_name]

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth

    def set_channels(self, channels):
        self.channels = channels
    
    def configure(self, acc_config):
        self.acc_config = acc_config
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