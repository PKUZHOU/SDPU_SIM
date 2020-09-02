from .defines import *
import math
class Compiler:
    def __init__(self):
        self.acc_cfg = None
        self.tag = 0

    def load_acc_cfg(self, acc_cfg):
        """
        Load the accelerator config
        Args:
            acc_cfg: the accelerator config stored in a dict
        Returns:
            no returns
        """
        self.acc_cfg = acc_cfg

    def gen_load_inst(self, type, bytes, tag):
        load_inst = "{}-{}-{}-{}".format(LOAD_, type, bytes, tag)
        return load_inst
    
    def gen_store_inst(self, type, bytes, tag):
        store_inst = "{}-{}-{}-{}".format(STORE_, type, bytes, tag)
        return store_inst

    def gen_gemm_inst(self, a_rows, a_cols, b_rows, b_cols, tag):
        gemm_inst = "{}-{}-{}-{}-{}-{}".format(GEMM_,a_rows, a_cols, b_rows, b_cols, tag)
        return gemm_inst

    def partition_and_generate_gemm_inst(self,  gemm_array_a_rows, gemm_array_a_cols, \
        gemm_array_b_rows, gemm_array_b_cols, array_size):
        
        instructions = []


        # a is the input matrix
        a_tile_rows_full = gemm_array_a_rows // array_size
        a_tile_cols_full = gemm_array_a_cols // array_size
        
        a_tile_rows_margin = gemm_array_a_rows % array_size
        a_tile_cols_margin = gemm_array_a_cols % array_size

        # b is the weight matrix
        b_tile_rows_full = gemm_array_b_rows // array_size
        b_tile_cols_full = gemm_array_b_cols // array_size

        b_tile_rows_margin = gemm_array_b_rows % array_size
        b_tile_cols_margin = gemm_array_b_cols % array_size
     
        for b_tile_col in range(b_tile_cols_full):
            for b_tile_row in range(b_tile_rows_full):

                load_W_inst = self.gen_load_inst("W", array_size * array_size, self.tag)
                instructions.append(load_W_inst)

                gemm_inst = self.gen_gemm_inst(gemm_array_a_rows,array_size,array_size,array_size, self.tag)
                instructions.append(gemm_inst)

                # for _ in range(a_tile_rows_full):
                #     gemm_inst = self.gen_gemm_inst(gemm_array_a_cols,array_size,array_size,array_size, self.tag)
                #     instructions.append(gemm_inst)

                # for _ in range(a_tile_rows_full):
                #     gemm_inst = self.gen_gemm_inst(array_size,array_size,array_size,array_size, self.tag)
                #     instructions.append(gemm_inst)
                
                # if(a_tile_rows_margin > 0):
                #     gemm_inst = self.gen_gemm_inst(a_tile_rows_margin, array_size, array_size,array_size, self.tag)
                #     instructions.append(gemm_inst)

                self.tag += 1

            if(b_tile_rows_margin > 0):
                
                load_W_inst = self.gen_load_inst("W", b_tile_rows_margin * array_size, self.tag)
                instructions.append(load_W_inst)

                gemm_inst = self.gen_gemm_inst(gemm_array_a_rows, a_tile_cols_margin, b_tile_rows_margin,array_size, self.tag)
                instructions.append(gemm_inst)

                self.tag += 1
                # for _ in range(a_tile_rows_full):
                #     gemm_inst = self.gen_gemm_inst(array_size, a_tile_cols_margin, b_tile_rows_margin,array_size, self.tag)
                #     instructions.append(gemm_inst)

                # if(a_tile_rows_margin > 0):
                #     gemm_inst = self.gen_gemm_inst(a_tile_rows_margin, a_tile_cols_margin, b_tile_rows_margin,array_size, self.tag)
                #     instructions.append(gemm_inst)

        if(b_tile_cols_margin > 0):
            for b_tile_row in range(b_tile_rows_full):
                load_W_inst = self.gen_load_inst("W", array_size * b_tile_cols_margin, self.tag)
                instructions.append(load_W_inst)

                gemm_inst = self.gen_gemm_inst(gemm_array_a_rows,array_size,array_size,b_tile_cols_margin, self.tag)
                instructions.append(gemm_inst)

                # for _ in range(a_tile_rows_full):
                #     gemm_inst = self.gen_gemm_inst(array_size,array_size,array_size,b_tile_cols_margin, self.tag)
                #     instructions.append(gemm_inst)
                
                # if(a_tile_rows_margin > 0):
                #     gemm_inst = self.gen_gemm_inst(a_tile_rows_margin, array_size, array_size,b_tile_cols_margin, self.tag)
                #     instructions.append(gemm_inst)

                self.tag += 1

            if(b_tile_rows_margin > 0):

                load_W_inst = self.gen_load_inst("W", b_tile_rows_margin * b_tile_cols_margin, self.tag)
                instructions.append(load_W_inst)

                gemm_inst = self.gen_gemm_inst(gemm_array_a_rows,b_tile_rows_margin,b_tile_rows_margin,b_tile_cols_margin, self.tag)
                instructions.append(gemm_inst)

                # for _ in range(a_tile_rows_full):
                #     gemm_inst = self.gen_gemm_inst(array_size, a_tile_cols_margin, b_tile_rows_margin,b_tile_cols_margin, self.tag)
                #     instructions.append(gemm_inst)

                # if(a_tile_rows_margin > 0):
                #     gemm_inst = self.gen_gemm_inst(a_tile_rows_margin, a_tile_cols_margin, b_tile_rows_margin,b_tile_cols_margin, self.tag)
                #     instructions.append(gemm_inst)
                
                self.tag += 1

        return instructions


    def compile_conv_layer(self, layer, isFirst = False):
        """
        Compile the convolutional layer
        Args:
            layer: the conv layer shape
        Returns:
            No return
        """

        array_size = self.acc_cfg["ARRAY_SIZE"]
        instructions = []

        N = layer.nifm #input channel
        W = layer.wifm #input width
        H = W          #input height
        K = layer.hfil #kernel width
        S = layer.htrd #stride
        O = layer.nofm #out channel
        R = layer.hofm #output height
        C = layer.wofm #output width

        gemm_array_a_rows = R*C
        gemm_array_a_cols = K*K*N

        gemm_array_b_rows = K*K*N
        gemm_array_b_cols = O

        if(isFirst):
            load_IA_inst = self.gen_load_inst("IA",N*W*H, self.tag)
            instructions.append(load_IA_inst)

        instructions += self.partition_and_generate_gemm_inst(gemm_array_a_rows,gemm_array_a_cols, \
            gemm_array_b_rows,gemm_array_b_cols, array_size)

        return instructions

    def compile_fc_layer(self, layer, isFirst = False):
        """
        Compile the fully-connected layer
        Args:
            layer: the fc layer shape
        Returns:
            No return
        """
        N = layer.nifm #input channel
        O = layer.nofm #out channel

        array_size = self.acc_cfg["ARRAY_SIZE"]
        instructions = []

        gemm_array_a_rows = 1
        gemm_array_a_cols = N

        gemm_array_b_rows = N
        gemm_array_b_cols = O

        if(isFirst):
            load_IA_inst = self.gen_load_inst("IA",N, self.tag)
            instructions.append(load_IA_inst)

        instructions += self.partition_and_generate_gemm_inst(gemm_array_a_rows,gemm_array_a_cols, \
            gemm_array_b_rows,gemm_array_b_cols, array_size)

        return instructions
        

    def compile(self, task):
        """
        Compile the network
        """
        # print("Start compiling ...")
        instructions = []
        while(True):
            cur_layer = task.get_next_layer()
            if(cur_layer == -1):
                return instructions

            isFirst = False

            if(len(instructions) == 0):
                isFirst = True

            if(cur_layer.type == "Conv"):
                instructions += self.compile_conv_layer(cur_layer,isFirst)
            
            elif(cur_layer.type == "FC"):
                instructions += self.compile_fc_layer(cur_layer,isFirst)

        return instructions
