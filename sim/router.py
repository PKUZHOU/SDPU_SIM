from .simobj import SimObj
from .event import Event
from .defines import *
import time

class Router(SimObj):
    def __init__(self,name):
        super(Router,self).__init__(name)
        self.latency = 0
        self.bandwidth = 0
        # for ports connecting to the neighbors
        self.connected = {}
        # input buffer is to hold the packets to send
        self.input_buffer = []
        # local buffer is to hold the packets to receive
        self.local_buffer = []
        # handle the received packet
        self.handle_local_data_func = None

    def set_local_data_handler(self, handler):
        self.handle_local_data_func = handler

    def local_processing(self):
        if(self.handle_local_data_func is not None):
            self.handle_local_data_func(self.local_buffer)
        self.local_buffer.clear()

    def get_type(self):
        return ROUTER_

    def add_to_input_buffer(self, src_router, dst_router, packet_type, send_delay):
        """
        Add the packet to the input buffer
        Args:
            src_router: the source router name
            dst_router: the destination router name
            packet_type: the type of the packet
            send_delay: the number of cycles before the packet is truly sent
        """
        curTick = self.eventQueue.curTick
        send_time = curTick + send_delay
        self.input_buffer.append([src_router, dst_router, packet_type, send_time])
        self.add_event(self.forward, send_delay)

    def set_latency(self, latency):
        self.latency = latency
    
    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth

    def get_next_hop_pe_to_pe(self, cur_tile_pos, cur_pe_pos, dst_pe_pos):
        cur_tile_row, cur_tile_col = cur_tile_pos
        cur_pe_row, cur_pe_col = cur_pe_pos
        dst_pe_row, dst_pe_col = dst_pe_pos
        # if the two PEs are in the same tile
        # X-Y Router
        if(dst_pe_col > cur_pe_col):
            next_hop_col = cur_pe_col + 1
            next_hop_row = cur_pe_row
            
        elif(dst_pe_col < cur_pe_col):
            next_hop_col = cur_pe_col - 1
            next_hop_row = cur_pe_row

        else:
            if(dst_pe_row > cur_pe_row):
                next_hop_col = cur_pe_col
                next_hop_row = cur_pe_row + 1

            elif(dst_pe_row < cur_pe_row):
                next_hop_col = cur_pe_col
                next_hop_row = cur_pe_row - 1

        next_hop_name = "{}-{}-{}-{}-{}-{}".format(ROUTER_, PE_, cur_tile_row,\
                        cur_tile_col, next_hop_row, next_hop_col)
        return next_hop_name

    def get_next_hop_pe_to_gbuf(self, cur_tile_pos, cur_pe_pos):
        cur_tile_row, cur_tile_col = cur_tile_pos
        cur_pe_row, cur_pe_col = cur_pe_pos
        
        if(cur_pe_col > 0):
            next_hop_col = cur_pe_col - 1
            next_hop_row = cur_pe_row
            next_hop_name = "{}-{}-{}-{}-{}-{}".format(ROUTER_, PE_, cur_tile_row, cur_tile_col, next_hop_row, next_hop_col)
        elif(cur_pe_row > 0):
            next_hop_col = cur_pe_col
            next_hop_row = cur_pe_row - 1
            next_hop_name = "{}-{}-{}-{}-{}-{}".format(ROUTER_, PE_,cur_tile_row, cur_tile_col, next_hop_row, next_hop_col)
        else:
            # direct to the gbuf
            next_hop_name = "{}-{}-{}-{}".format(ROUTER_, GBUF_,cur_tile_row, cur_tile_col)
        return next_hop_name
    
    def get_next_hop_nop_to_nop(self, cur_tile_pos, dst_tile_pos):
        cur_tile_row, cur_tile_col = cur_tile_pos
        dst_tile_row, dst_tile_col = dst_tile_pos

        if(dst_tile_col > cur_tile_col):
            next_hop_col = cur_tile_col + 1
            next_hop_row = cur_tile_row
            
        elif(dst_tile_col < cur_tile_col):
            next_hop_col = cur_tile_col - 1
            next_hop_row = cur_tile_row

        else:
            if(dst_tile_row > cur_tile_row):
                next_hop_col = cur_tile_col
                next_hop_row = cur_tile_row + 1

            elif(dst_tile_row < cur_tile_row):
                next_hop_col = cur_tile_col
                next_hop_row = cur_tile_row - 1
        next_hop_name = "{}-{}-{}-{}".format(ROUTER_,NOP_,next_hop_row,next_hop_col)
        return next_hop_name

    def cleared_input_buffer(self):
        new_buffer = []
        for packet in self.input_buffer:
            send_time = packet[3]
            if send_time > self.eventQueue.curTick:
                new_buffer.append(packet)
        return new_buffer

    def forward(self):
        # a = time.time()
        unused_ports = []
        for key in self.connected.keys():
            unused_ports.append(key)

        for packet_idx, packet in enumerate(self.input_buffer):

            # TODO: take the NOC bandwidth into consideration 
            # check if this packet is ready to be forwarded this time
            send_time = packet[3]
            if(send_time != self.eventQueue.curTick):
                continue
            # the packet is ready to send 
            src_router, dst_router, packet_type, _ = packet

            # decode the current router name and the destination router name
            splited_cur_name = self.name().split("-")
            splited_dst_name = dst_router.split("-")
            #EXT_MEM, Tile, GBUF or PE ?
            cur_level = splited_cur_name[1]
            dst_level = splited_dst_name[1]
            #current tile row and col
            cur_tile_row = int(splited_cur_name[2])
            cur_tile_col = int(splited_cur_name[3])
            #dst tile row and col
            dst_tile_row = int(splited_dst_name[2])
            dst_tile_col = int(splited_dst_name[3])
            # the in_same_tile flag indicates that the dst and cur router is in the same tile
            in_same_tile = cur_tile_row == dst_tile_row\
                        and cur_tile_col == dst_tile_col

            if(dst_router == self.name()):
                self.local_buffer.append([src_router, dst_router, packet_type])
                self.add_event(self.local_processing, latency = 1)
                continue

            else:               
                # the package is not for current router
                # so forward it 
                if(cur_level == PE_):
                    cur_pe_row = int(splited_cur_name[4])
                    cur_pe_col = int(splited_cur_name[5])
                    # PE to PE
                    if(dst_level == PE_):
                        cur_tile_pos = [cur_tile_row, cur_tile_col]
                        cur_pe_pos = [cur_pe_row, cur_pe_col]
                        if(in_same_tile):
                            dst_pe_row = int(splited_dst_name[4])
                            dst_pe_col = int(splited_dst_name[5])
                            dst_pe_pos = [dst_pe_row, dst_pe_col]
                            next_hop_name = self.get_next_hop_pe_to_pe(cur_tile_pos,cur_pe_pos,dst_pe_pos)
                        else:
                            next_hop_name = self.get_next_hop_pe_to_gbuf(cur_tile_pos,cur_pe_pos)
                    # PE to GBUF
                    elif(dst_level == GBUF_):
                        if(in_same_tile):
                            next_hop_name = self.get_next_hop_pe_to_gbuf(cur_tile_pos,cur_pe_pos)
                        else:
                            next_hop_name = self.get_next_hop_pe_to_gbuf(cur_tile_pos,cur_pe_pos)
                    # PE to MEM
                    elif(dst_level == EXT_MEM_):
                        next_hop_name = self.get_next_hop_pe_to_gbuf(cur_tile_pos, cur_pe_pos)

                elif(cur_level == GBUF_):
                    # GBUF to GBUF
                    if(dst_level == GBUF_):
                        # send to NOP
                        next_hop_name = "{}-{}-{}-{}".format(ROUTER_, NOP_, cur_tile_row, cur_tile_col)
                    
                    # GBUF to PE
                    elif(dst_level == PE_):        
                        if(in_same_tile):
                            next_hop_name = "{}-{}-{}-{}-{}-{}".format(ROUTER_, PE_, cur_tile_row,\
                                cur_tile_col,0,0)
                        else:
                            # send to NOP
                            next_hop_name = "{}-{}-{}-{}".format(ROUTER_, NOP_, cur_tile_row, cur_tile_col)          

                    # GBUF to MEM
                    elif(dst_level == EXT_MEM_):
                        # send to NOP
                        next_hop_name = "{}-{}-{}-{}".format(ROUTER_, NOP_, cur_tile_row, cur_tile_col)
                            
                elif(cur_level == EXT_MEM_):
                    # only can send to NOP
                    next_hop_name = "{}-{}-{}-{}".format(ROUTER_,NOP_,cur_tile_row,cur_tile_col)

                elif(cur_level == NOP_):
                    # NOP to MEM
                    if(dst_level == EXT_MEM_):
                        if(in_same_tile):
                            # direct to the memory
                            next_hop_name = "{}-{}-{}-{}".format(ROUTER_,EXT_MEM_,cur_tile_row,cur_tile_col)
                        else:
                            # forward to other NOP 
                            cur_tile_pos = [cur_tile_row,cur_tile_col]
                            dst_tile_pos = [dst_tile_row,dst_tile_col]
                            next_hop_name = self.get_next_hop_nop_to_nop(cur_tile_pos, dst_tile_pos)
                    # NOP to PE
                    elif(dst_level == PE_):
                        if(in_same_tile):
                            # first send to the GBUF
                            next_hop_name = "{}-{}-{}-{}".format(ROUTER_,GBUF_,cur_pe_row,cur_pe_col)
                        else:
                            # forward to other NOP
                            cur_tile_pos = [cur_tile_row,cur_tile_col]
                            dst_tile_pos = [dst_tile_row,dst_tile_col]
                            next_hop_name = self.get_next_hop_nop_to_nop(cur_tile_pos, dst_tile_pos)
                    # NOP to GBUF
                    elif(dst_level == GBUF_):
                        if(in_same_tile):
                            next_hop_name = "{}-{}-{}-{}".format(ROUTER_,GBUF_,cur_tile_row,cur_tile_col)
                        else:
                            # forward to other NOP
                            cur_tile_pos = [cur_tile_row,cur_tile_col]
                            dst_tile_pos = [dst_tile_row,dst_tile_col]
                            next_hop_name = self.get_next_hop_nop_to_nop(cur_tile_pos, dst_tile_pos)
                
            if next_hop_name in self.connected.keys():
                if(next_hop_name in unused_ports):
                    next_hop_router = self.connected[next_hop_name]
                    next_hop_router.add_to_input_buffer(src_router, dst_router, packet_type, self.latency)
                    # unused_ports.remove(next_hop_name)
                else:
                    pass
                    # next_hop_router.add_to_input_buffer(src_router, dst_router, packet_type, self.latency + 1)
                    # self.add_to_input_buffer(src_router, dst_router, next_hop_name, 1)
                    # self.input_buffer[packet_idx][-1] += 1
      
        self.input_buffer = self.cleared_input_buffer()
        # print(time.time() - a )
        # if(len(self.input_buffer)>0):
        #     self.add_event(self.forward, 1)

    def configure(self, acc_configs, type):
        """
        Configure the router, set the latency and bandwidth parameters
        Args:
            acc_configs: the dict of configs
            type: string, "NOC" or "NOP" 
        Returns:
            No returns
        """
        if(type == NOC_):
            latency = acc_configs["NOC_LATENCY"]
            bandwidth = acc_configs["NOC_BANDWIDTH"]
            self.set_latency(latency)
            self.set_bandwidth(bandwidth)
        elif(type == NOP_):
            latency = acc_configs["NOP_LATENCY"]
            bandwidth = acc_configs["NOP_BANDWIDTH"]
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
        self.connected[router.name()] = router

    def startup(self, eventQueue):
        if(self.eventQueue is None):
            self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)