from .event import EventQueue
from .tile import Tile
from .pe import PE
from .gbuffer import GlobalBuffer
from .router import Router

class System:
    def __init__(self, acc_config):
        self.evetq = EventQueue()
        self.modules = {}
        self.acc_config = acc_config
        self.build_system()

    def build_system(self):
        PE_rows = self.acc_config["H_PE"] # the number of rows of each PE array
        PE_cols = self.acc_config["W_PE"] # the number of columns of each PE array
        Tile_rows = self.acc_config["H_tile"] # the number of rows of each Tile array
        Tile_cols = self.acc_config["W_tile"] # the number of columns of each Tile array

        for tile_row_id in range(Tile_rows):
            for tile_col_id in range(Tile_cols):
                #add tile
                tile_id_prefix = str(tile_row_id)+"-"+str(tile_col_id)
                tile_name = "TILE-" + tile_id_prefix
                tile = Tile(tile_name)
                #PE level loop
                for pe_row_id in range(PE_rows):
                    for pe_col_id in range(PE_cols):
                        #add pe
                        pe_id_prefix = str(pe_row_id)+"-"+str(pe_col_id)
                        pe_name = "PE-"+ tile_id_prefix + '-'+pe_id_prefix
                        pe = PE(pe_name)
                        #TODO: Connect PEs to form array
                        tile.modules[pe_name] = pe
                        
                gbuf_name = "GBUF-" + tile_id_prefix
                gbuf = GlobalBuffer(gbuf_name)
                tile.modules[gbuf_name] = gbuf
                self.modules[tile_name] = tile
                
    def instantiate(self):
        for module in self.modules.values():
            module.startup(self.evetq)

    def load_insts(self, layer_insts):
        for module_name, insts in layer_insts.items():
            module = self.modules[module_name]
            module.load_insts(insts)

    def simulate(self):
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