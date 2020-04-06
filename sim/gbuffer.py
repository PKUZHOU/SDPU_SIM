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
        self.first_IA = True

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
                first_pe_name = "-".join([self.name().replace(GBUF_,"{}-{}".format(ROUTER_,PE_)),\
                    "{}-{}".format(multicast_pe_col, 0)])
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

    def load_IA(self):
        if(not self.first_IA):
            self.add_event(self.send_IA,1)
            self.first_IA = True
        else:
            IA_Bytes = self.state_regs[IA_BYTES_TO_LOAD_]
            ext_mem = self.global_modules[EXT_MEM_]
            ext_mem.query(IA_Bytes,self.send_IA)

    def load_W(self):
        load_from_ext_mem = self.config_regs["LOAD_W"]
        W_Bytes = self.state_regs[W_BYTES_TO_LOAD_]
        ext_mem = self.global_modules[EXT_MEM_]
        if(load_from_ext_mem):
            ext_mem.query(W_Bytes,self.send_W)
        else:
            # the weight is broadcast
            self.add_event(self.send_W,1)

    def send_IA(self):
        # The PE array shape of this tile
        PE_rows = self.config_regs['PE_ROWS']
        PE_cols = self.config_regs['PE_COLS']
        for pe_row_id in range(PE_rows):
            for pe_col_id in range(PE_cols):
                pe_name = self.name().replace(GBUF_,PE_)\
                    + "-{}-{}".format(pe_row_id, pe_col_id)
                pe = self.global_modules[pe_name]
                pe.add_event(pe.load_IA,1)

    def send_W(self):
        # The PE array shape of this tile
        PE_rows = self.config_regs['PE_ROWS']
        PE_cols = self.config_regs['PE_COLS']
        for pe_row_id in range(PE_rows):
            for pe_col_id in range(PE_cols):
                pe_name = self.name().replace(GBUF_,PE_)\
                    + "-{}-{}".format(pe_row_id, pe_col_id)
                pe = self.global_modules[pe_name]
                pe.add_event(pe.load_W, 1)

    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)
        if(self.eventQueue is None):
            self.eventQueue = eventQueue

        # the IA_bytes to load
        IA_rows = self.config_regs[TILE_H_]
        IA_cols = self.config_regs[TILE_W_]
        IA_n = self.config_regs[TILE_N_]
        IA_bytes = IA_rows * IA_cols * IA_n
        self.state_regs[IA_BYTES_TO_LOAD_] = IA_bytes

        K = self.config_regs[TILE_K_]
        W_o = self.config_regs[TILE_O_]
        W_n = self.config_regs[TILE_N_]
        W_bytes = K*K*W_o*W_n
        self.state_regs[W_BYTES_TO_LOAD_] = W_bytes

        # Load input activation from the external memory 
        self.add_event(self.load_IA,1)
        self.add_event(self.load_W,1)



    