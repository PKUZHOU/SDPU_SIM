from .simobj import SimObj
from .event import Event
from .router import Router
from .sram import SRAM
from .mac_vector import MAC_Vector

class PE(SimObj):
    def __init__(self,name):
        super(PE,self).__init__(name)
        self.eventQueue = None
        #add router
        self.add_module(Router(self.name().replace("PE","ROUTER-PE")))
        #IA buffer
        self.add_module(SRAM(self.name().replace("PE","IA_BUFFER")))
        #W buffer
        self.add_module(SRAM(self.name().replace("PE","W_BUFFER")))
        #ACC buffer
        self.add_module(SRAM(self.name().replace("PE","ACC_BUFFER")))
        #MAC vector
        self.add_module(MAC_Vector(self.name().replace("PE","MAC_VECTOR")))

        self.config_regs = []
    
    def get_type(self):
        return "PE"

    def get_router(self):
        router_name = self.name().replace("PE","ROUTER-PE")
        router = self.modules[router_name]
        return router

    def configure(self, config):
        """
        Configure the parameters of submodules in the PE, including Router, IA_buffer,
        W_buffer, Acc_buffer and MAC_Vector
        Args: 
            config: the dictionary of all the configs
        Returns:
            No returns
        """
        for module_name, module in self.modules.items():
            if("IA_BUFFER" in module_name):
                module.set_depth(config["IA_Buffer_Depth"])
                module.set_width(config["IA_Buffer_Width"])

            elif("W_BUFFER" in module_name):
                module.set_depth(config["W_Buffer_Depth"])
                module.set_width(config["W_Buffer_Width"])

            elif("ACC_BUFFER" in module_name):
                module.set_depth(config["Acc_Buffer_Depth"])
                module.set_width(config["Acc_Buffer_Width"])

            elif("ROUTER" in module_name):
                module.set_latency(config["NOC_Latency"])
                module.set_bandwidth(config["NOC_Bandwidth"])

            elif("MAC_VECTOR" in module_name):
                module.set_lanes(config["Lanes"])

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
    
    def processEvent(self):
        print("Hello from ", self.name())