from .simobj import SimObj
from .event import Event
from .router import Router
from .sram import SRAM
from .defines import *

class GlobalBuffer(SimObj):
    def __init__(self, name):
        super(GlobalBuffer,self).__init__(name)
        self.config_regs = None
        self.eventQueue = None
        self.state_regs = {}
        self.acc_config = None
    def get_type(self):
        return GBUF_

    def load_config_regs(self, config_regs):
        self.config_regs = config_regs

    def handle_local_data_func(self, local_buffer):
        router = self.get_router()
        for packet in local_buffer:
            _, _, packet_type = packet
            if(packet_type == EXT_MEM_DATA_):
                # TODO: write to local IA buffer
                input_buffer = self.get_sram("INPUT")
                # a flit = 64bit
                input_buffer.write(8)
                multicast_pe_col = self.state_regs["MULTICAST_PE_COL"] 
                # multicast the input to a PE col
                first_pe_name = "-".join([self.name().replace(GBUF_,"{}-{}".format(ROUTER_,PE_)),"{}-{}".format(multicast_pe_col, 0)])
                router.add_to_input_buffer(router.name(), first_pe_name, MULTICAST_, 1 ) 
                router.add_event(router.forward, 1)
                total_pe_cols = self.acc_config["H_PE"]
                self.state_regs["MULTICAST_PE_COL"] = (multicast_pe_col + 1)% total_pe_cols

    def add_sram(self, sram_type, acc_config):
        """
        Args: 
            sram_type: "INPUT","WEIGHT","OUTPUT"
        """
        sram_name = self.name().replace(GBUF_,"{}-{}-{}".format(SRAM_,GBUF_,sram_type.upper()))
        sram = SRAM(sram_name)
        sram.set_depth(acc_config[sram_type + '_SRAM_DEPTH'])
        sram.set_width(acc_config[sram_type + '_SRAM_WIDTH'])
        self.add_module(sram)

    def get_sram(self, sram_type):
        """
        Args: 
            sram_type: "INPUT","WEIGHT","OUTPUT"
        """
        sram_name = self.name().replace(GBUF_,"{}-{}-{}".format(SRAM_,GBUF_,sram_type.upper()))
        return self.modules[sram_name]

    def get_router(self):
        router = self.modules[self.name().replace(GBUF_,"{}-{}".format(ROUTER_,GBUF_))]
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

    def configure(self, acc_config):
        """
        configure the modules in the GBUF, including srams, router
        Args:
            acc_config: The dict of the accelerator config
        """
        self.acc_config = acc_config
        # add the router
        router_name = self.name().replace(GBUF_,"{}-{}".format(ROUTER_,GBUF_))
        router = Router(router_name)
        router.set_local_data_handler(self.handle_local_data_func)
        self.add_module(router)
        # add the input sram
        self.add_sram('INPUT', acc_config)
        self.add_sram('WEIGHT',acc_config)
        self.add_sram('OUTPUT',acc_config)

    def send_packet(self, dst, packet_type):
        # local router
        router = self.get_router()
        src = router.name()
        # send the packet through local router
        # take 4 cycles to shape the packet and write to the router buffer
        router.add_to_input_buffer( src, dst, packet_type, send_delay = 4)
        
        #router.add_event(router.forward, latency = 4)

    def multicast_inputs(self):
        """
        Read the input data from input sram and send them to different PE rows through NOC
        """
        input_sram = self.get_sram("INPUT")
        # multicast to each PE row
        PE_rows = self.config_regs['PE_ROWS']
        for row in range(PE_rows):
            bytes_in_word = 8
            ret = input_sram.read(bytes_in_word)
            if(ret == 0):
                # the first PE of each row
                dst_router_name = self.name().replace(GBUF_,"{}-{}".format(ROUTER_,PE_))\
                    + "-{}-{}".format(row, 0)
                self.send_packet(dst_router_name, MULTICAST_)
            else:
                return
        # start another pass in the next tick 
        multicast_event = Event(self.multicast_inputs)
        curTick = self.eventQueue.curTick
        self.eventQueue.schedule(multicast_event,curTick + 1)

    def unicast_weights(self):
        """
        Read the weight data from weight sram and send them to different PE through NOC
        """
        weight_sram = self.get_sram("WEIGHT")
        # unicast to each PE
        # TODO: consider the NOC bandwidth
        PE_rows = self.config_regs['PE_ROWS']
        PE_cols = self.config_regs['PE_COLS']
        for row in range(PE_rows):
            for col in range(PE_cols):
                bytes_in_word = 8
                ret = weight_sram.read(bytes_in_word)
                if(ret == 0):
                    # the first PE of each row
                    dst_router_name = self.name().replace(GBUF_,"{}-{}".format(ROUTER_,PE_))\
                        + "-{}-{}".format(row,col)
                    self.send_packet(dst_router_name, UNICAST_)
                else:
                    return
        # start another pass in the next tick 
        multicast_event = Event(self.multicast_inputs)
        curTick = self.eventQueue.curTick
        self.eventQueue.schedule(multicast_event,curTick + 1)

    def load_IA(self):
        if(self.state_regs[IA_BYTES_TO_LOAD_] > 0):
            # The total input activation bytes of this tile
            # One cache line size 64B per transaction
            # Send read request to memory controller 
            tile_row_idx = int(self.name().split("-")[1])
            tile_col_idx = int(self.name().split("-")[2])
            total_row = int(self.acc_config["H_TILE"])
            total_col = int(self.acc_config["W_TILE"])

            if tile_row_idx <= total_row//2:
                target_row = 0
            else:
                target_row = total_row - 1
            if tile_col_idx <= total_col//2:
                target_col = 0
            else:
                target_col = total_col -1

            dst_router = "{}-{}-{}-{}".format(ROUTER_,EXT_MEM_, target_row, target_col)
            self.send_packet(dst = dst_router, packet_type = MEM_READ_REQ_)
            self.state_regs[IA_BYTES_TO_LOAD_] -= CACHE_LINE_BYTES_
            self.add_event(self.load_IA, latency = 1)

    def send_IA(self):
        # The PE array shape of this tile

        # PE_rows = self.config_regs['PE_ROWS']
        # PE_cols = self.config_regs['PE_COLS']
        # input_sram = self.get_sram("INPUT")
        # assert(ret == 0)
        # weight_sram = self.get_sram("WEIGHT")
        # assert(ret == 0)
        raise NotImplementedError

    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)
        self.eventQueue = eventQueue

        # the IA_bytes to load
        IA_rows = self.config_regs[TILE_H_]
        IA_cols = self.config_regs[TILE_W_]
        IA_n = self.config_regs[TILE_N_]
        IA_bytes = IA_rows * IA_cols * IA_n
        self.state_regs[IA_BYTES_TO_LOAD_] = IA_bytes
        self.state_regs["MULTICAST_PE_COL"] = 0
        # Load input activation from the external memory 
        self.add_event(self.load_IA,1)



    