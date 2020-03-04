from .simobj import SimObj
from .event import Event
from .router import Router
from .sram import SRAM
from .mac_vector import MAC_Vector
from .defines import *

class PE(SimObj):
    def __init__(self,name):
        super(PE,self).__init__(name)
        self.eventQueue = None
        self.config_regs = []
    
    def process_router_data(self, local_buffer):
        for package in local_buffer:
            #fill the weight buffer and sram buffer
            IA_buffer = self.get_sram(IA_BUFFER_)
            W_buffer = self.get_sram(W_BUFFER_)
            
            if(package == MULTICAST_):
                IA_buffer.write(8) # 8 bytes
            elif(package == UNICAST_):
                W_buffer.write(8)

        # invoke the computing
        if(IA_buffer.remaining_bytes() > 64 and W_buffer.remaining_bytes() > 64):
            # vector_MAC = self.get_vector_MAC()
            event = Event(self.compute)
            curTick = self.eventQueue.curTick
            self.eventQueue.schedule(event, curTick + 1)
    
    def compute(self):
        pass

    def get_type(self):
        return PE_

    def add_router(self, acc_config):
        router = Router(self.name().replace(PE_,"-".join([ROUTER_, PE_])))
        router.set_latency(acc_config["NOC_LATENCY"])
        router.set_bandwidth(acc_config["NOC_BANDWIDTH"])
        router.handle_local_data_func = self.process_router_data
        self.add_module(router)
        return router

    def get_router(self):
        router_name = self.name().replace(PE_,"-".join([ROUTER_, PE_]))
        router = self.modules[router_name]
        return router

    def add_sram(self, sram_type, acc_config):
        """
        Args: 
            sram_type:  "IA_BUFFER","W_BUFFER","ACC_BUFFER"
        """
        sram_name = self.name().replace(PE_,"-".join([SRAM_, sram_type]))
        sram = SRAM(sram_name)
        sram.set_depth(acc_config["{}_DEPTH".format(sram_type)])
        sram.set_width(acc_config["{}_WIDTH".format(sram_type)])
        self.add_module(sram)
        return sram

    def get_sram(self, sram_type):
        """
        Args: 
            sram_type:  "IA_BUFFER","W_BUFFER","ACC_BUFFER"
        """
        sram_name = self.name().replace(PE_,"-".join([SRAM_, sram_type]))
        return self.modules[sram_name]
    
    def add_MAC_vector(self, acc_config):
        MAC_vector_name = self.name().replace(PE_,MAC_VECTOR_)
        MAC_vector = MAC_Vector(MAC_vector_name)
        MAC_vector.set_lanes(acc_config["LANES"])
        return MAC_vector

    def get_vector_MAC(self):
        MAC_vector_name = self.name().replace(PE_,MAC_VECTOR_)
        return self.modules[MAC_vector_name]

    def configure(self, config):
        """
        Configure the parameters of submodules in the PE, including Router, IA_buffer,
        W_buffer, Acc_buffer and MAC_Vector
        Args: 
            config: the dictionary of all the configs
        Returns:
            No returns
        """
        #IA buffer
        IA_buffer = self.add_sram(IA_BUFFER_,config)
        #W buffer
        W_buffer = self.add_sram(W_BUFFER_,config)
        #ACC buffer
        ACC_buffer = self.add_sram(ACC_BUFFER_,config)
        #MAC vector
        self.add_MAC_vector(config)
        #Router
        
        router = self.add_router(config)
        router.set_neighbor(IA_buffer,'L')
        router.set_neighbor(W_buffer,'L')
        router.set_neighbor(ACC_buffer,'L')

    def connect_to(self, neighbor, direction):
        """
        Set the router to connect the neighbor tile
        Args: 
            neighbor_pe: the neighbor pe to connect
            direction: "N","S","W","E" 
        Returns:
            No returns
        """
        router = self.get_router()
        neighbor_router = neighbor.get_router()
        router.set_neighbor(neighbor_router, direction)
        
    def load_config_regs(self, pe_config_regs):
        """
        Load the config_regs
        Args:
            pe_config_regs: A list containing all the config_regs
        Returns: 
            No returns
        """
        self.config_regs = pe_config_regs

    def startup(self, eventQueue):
        self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)