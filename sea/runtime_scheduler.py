from .defines import *

class Runtime_Scheduler:
    def __init__(self):
        self.acc_cfg = None
        self.free_tiles = []
    
    def load_acc_cfg(self, acc_cfg):
        self.acc_cfg = acc_cfg

    def mapping_fc_layer(self, layer, tile_ids):
        """
        Compile the fully-connected layer
        Args:
            layer: the fc layer shape
        Returns:
            No return
        """
        # raise NotImplementedError
        PE_rows = self.acc_cfg["H_PE"] # the number of rows of each PE array
        PE_cols = self.acc_cfg["W_PE"] # the number of columns of each PE array
        Tile_rows = self.acc_cfg["H_TILE"] # the number of rows of each Tile array
        Tile_cols = self.acc_cfg["W_TILE"] # the number of columns of each Tile array
        
        n_tiles = len(tile_ids)

        N = layer.nifm #input channel
        O = layer.nofm #out channel

        per_tile_N = []
        per_tile_O = []

        O_base = O//n_tiles
        O_remain = O%n_tiles
        # c_base = C//n_tiles
        # c_remain = C%n_tiles
        
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

        for _ in range(n_tiles):
            tile_O = O_base
            tile_N = N
            if(O_remain > 0):
                tile_O += 1
                O_remain -= 1         
            per_tile_N.append(tile_N)
            per_tile_O.append(tile_O)

        instr = {}
        for tile_index, tile_id in enumerate(tile_ids):
            tile_row_id = tile_id //Tile_cols
            tile_col_id = tile_id %Tile_cols

            tile_regs = {}
            # tile_regs[LAYER_TYPE_] = FC_
            #PE level loop
            for pe_row_id in range(PE_rows):
                for pe_col_id in range(PE_cols):
                    pe_name = "{}-{}-{}-{}-{}".format(PE_, tile_row_id, tile_col_id,\
                        pe_row_id, pe_col_id)
                    pe_reg = {}
                    # # calculate the loops per PE 
                    pe_reg[PE_O_] = per_pe_o[pe_col_id]
                    pe_reg[PE_N_] = per_pe_n[pe_row_id]
                    pe_reg[PE_H_] = 1
                    pe_reg[PE_W_] = 1
                    pe_reg[PE_R_] = 1
                    pe_reg[PE_C_] = 1
                    pe_reg[PE_S_] = 1
                    pe_reg[PE_K_] = 1

                    pe_reg[LAYER_TYPE_] = FC_
                    
                    #disable the invalid PEs
                    if(pe_reg[PE_O_] == 0 or\
                        pe_reg[PE_N_] == 0 or\
                        pe_reg[PE_H_] == 0 or\
                        pe_reg[PE_W_] == 0):
                        pe_reg[PE_O_] = 0
                        pe_reg[PE_N_] = 0
                        pe_reg[PE_H_] = 0
                        pe_reg[PE_W_] = 0
                        pe_reg[PE_R_] = 0
                        pe_reg[PE_C_] = 0

                    tile_regs[pe_name] = pe_reg
            
            gbuf_reg = {}    
            gbuf_reg[LAYER_TYPE_] = FC_

            gbuf_name = "{}-{}-{}".format(GBUF_,tile_row_id,tile_col_id)

            gbuf_reg[TILE_O_] = per_tile_O[tile_index] 
            gbuf_reg[TILE_N_] = per_tile_N[tile_index]
            gbuf_reg[TILE_H_] = 1
            gbuf_reg[TILE_W_] = 1
            gbuf_reg[TILE_K_] = 1   
            # set the pe array shape
            gbuf_reg["PE_ROWS"] = PE_rows
            gbuf_reg["PE_COLS"] = PE_cols
            gbuf_reg["LOAD_W"] = True
            tile_regs[gbuf_name] = gbuf_reg
            tile_name = "{}-{}-{}".format(TILE_, tile_row_id, tile_col_id)
            instr[tile_name] = tile_regs 
        return instr


    def mapping_conv_layer(self, layer, tile_ids):

        PE_rows = self.acc_cfg["H_PE"] # the number of rows of each PE array
        PE_cols = self.acc_cfg["W_PE"] # the number of columns of each PE array
        Tile_rows = self.acc_cfg["H_TILE"] # the number of rows of each Tile array
        Tile_cols = self.acc_cfg["W_TILE"] # the number of columns of each Tile array


        n_tiles = len(tile_ids)

        N = layer.nifm #input channel
        W = layer.wifm #input width
        K = layer.hfil #kernel width
        S = layer.htrd #stride
        O = layer.nofm #out channel
        R = layer.hofm #output height
        C = layer.wofm #output width

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

        r_base = R//n_tiles
        r_remain = R%n_tiles
        # c_base = C//n_tiles
        # c_remain = C%n_tiles

        for _ in range(n_tiles):
            tile_r = r_base
            tile_c = C
            if(r_remain > 0):
                tile_r += 1
                r_remain -= 1         
            per_tile_r.append(tile_r)
            per_tile_c.append(tile_c)

        #generate the codes
        #Tile level loop 
        instr = {}
        assigned_first_tile = False
        for tile_index, tile_id in enumerate(tile_ids):
            tile_row_id = tile_id //Tile_cols
            tile_col_id = tile_id %Tile_cols

            tile_regs = {}
            # tile_regs[LAYER_TYPE_] = CONV_
            #PE level loop
            for pe_row_id in range(PE_rows):
                for pe_col_id in range(PE_cols):
                    pe_name = "{}-{}-{}-{}-{}".format(PE_, tile_row_id, tile_col_id,\
                        pe_row_id, pe_col_id)
                    pe_reg = {}
                    # # calculate the loops per PE 
                    pe_reg[PE_O_] = per_pe_o[pe_col_id]
                    pe_reg[PE_N_] = per_pe_n[pe_row_id]
                    pe_reg[PE_H_] = per_tile_r[tile_index] * S + K
                    pe_reg[PE_W_] = per_tile_c[tile_index] * S + K 
                    pe_reg[PE_R_] = per_tile_r[tile_index]
                    pe_reg[PE_C_] = per_tile_c[tile_index]
                    pe_reg[PE_S_] = S
                    pe_reg[PE_K_] = K
                    # pe_reg[LAYER_TYPE_] = CONV_
                    #disable the invalid PEs
                    if(pe_reg[PE_O_] == 0 or\
                        pe_reg[PE_N_] == 0 or\
                        pe_reg[PE_H_] == 0 or\
                        pe_reg[PE_W_] == 0):
                        pe_reg[PE_O_] = 0
                        pe_reg[PE_N_] = 0
                        pe_reg[PE_H_] = 0
                        pe_reg[PE_W_] = 0
                        pe_reg[PE_R_] = 0
                        pe_reg[PE_C_] = 0
                        pe_reg[PE_K_] = 0


                    tile_regs[pe_name] = pe_reg
            
            gbuf_reg = {}    
            gbuf_name = "{}-{}-{}".format(GBUF_,tile_row_id,tile_col_id)

            # gbuf_reg[LAYER_TYPE_] = CONV_
            gbuf_reg[TILE_H_] = per_tile_r[tile_index] * S + K
            gbuf_reg[TILE_W_] = per_tile_c[tile_index] * S + K 
            gbuf_reg[TILE_N_] = N
            gbuf_reg[TILE_O_] = O
            gbuf_reg[TILE_K_] = K

            # set the pe array shape
            gbuf_reg["PE_ROWS"] = PE_rows
            gbuf_reg["PE_COLS"] = PE_cols

            tile_regs[gbuf_name] = gbuf_reg
            if(not assigned_first_tile):
                gbuf_reg["LOAD_W"] = True
                assigned_first_tile = True
            else:
                gbuf_reg["LOAD_W"] = False

            tile_name = "{}-{}-{}".format(TILE_, tile_row_id, tile_col_id)
            instr[tile_name] = tile_regs 

        return instr

    def mapping_layer(self, allocated_tiles, cur_layer):

        # total_task = len(allocated_tiles)
        # per_task_instr = []
        # for task_index in range(total_task):
        #     per_layer_instr = []
        #     nn_task = task_queue.tasks[task_index]
        #     nn = nn_task.layers
        #     for layer_name in nn:
        #         cur_layer = nn[layer_name]
        #         if(cur_layer.type == "Conv"):
        #             instr = self.mapping_conv_layer(cur_layer,allocation[task_index])
        #             # return instr
        #         elif(cur_layer.type=="FC"):
        #             instr = self.mapping_fc_layer(cur_layer,allocation[task_index])
        #         per_layer_instr.append(instr)

            # per_task_instr.append(per_layer_instr)
        if(cur_layer.type == "Conv"):
            instr = self.mapping_conv_layer(cur_layer,allocated_tiles)
            return instr
        elif(cur_layer.type=="FC"):
            instr = self.mapping_fc_layer(cur_layer,allocated_tiles)
            return instr
        # per_layer_instr.append(instr)
        return None