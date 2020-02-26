from .simobj import SimObj
from .event import Event
from .router import Router
from .gbuffer import GlobalBuffer
from .pe import PE
from .nop import NOP

class Tile(SimObj):
    def __init__(self,name):
        super(Tile,self).__init__(name)
        self.eventQueue = None
        self.acc_config = None 
    
    def get_type(self):
        return "TILE"

    def add_NOP(self):
        nop_name = self.name().replace("TILE","NOP")
        nop = NOP(nop_name)
        nop.configure(self.acc_config)
        self.add_module(nop)

    def get_NOP(self):
        nop_name = self.name().replace("TILE","NOP")
        return self.modules[nop_name]

    def get_router(self):
        router = self.get_NOP().get_router()
        return router

    def add_gbuf(self):
        gbuf_name = self.name().replace("TILE","GBUF")
        gbuf = GlobalBuffer(gbuf_name)
        gbuf.configure(self.acc_config)
        self.add_module(gbuf)

    def get_gbuf(self):
        gbuf_name = self.name().replace("TILE","GBUF")
        return self.modules[gbuf_name]

    def add_PEs(self):          
        PE_rows = self.acc_config["H_PE"] # the number of rows of each PE array
        PE_cols = self.acc_config["W_PE"] # the number of columns of each PE array
        #PE level loop
        for pe_row_id in range(PE_rows):
            for pe_col_id in range(PE_cols):
                #add pe
                pe_id_prefix = str(pe_row_id)+"-"+str(pe_col_id)
                pe_name = self.name().replace("TILE","PE") + '-'+pe_id_prefix
                pe = PE(pe_name)
                #configure the PE, eg. SRAM depth and width
                pe.configure(self.acc_config)
                self.add_module(pe)

    def get_PE(self, PE_row, PE_col):
        PE_subfix = "-".join([str(PE_row),str(PE_col)])
        PE_prefix = self.name().replace("TILE","PE")
        PE_name = "-".join([PE_prefix, PE_subfix])           
        return self.modules[PE_name]

    def configure(self,acc_config):
        self.acc_config = acc_config
        #add the router
        self.add_NOP()
        #add the global buffer
        self.add_gbuf()
        #add the PEs
        self.add_PEs()
        #connect this modules
        self.connect_modules()

    def connect_to(self, neighbor, direction):
        """
        Set the router to connect the neighbor tile
        Args: 
            neighbor_tile: the neighbor tile to connect
            direction: "N","S","W","E" 
        Returns:
            No returns
        """
        router = self.get_router() 
        neighbor_router = neighbor.get_router()
        router.set_neighbor(neighbor_router, direction)

    def connect_modules(self):
        """
        Connect the tile level modules
        """
        #connect the PEs
        PE_rows = self.acc_config["H_PE"]
        PE_cols = self.acc_config["W_PE"] 
        for pe_row_id in range(PE_rows):
            for pe_col_id in range(PE_cols):
                pe = self.get_PE(pe_row_id, pe_col_id)
                #N direction
                if(pe_row_id > 0):            
                    N_pe = self.get_PE(pe_row_id, pe_col_id)
                    pe.connect_to(N_pe,'N')
                #E direction
                if(pe_col_id < PE_cols - 1):      
                    E_pe = self.get_PE(pe_row_id, pe_col_id+1)
                    pe.connect_to(E_pe,'E')
                #S direction
                if(pe_row_id < PE_rows - 1):             
                    S_pe = self.get_PE(pe_row_id + 1, pe_col_id)
                    pe.connect_to(S_pe,'S')
                #W direction
                if(pe_col_id > 0):           
                    W_pe = self.get_PE(pe_row_id, pe_col_id-1)
                    pe.connect_to(W_pe,'W')          
        
        #connect the global buffer
        gbuffer_name = self.name().replace("TILE","GBUF")
        gbuffer = self.modules[gbuffer_name]
        #connect to the first PE TODO: more than one routers in a global_buffer
        first_pe = self.get_PE(0,0)
        gbuffer.connect_to(first_pe,'E')
        #connect the first pe to this gbuffer
        first_pe.connect_to(gbuffer,'W')
        #connect the gbuffer with the NOP router
        NOP = self.get_NOP()
        gbuffer.connect_to(NOP,'W')
        #the local port
        NOP.connect_to(gbuffer,'L')

    def load_config_regs(self, tile_config_regs):
        for module_name, config_regs in tile_config_regs.items():
            self.modules[module_name].load_config_regs(config_regs)

    def startup(self, eventQueue):
        self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)

    def processEvent(self):
        print("Hello from ", self.name())