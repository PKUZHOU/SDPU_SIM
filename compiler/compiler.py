from sim.defines import *
import math
class Compiler:
    def __init__(self):
        self.acc_cfg = None
        self.nn = None
        self.compiled_config_regs = []
    def load_acc_cfg(self, acc_cfg):
        """
        Load the accelerator config
        Args:
            acc_cfg: the accelerator config stored in a dict
        Returns:
            no returns
        """
        self.acc_cfg = acc_cfg

    def gen_load_inst(self, src, dst, words):
        load_inst = "{load}-{src}-{dst}-{words}".format(LOAD_, src,dst,words)
        return load_inst
    
    def gen_store_inst(self,src,dst, words):
        store_inst = "{store}-{src}-{dst}-{words}".format(STORE_,src, dst, words)
        return store_inst

    def load_nn(self, nn):
        """
        Load the neural network architecture
        Args:
            nn: neural network (instance of NN class)
        Returns:
            no returns
        """
        self.nn = nn

    def compile_conv_layer(self, layer):
        """
        Compile the convolutional layer
        Args:
            layer: the conv layer shape
        Returns:
            No return
        """
        PE_rows = self.acc_cfg["H_PE"] # the number of rows of each PE array
        PE_cols = self.acc_cfg["W_PE"] # the number of columns of each PE array
        Tile_rows = self.acc_cfg["H_TILE"] # the number of rows of each Tile array
        Tile_cols = self.acc_cfg["W_TILE"] # the number of columns of each Tile array



        Total_tiles = Tile_rows * Tile_cols

        N = layer.nifm #input channel
        W = layer.wifm #input width
        H = W          #input height
        K = layer.hfil #kernel width
        S = layer.htrd #stride
        O = layer.nofm #out channel
        R = layer.hofm #output height
        C = layer.wofm #output width

        # assign some output/input channels to each PE
        # consider the unused PEs
        per_pe_o = []
        per_pe_n = [] 
        o_base = O//PE_cols
        o_remain = O%PE_cols
        n_base = N//PE_cols
        n_remain = N%PE_cols

        for _ in range(PE_cols):
            pe_o = o_base
            if(o_remain > 0):
                pe_o += 1
                o_remain -= 1
            per_pe_o.append(pe_o)
        for _ in range(PE_rows):
            pe_n = n_base
            if(n_remain > 0):
                pe_n += 1
                n_remain -= 1
            per_pe_n.append(pe_n) # input channels per pe

        per_tile_r = []
        per_tile_c = []
        r_base = R//Total_tiles
        r_remain = R%Total_tiles
        c_base = C//Total_tiles
        c_remain = C%Total_tiles
        for _ in range(Total_tiles):
            tile_r = r_base
            tile_c = c_base
            if(r_remain > 0):
                tile_r += 1
                r_remain -= 1
            if(c_remain > 0):
                tile_c += 1
                c_remain -= 1           
            per_tile_r.append(tile_r)
            per_tile_c.append(tile_c)

        #generate the codes
        #Tile level loop 
        config_regs = {}
        for tile_row_id in range(Tile_rows):
            for tile_col_id in range(Tile_cols):
                tile_config_regs = {}
                #PE level loop
                for pe_row_id in range(PE_rows):
                    for pe_col_id in range(PE_cols):
                        pe_name = "{}-{}-{}-{}-{}".format(PE_, tile_row_id, tile_col_id,\
                            pe_row_id, pe_col_id)
                        pe_config_reg = {}
                        # # calculate the loops per PE 
                        pe_config_reg[PE_O_] = per_pe_o[pe_col_id]
                        pe_config_reg[PE_N_] = per_pe_n[pe_row_id]
                        pe_config_reg[PE_H_] = per_tile_r[tile_row_id*Tile_rows+tile_row_id]  * S + K
                        pe_config_reg[PE_W_] = per_tile_c[tile_row_id*Tile_rows+tile_row_id] * S + K 
                        pe_config_reg[PE_R_] = per_tile_r[tile_row_id*Tile_rows+tile_row_id]
                        pe_config_reg[PE_C_] = per_tile_c[tile_row_id*Tile_rows+tile_row_id]
                        pe_config_reg[PE_S_] = S
                        pe_config_reg[PE_K_] = K

                        #disable the invalid PEs
                        if(pe_config_reg[PE_O_] == 0 or\
                           pe_config_reg[PE_N_] == 0 or\
                           pe_config_reg[PE_H_] == 0 or\
                           pe_config_reg[PE_W_] == 0):
                           pe_config_reg[PE_O_] = 0
                           pe_config_reg[PE_N_] = 0
                           pe_config_reg[PE_H_] = 0
                           pe_config_reg[PE_W_] = 0
                           pe_config_reg[PE_R_] = 0
                           pe_config_reg[PE_C_] = 0


                        tile_config_regs[pe_name] = pe_config_reg
                
                gbuf_config_reg = {}    
                gbuf_name = "{}-{}-{}".format(GBUF_,tile_row_id,tile_col_id)

                gbuf_config_reg[TILE_H_] = per_tile_r[tile_row_id*Tile_rows+tile_row_id] * S + K
                gbuf_config_reg[TILE_W_] = per_tile_c[tile_row_id*Tile_rows+tile_row_id] * S + K 
                gbuf_config_reg[TILE_N_] = N
                # set the pe array shape
                gbuf_config_reg["PE_ROWS"] = PE_rows
                gbuf_config_reg["PE_COLS"] = PE_cols

                tile_config_regs[gbuf_name] = gbuf_config_reg
                tile_name = "{}-{}-{}".format(TILE_, tile_row_id, tile_col_id)
                config_regs[tile_name] = tile_config_regs 
                
        return config_regs
        
    def compile_fc_layer(self, layer):
        """
        Compile the fully-connected layer
        Args:
            layer: the fc layer shape
        Returns:
            No return
        """
        raise NotImplementedError

    def compile(self):
        """
        Compile the network
        """
        print("Start compiling ...")
        # Contain the layers at the same level in the DAG

        per_layer_config_regs = []

        cur_names = ('__INPUT__',)
        while(True):
            next_names = ()
            for layer_name in cur_names:
                print("Layer "+ layer_name)
                layer = self.nn[layer_name]
                layer_type = layer.type
                if(layer_type == None):
                    N = layer.nofm
                    H = layer.hofm
                    W = layer.wofm
                    print("Shape ", N, H, W)
                #convolutional layer
                elif(layer_type == "Conv"):
                    per_layer_config_regs.append(self.compile_conv_layer(layer))
                #fully-connected layer
                elif(layer_type == "FC"):
                    pass    
                    # self.compile_fc_layer(layer)
                next_names += self.nn.nexts(layer_name)

            if(next_names[0] == None):
                return per_layer_config_regs
            else:
                #TODO deal with multi output
                cur_names = (next_names[0],)
        return per_layer_config_regs