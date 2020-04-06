from .simobj import SimObj
from .event import Event
from .router import Router
from .sram import SRAM
from .mac_vector import MAC_Vector
from .defines import *
import math

class PE(SimObj):
    def __init__(self,name):
        super(PE,self).__init__(name)
        self.eventQueue = None
        self.config_regs = []
        self.acc_config = None
        self.status = {}
        self.status["IA_Loaded"] = False
        self.status["W_Loaded"] = False

    def finish_compute(self):
        tile_row, tile_col, _, _ = self.name().split("-")[1:]
        tile_name = "{}-{}-{}".format(TILE_,tile_row,tile_col)
        tile = self.global_modules[tile_name]
        tile.finished_PEs += 1
        tile.add_event(tile.check_finish,10)

    def compute(self):
        if(self.status["IA_Loaded"] and self.status["W_Loaded"]):
            out_channels = self.config_regs[PE_O_]
            input_channels = self.config_regs[PE_N_]
            # input_w = self.config_regs[PE_W_]
            # input_h = self.config_regs[PE_H_]
            out_channel_passes = math.ceil(out_channels/8.)
            input_channel_passes = math.ceil(input_channels/8.)
            r = self.config_regs[PE_R_]
            c = self.config_regs[PE_C_]
            k = self.config_regs[PE_K_]
            passes = k * k * r * c * out_channel_passes * input_channel_passes + 1
            # print(passes)
            self.add_event(self.finish_compute, passes)
            self.status["IA_Loaded"] = False
            self.status["W_Loaded"] = False

    def load_IA(self):
        IA_rows = self.config_regs[PE_H_]
        IA_cols = self.config_regs[PE_W_]
        IA_n = self.config_regs[PE_N_]
        IA_Bytes = IA_rows * IA_cols * IA_n
        
        NOC_BW = self.acc_config["NOC_BANDWIDTH"]
        Freq = self.acc_config["FREQUENCY"]
        BW = NOC_BW * 1e9
        Freq = Freq * 1e6
        latency = int(Freq * IA_Bytes/BW)+1
        # print(latency)
        self.status["IA_Loaded"] = True
        self.add_event(self.compute,latency)

    def load_W(self):
        K = self.config_regs[PE_K_]
        O = self.config_regs[PE_O_]
        N = self.config_regs[PE_N_]
        W_Bytes = K*K*O*N
        # print("W",W_Bytes)
        NOC_BW = self.acc_config["NOC_BANDWIDTH"]
        Freq = self.acc_config["FREQUENCY"]
        BW = NOC_BW * 1e9
        Freq = Freq * 1e6
        latency = int(Freq * W_Bytes/BW)+1
        self.status["W_Loaded"] = True
        self.add_event(self.compute,latency)

    def get_type(self):
        return PE_

    def add_sram(self, sram_type, acc_config):
        """
        Args: 
            sram_type:  "IA_BUFFER","W_BUFFER","ACC_BUFFER"
        """
        sram_name = self.name().replace(PE_,"-".join([SRAM_, sram_type]))
        sram = SRAM(sram_name)
        sram.set_depth(acc_config["{}_DEPTH".format(sram_type)])
        sram.set_width(acc_config["{}_WIDTH".format(sram_type)])
        self.add_module(sram)
        return sram

    def get_sram(self, sram_type):
        """
        Args: 
            sram_type:  "IA_BUFFER","W_BUFFER","ACC_BUFFER"
        """
        sram_name = self.name().replace(PE_,"-".join([SRAM_, sram_type]))
        return self.modules[sram_name]
    
    def add_MAC_vector(self, acc_config):
        MAC_vector_name = self.name().replace(PE_,MAC_VECTOR_)
        MAC_vector = MAC_Vector(MAC_vector_name)
        MAC_vector.set_lanes(acc_config["LANE"])
        return MAC_vector

    def get_vector_MAC(self):
        MAC_vector_name = self.name().replace(PE_,MAC_VECTOR_)
        return self.modules[MAC_vector_name]

    def configure(self, config):
        """
        Configure the parameters of submodules in the PE, including Router, IA_buffer,
        W_buffer, Acc_buffer and MAC_Vector
        Args: 
            config: the dictionary of all the configs
        Returns:
            No returns
        """
        self.acc_config = config
        #IA buffer
        IA_buffer = self.add_sram(IA_BUFFER_,config)
        #W buffer
        W_buffer = self.add_sram(W_BUFFER_,config)
        #ACC buffer
        ACC_buffer = self.add_sram(ACC_BUFFER_,config)
        #MAC vector
        self.add_MAC_vector(config)
        #Router
        
    def load_config_regs(self, pe_config_regs):
        """
        Load the config_regs
        Args:
            pe_config_regs: A list containing all the config_regs
        Returns: 
            No returns
        """
        self.config_regs = pe_config_regs

    def startup(self, eventQueue):
        if(self.eventQueue is None):
            self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)