from .event import EventQueue
from .tile import Tile
from .pe import PE
from .gbuffer import GlobalBuffer
from .router import Router
from .ext_mem import Ext_Memory
from .defines import *

class System:
    def __init__(self, acc_config):
        self.evetq = EventQueue()
        self.modules = {}
        self.acc_config = acc_config
        self.build_system()

    def add_module(self, module):
        """
        Add module to the system (top level)
        Args: 
            module: SimObj(), the module to add
        Returns:
            No returns  
        """
        self.modules[module.name()] = module

    def build_system(self):
        """
        Add all the top level modules to the system, and deal with the connections.
        """
        #read the Tile and PE array shape from configs.
        Tile_rows = self.acc_config["H_TILE"] # the number of rows of each Tile array
        Tile_cols = self.acc_config["W_TILE"] # the number of columns of each Tile array
        
        #Tile level loop
        for tile_row_id in range(Tile_rows):
            for tile_col_id in range(Tile_cols):
                #add tile
                tile_name = "{}-{}-{}".format(TILE_, tile_row_id, tile_col_id)
                tile = Tile(tile_name)
                tile.configure(self.acc_config)
                self.add_module(tile)
        
        #add external memory
        ext_mem_name = EXT_MEM_
        ext_mem = Ext_Memory(ext_mem_name)
        ext_mem.configure(self.acc_config)
        self.add_module(ext_mem)

        #connect the modules
        self.connect_modules()

    def get_ext_mem(self):
        return self.modules[EXT_MEM_]

    def get_tile(self, tile_row, tile_col):
        tile_name = "{}-{}-{}".format(TILE_,tile_row, tile_col)           
        return self.modules[tile_name]

    def connect_modules(self):
        """
        Connect the top level modules of the system, mainly the routing topology
        """
        Tile_rows = self.acc_config["H_TILE"]
        Tile_cols = self.acc_config["W_TILE"] 
        for tile_row_id in range(Tile_rows):
            for tile_col_id in range(Tile_cols):
                tile = self.get_tile(tile_row_id, tile_col_id)  
                #N direction
                if(tile_row_id > 0):  
                    N_tile = self.get_tile(tile_row_id - 1, tile_col_id)         
                    tile.connect_to(N_tile,'N')
                #E direction
                if(tile_col_id < Tile_cols - 1):
                    E_tile = self.get_tile(tile_row_id, tile_col_id + 1)               
                    tile.connect_to(E_tile,'E')
                #S direction
                if(tile_row_id < Tile_rows - 1):
                    S_tile = self.get_tile(tile_row_id + 1, tile_col_id)              
                    tile.connect_to(S_tile,'S')
                #W direction
                if(tile_col_id > 0):          
                    W_tile = self.get_tile(tile_row_id, tile_col_id - 1)
                    tile.connect_to(W_tile,'W')     
                #EXT_MEM
                if(tile_row_id == 0 and tile_col_id == 0):
                    ext_mem = self.get_ext_mem()
                    corner_tile = self.get_tile(tile_row_id, tile_col_id)
                    corner_tile.connect_to(ext_mem, 'W')
                    ext_mem.connect_to(corner_tile,'E')
                if(tile_row_id == 0 and tile_col_id == Tile_cols - 1):
                    ext_mem = self.get_ext_mem()
                    corner_tile = self.get_tile(tile_row_id, tile_col_id)
                    corner_tile.connect_to(ext_mem, 'E')
                    ext_mem.connect_to(corner_tile,'W')
                if(tile_row_id == Tile_rows-1 and tile_col_id == 0):
                    ext_mem = self.get_ext_mem()
                    corner_tile = self.get_tile(tile_row_id, tile_col_id)
                    corner_tile.connect_to(ext_mem, 'S')
                    ext_mem.connect_to(corner_tile,'N')
                if(tile_row_id == Tile_rows-1 and tile_col_id == Tile_cols - 1):
                    ext_mem = self.get_ext_mem()
                    corner_tile = self.get_tile(tile_row_id, tile_col_id)
                    corner_tile.connect_to(ext_mem, 'N')
                    ext_mem.connect_to(corner_tile,'S')
                    
                    

    def instantiate(self):
        """
        Initiate all the modules
        """
        for module in self.modules.values():
            module.startup(self.evetq)

    def load_config_regs(self, layer_config_regs):
        """
        Load the compiled config_regs to the corresponding modules
        Args:
            layer_config_regs: dict{} the compiled config_regs of a layer
                the key are the module names
        Returns:
            No returns
        """
        for module_name, config_regs in layer_config_regs.items():
            module = self.modules[module_name]
            module.load_config_regs(config_regs)

    def simulate(self):
        """
        Run the simulation. This function fetch evens from 
        the evenqueue and run them.
        """
        while(True):
            curTick = self.evetq.nextTick()
            if(curTick < 0):
                return
            print("Tick: ",curTick)
            self.evetq.setCurTick(curTick)
            cur_events = self.evetq.getEvents(curTick)
            # print(len(cur_events))
            for event in cur_events:
                event.process()
            #all the events within current cycle are processes
            #so we remove these events from the event queue
            self.evetq.removeEvents(curTick)
