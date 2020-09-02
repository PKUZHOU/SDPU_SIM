import math
class ExecutionModels:
    def __init__(self):
        self.nLane = 0
        self.nAU = 0
        self.nPE = 0
        self.BW_tile = 0

    def set_acc_config(self, acc_config):
        self.nAU = acc_config["AU"]
        self.nLane = acc_config["LANE"]
        freq = acc_config["FREQUENCY"] * 1e6
        BW = acc_config["EXT_MEM_BANDWIDTH"] * 1e9
        total_Tile = acc_config["TOTAL_TILE"]
        self.BW_tile = BW/freq/total_Tile
        self.nPE = acc_config["TOTAL_PE"]


    def t_conv_compute(self, M,N,R,C,K,nTile):
        Tr = R
        Tc = math.ceil(float(C)/nTile)
        Tn = self.nLane
        Tm = math.ceil(float(M*N)/self.nPE*self.nLane)

        cycles = Tr * Tc * K * K * \
            math.ceil(float(Tn)/self.nLane)*math.ceil(float(Tm)/self.nAU)
        return cycles

    def t_conv_load(self, M,N, R,C, K, nTile, alpha, beta):
        Tr = R
        Tc = math.ceil(float(C)/nTile)
        cycles = (Tr * Tc * N * alpha + K * K * N * M * beta)/self.BW_tile
        return cycles

    def t_fc_compute(self, M, N,nTile):
        Tm = math.ceil(float(M)/nTile)
        Tn = math.ceil(float(N)/self.nPE)
        cycle = math.ceil(float(Tn)/self.nLane)*math.ceil(float(Tm)/self.nAU)
        return cycle       
    
    def t_fc_load(self, M, N, nTile, alpha):
        Tm = math.ceil(float(M)/nTile)
        cycle = (N * alpha + N * Tm)/self.BW_tile
        return cycle



    def estimate_layer(self, layer, ntile):
        if(layer.type == "Conv"):
            N = layer.nifm #input channel
            W = layer.wifm #input width
            H = W          #input height
            K = layer.hfil #kernel width
            M = layer.nofm #out channel
            R = layer.hofm #output height
            C = layer.wofm #output width
            t_compute = self.t_conv_compute(M,N,R,C,K,ntile)
            t_load = self.t_conv_load(M,N,R,C,K,ntile,0,ntile)
            t = max(t_compute,t_load)

        elif(layer.type == "FC"):
            N = layer.nifm #input channel
            M = layer.nofm #out channel
            t_compute = self.t_fc_compute(M,N,ntile)
            t_load = self.t_fc_load(M,N,ntile,1)
            t = max(t_compute,t_load)
        else:
            t = 0
        return t
    
    def estimate_nn(self,nn,ntile):
        t = 0
        for layer_name in nn:
            cur_layer = nn[layer_name]
            t += self.estimate_layer(cur_layer,ntile)   
        return t