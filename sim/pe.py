from .simobj import SimObj
from .event import Event
from .router import Router
from .sram import SRAM
from .mac_vector import MAC_Vector

class PE(SimObj):
    def __init__(self,name):
        super(PE,self).__init__(name)
        self.eventQueue = None
        self.config_regs = []
    
    def get_type(self):
        return "PE"

    def get_router(self):
        router_name = self.name().replace("PE","ROUTER-PE")
        router = self.modules[router_name]
        return router

    def get_sram(self, sram_type):
        """
        Args: 
            sram_type:  "IA_BUFFER","W_BUFFER","ACC_BUFFER"
        """
        pre_fix = "SRAM-" + sram_type
        sram_name = self.name().replace("PE",pre_fix)
        return self.modules[sram_name]

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
        IA_buffer = SRAM(self.name().replace("PE","SRAM-IA_BUFFER"))
        IA_buffer.set_depth(config["IA_Buffer_Depth"])
        IA_buffer.set_width(config["IA_Buffer_Width"])
        #W buffer
        W_buffer = SRAM(self.name().replace("PE","SRAM-W_BUFFER"))
        W_buffer.set_depth(config["W_Buffer_Depth"])
        W_buffer.set_width(config["W_Buffer_Width"])
        #ACC buffer
        ACC_buffer = SRAM(self.name().replace("PE","SRAM-ACC_BUFFER"))
        ACC_buffer.set_depth(config["Acc_Buffer_Depth"])
        ACC_buffer.set_width(config["Acc_Buffer_Width"])
        #MAC vector
        MAC_vector = MAC_Vector(self.name().replace("PE","SRAM-MAC_VECTOR"))
        MAC_vector.set_lanes(config["Lanes"])
        #add router
        router = Router(self.name().replace("PE","ROUTER-PE"))
        router.set_latency(config["NOC_Latency"])
        router.set_bandwidth(config["NOC_Bandwidth"])

        self.add_module(router)
        router.set_neighbor(IA_buffer,'L')
        router.set_neighbor(W_buffer,'L')
        router.set_neighbor(ACC_buffer,'L')
        self.add_module(router)
        self.add_module(IA_buffer)
        self.add_module(W_buffer)
        self.add_module(ACC_buffer)
        self.add_module(MAC_vector)

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