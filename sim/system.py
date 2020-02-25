from .event import EventQueue
from .tile import Tile
from .pe import PE
from .gbuffer import GlobalBuffer
from .router import Router
from .ext_mem import Ext_Memory

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
        Tile_rows = self.acc_config["H_tile"] # the number of rows of each Tile array
        Tile_cols = self.acc_config["W_tile"] # the number of columns of each Tile array
        
        #Tile level loop
        for tile_row_id in range(Tile_rows):
            for tile_col_id in range(Tile_cols):
                #add tile
                tile_id_prefix = str(tile_row_id)+"-"+str(tile_col_id)
                tile_name = "TILE-" + tile_id_prefix
                tile = Tile(tile_name)
                tile.configure(self.acc_config)
                self.add_module(tile)
        
        #add external memory
        ext_mem_name = "EXT_MEM"
        ext_mem = Ext_Memory(ext_mem_name)
        ext_mem.set_bandwidth(self.acc_config["Ext_Bandwidth"])
        self.add_module(ext_mem)
    
        #connect the modules
        self.connect_modules()


    def get_TILE(self, TILE_row, TILE_col):
        TILE_subfix = "-".join([str(TILE_row),str(TILE_col)])
        TILE_name = "-".join(["TILE", TILE_subfix])           
        return self.modules[TILE_name]


    def connect_modules(self):
        """
        Connect the top level modules of the system, mainly the routing topology
        """
        Tile_rows = self.acc_config["H_tile"]
        Tile_cols = self.acc_config["W_tile"] 
        for tile_row_id in range(Tile_rows):
            for tile_col_id in range(Tile_cols):
                tile = self.get_TILE(tile_row_id, tile_col_id)  
                #N direction
                if(tile_row_id > 0):  
                    N_tile = self.get_TILE(tile_row_id - 1, tile_col_id)         
                    tile.connect_to(N_tile,'N')
                #E direction
                if(tile_col_id < Tile_cols - 1):
                    E_tile = self.get_TILE(tile_row_id, tile_col_id + 1)               
                    tile.connect_to(E_tile,'E')
                #S direction
                if(tile_row_id < Tile_rows - 1):
                    S_tile = self.get_TILE(tile_row_id + 1, tile_col_id)              
                    tile.connect_to(S_tile,'S')
                #W direction
                if(tile_col_id > 0):          
                    W_tile = self.get_TILE(tile_row_id, tile_col_id - 1)
                    tile.connect_to(W_tile,'W')              

    def instantiate(self):
        for module in self.modules.values():
            module.startup(self.evetq)

    def load_insts(self, layer_insts):
        """
        Load the compiled instructions to the corresponding modules
        Args:
            layer_insts: dict{} the compiled instructions of a layer
                the key are the module names
        Returns:
            No returns
        """
        for module_name, insts in layer_insts.items():
            module = self.modules[module_name]
            module.load_insts(insts)

    def simulate(self):
        """
        Run the simulation. This function fetch evens from 
        the evenqueue and run them.
        """
        while(True):
            curTick = self.evetq.nextTick()
            if(curTick < 0):
                print("Simulation finished!")
                return
            print("Tick: ",curTick)
            self.evetq.setCurTick(curTick)
            cur_events = self.evetq.getEvents(curTick)
            for event in cur_events:
                event.process()
            #all the events within current cycle are processes
            #so we remove these events from the event queue
            self.evetq.removeEvents(curTick)