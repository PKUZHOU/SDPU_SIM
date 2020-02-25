from .simobj import SimObj
from .event import Event

class Router(SimObj):
    def __init__(self,name):
        super(Router,self).__init__(name)
        self.event = Event(self.processEvent)
        self.latency = 0
        self.bandwidth = 0
        # for ports connecting to the neighbors
        self.N_port = None
        self.W_port = None
        self.S_port = None
        self.E_port = None
        #local modules which communicate with this router.
        self.Local_port = None

    def get_type(self):
        return "ROUTER"
        
    def set_latency(self, latency):
        self.latency = latency
    
    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth

    def configure(self, acc_configs, type):
        """
        Configure the router, set the latency and bandwidth parameters
        Args:
            acc_configs: the dict of configs
            type: string, "NOC" or "NOP" 
        Returns:
            No returns
        """
        if(type == "NOC"):
            latency = acc_configs["NOC_Latency"]
            bandwidth = acc_configs["NOC_Bandwidth"]
            self.set_latency(latency)
            self.set_bandwidth(bandwidth)
        elif(type == "NOP"):
            latency = acc_configs["NOP_Latency"]
            bandwidth = acc_configs["NOP_Bandwidth"]
            self.set_latency(latency)
            self.set_bandwidth(bandwidth)

    def set_neighbor(self, router, direction):
        """
        Set the connections to each neighbor router
        Args:
            port: other router
            direction: N W S E, in character
        Returns:
            No returns
        """ 
        if(direction == 'N'):
            self.N_port = router
        elif(direction == 'W'):
            self.W_port = router
        elif(direction == 'S'):
            self.S_port = router
        elif(direction == 'E'):
            self.E_port = router
        
        elif(direction == "L"):
            self.Local_port = router

    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)
        # eventQueue.schedule(self.event, 100)
    
    def processEvent(self):
        print("Hello from ", self.name())