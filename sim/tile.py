from .simobj import SimObj
from .event import Event
from .router import Router
from .gbuffer import GlobalBuffer
from .pe import PE
from .nop import NOP
from .defines import *

class Tile(SimObj):
    def __init__(self,name):
        super(Tile,self).__init__(name)
        self.eventQueue = None
        self.acc_config = None 
        self.status = {}
        self.finished_tiles = None
        self.finished_PEs = 0 

    def get_type(self):
        return TILE_

    def add_gbuf(self):
        gbuf_name = self.name().replace(TILE_,GBUF_)
        gbuf = GlobalBuffer(gbuf_name)
        gbuf.set_global_modules(self.global_modules)
        gbuf.configure(self.acc_config)
        self.add_module(gbuf)

    def get_gbuf(self):
        gbuf_name = self.name().replace(TILE_,GBUF_)
        return self.modules[gbuf_name]

    def add_PEs(self):          
        PE_rows = self.acc_config["H_PE"] # the number of rows of each PE array
        PE_cols = self.acc_config["W_PE"] # the number of columns of each PE array
        #PE level loop
        for pe_row_id in range(PE_rows):
            for pe_col_id in range(PE_cols):
                #add pe
                pe_name = self.name().replace(TILE_,PE_) + \
                    '-{}-{}'.format(pe_row_id, pe_col_id)
                pe = PE(pe_name)
                #configure the PE, eg. SRAM depth and width
                pe.set_global_modules(self.global_modules)
                pe.configure(self.acc_config)
                self.add_module(pe)

    def get_PE(self, PE_row, PE_col):
        PE_subfix = "{}-{}".format(PE_row,PE_col)
        PE_prefix = self.name().replace(TILE_,PE_)
        PE_name = "{}-{}".format(PE_prefix, PE_subfix)           
        return self.modules[PE_name]

    def configure(self,acc_config):
        self.acc_config = acc_config
        #add the router
        # self.add_NOP()
        #add the global buffer
        self.add_gbuf()
        #add the PEs
        self.add_PEs()
        #connect this modules
        # self.connect_modules()

    def load_config_regs(self, tile_config_regs):
        for module_name, config_regs in tile_config_regs.items():
            self.modules[module_name].load_config_regs(config_regs)

    def startup(self, eventQueue):
        if(self.eventQueue is None):
            self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)

    def check_finish(self):
        if(self.finished_PEs == self.acc_config["TOTAL_PE"]):
            self.finished_tiles.append(self.name())
            self.finished_PEs = 0