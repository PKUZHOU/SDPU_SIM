class Compiler:
    def __init__(self):
        self.acc_cfg = None
        self.nn = None
        self.compiled_inst = []
    def load_acc_cfg(self, acc_cfg):
        """
        Load the accelerator config
        Args:
            acc_cfg: the accelerator config stored in a dict
        Returns:
            no returns
        """
        self.acc_cfg = acc_cfg

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
        Tile_rows = self.acc_cfg["H_tile"] # the number of rows of each Tile array
        Tile_cols = self.acc_cfg["W_tile"] # the number of columns of each Tile array

        Total_tiles = Tile_rows*Tile_cols

        N = layer.nifm #input channel
        W = layer.wifm #input width
        H = W          #input height
        K = layer.hfil #kernel width
        S = layer.htrd #stride
        O = layer.nofm #out channel
        R = layer.hofm #output height
        C = layer.wofm #output width

        per_pe_o = O//PE_cols #  out channels per pe
        per_pe_n = max(N//PE_rows,1) # input channels per pe
        #TODO deal with the margine 
        
        per_tile_R = max(R//(Total_tiles),1) # output rows per tile
        #TODO deal with the margine

        Lanes = self.acc_cfg["Lanes"]
        Vector_width = self.acc_cfg["Vector_Width"]
        #generate the codes
        #Tile level loop 
        insts = {}
        for tile_row_id in range(Tile_rows):
            for tile_col_id in range(Tile_cols):
                tile_id_prefix = str(tile_row_id)+"-"+str(tile_col_id)
                tile_insts = {}
                #PE level loop
                for pe_row_id in range(PE_rows):
                    for pe_col_id in range(PE_cols):
                        pe_id_prefix = str(pe_row_id)+"-"+str(pe_col_id)
                        pe_name = "PE-"+ tile_id_prefix + '-'+pe_id_prefix
                        pe_insts = []
                        # calculate the loops per PE 
                        n_loops = max(per_pe_o//Lanes, 1) * max(per_pe_n//Vector_width, 1)\
                            * per_tile_R * C * K * K
                        # TODO: more details e.g partial sum
                        pe_insts.append("Loop_"+str(n_loops))
                        tile_insts[pe_name] = pe_insts
                
                gbuf_insts = []    
                gbuf_name = "GBUF-"+tile_id_prefix
                # multicast the inputs 
                gbuf_insts.append("Multicast_"+str(per_pe_n*W*H))
                # unicast the weights
                gbuf_insts.append("Unicast_"+str(per_pe_n*per_pe_o))
                tile_insts[gbuf_name] = gbuf_insts
                tile_name = "TILE-" + tile_id_prefix
                insts[tile_name] = tile_insts 
        
        return insts
        
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

        per_layer_insts = []

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
                    per_layer_insts.append(self.compile_conv_layer(layer))
                #fully-connected layer
                elif(layer_type == "FC"):
                    pass    
                    # self.compile_fc_layer(layer)
                next_names += self.nn.nexts(layer_name)

            if(next_names[0] == None):
                return per_layer_insts
            else:
                #TODO deal with multi output
                cur_names = (next_names[0],)
        return per_layer_insts