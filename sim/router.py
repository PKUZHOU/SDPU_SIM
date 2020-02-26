from .simobj import SimObj
from .event import Event

class Router(SimObj):
    def __init__(self,name):
        super(Router,self).__init__(name)
        self.latency = 0
        self.bandwidth = 0
        # for ports connecting to the neighbors
        self.connected_routers = {}
        self.eventQueue = None
        self.input_buffer = []

    def get_type(self):
        return "ROUTER"

    def add_to_buffer(self, dst_router, packet_type):
        self.input_buffer.append([dst_router, packet_type])

    def set_latency(self, latency):
        self.latency = latency
    
    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth

    def forward(self):
        for packet in self.input_buffer:
            dst_router, packet_type = packet
            #TODO: Multicast
            if(dst_router == self.name()):
                #here is the destination
                #TODO: deal with the packet
                # print(self.name()+"received!")
                return
            splited_cur_name = self.name().split("-")
            splited_dst_name = dst_router.split("-")

            cur_level = splited_cur_name[1]
            dst_level = splited_dst_name[1]

            cur_tile_row = int(splited_cur_name[2])
            cur_tile_col = int(splited_cur_name[3])
            dst_tile_row = int(splited_dst_name[2])
            dst_tile_col = int(splited_dst_name[3])

            in_same_tile = cur_tile_row == dst_tile_row\
                        and cur_tile_col == dst_tile_col

            if(cur_level == "PE"):
                cur_row = int(splited_cur_name[4])
                cur_col = int(splited_cur_name[5])
                # PE to PE
                if(dst_level == "PE"):

                    dst_row = int(splited_dst_name[4])
                    dst_col = int(splited_dst_name[5])
                    # if the two PEs are in the same tile
                    if(in_same_tile):
                        # X-Y Router
                        if(dst_col > cur_col):
                            next_hop_col = cur_col + 1
                            next_hop_row = cur_row
                            
                        elif(dst_col < cur_col):
                            next_hop_col = cur_col - 1
                            next_hop_row = cur_row

                        else:
                            if(dst_row > cur_row):
                                next_hop_col = cur_col
                                next_hop_row = cur_row + 1

                            elif(dst_row < cur_row):
                                next_hop_col = cur_col
                                next_hop_row = cur_row - 1

                        next_hop_name = "ROUTER-PE-{}-{}-{}-{}".format(cur_tile_row, cur_tile_col,\
                                next_hop_row, next_hop_col)
                    else:
                        # the two PEs are in different tiles
                        raise NotImplementedError
                    
                # PE to GBUF
                elif(dst_level == "GBUF"):
                    if(in_same_tile):
                        if(cur_col > 0):
                            next_hop_col = cur_col - 1
                            next_hop_row = cur_row
                            next_hop_name = "ROUTER-PE-{}-{}-{}-{}".format(cur_tile_row, cur_tile_col,\
                                cur_row, next_hop_col)
                        elif(cur_row > 0):
                            next_hop_col = cur_col
                            next_hop_row = cur_row - 1
                            next_hop_name = "ROUTER-PE-{}-{}-{}-{}".format(cur_tile_row, cur_tile_col,\
                                cur_row, next_hop_col)
                        else:
                            next_hop_name = "ROUTER-GBUF-{}-{}".format(cur_tile_row, cur_tile_col)
                    else:
                        raise NotImplementedError

            elif(cur_level == "GBUF"):
                if(dst_level == "GBUF"):
                    raise NotImplementedError
                # GBUF to PE
                elif(dst_level == "PE"):        
                    if(in_same_tile):
                        next_hop_name = "ROUTER-PE-{}-{}-{}-{}".format(cur_tile_row, cur_tile_col,0,0)
                    else:
                        raise NotImplementedError

            next_hop_router = self.connected_routers[next_hop_name]
            next_hop_router.add_to_buffer(dst_router, packet_type)
            when = self.eventQueue.curTick + self.latency
            event = Event(next_hop_router.forward)
            self.eventQueue.schedule(event, when)
        self.input_buffer.clear()


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
        self.connected_routers[router.name()] = router

    def startup(self, eventQueue):
        self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)
    
    def processEvent(self):
        print("Hello from ", self.name())