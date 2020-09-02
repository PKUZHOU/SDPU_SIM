from nn_dataflow.nns import import_network
from metric import *

import math

Weight_Buff_BW = 30e9
Activation_Buff_BW = 167e9
MAC_Rows = 256
MAC_Cols = 256
Frequency = 700e6

def read_activation_cycles(n_bytes):
    cycles = Frequency*n_bytes/Activation_Buff_BW
    cycles = math.ceil(cycles)
    return cycles

def get_conv_kernel_bytes(conv_layer):
    N = conv_layer.nifm #input channel
    K = conv_layer.hfil #kernel width
    O = conv_layer.nofm #out channel
    return K * K * N * O

def get_fc_kernel_bytes(fc_layer):
    N = fc_layer.nifm #input channel
    O = fc_layer.nofm #out channel
    return N*O

def read_weight_cycles(n_bytes):
    cycles = Frequency*n_bytes/Weight_Buff_BW
    cycles = math.ceil(cycles)
    return cycles

def compute_conv(conv_layer):
    N = conv_layer.nifm #input channel
    W = conv_layer.wifm #input width
    H = W              #input height
    K = conv_layer.hfil #kernel width
    S = conv_layer.htrd #stride
    O = conv_layer.nofm #out channel
    R = conv_layer.hofm #output height
    C = conv_layer.wofm #output width
    
    I_col = K * K * N
    I_row = R * C
    W_col = O
    W_row = K * K * N

    I_col_loops = math.ceil(I_col / 256.)
    I_row_loops = math.ceil(I_row / 256.)
    W_col_loops = math.ceil(W_col / 256.)
    W_row_loops = math.ceil(W_row / 256.)

    total_loops = I_col_loops * I_row_loops * W_col_loops * W_row_loops
    return total_loops * 256

def compute_fc(fc_layer):
    N = fc_layer.nifm #input channel
    O = fc_layer.nofm #out channel
    col_loops = math.ceil(O/256.)
    row_loops = math.ceil(N/256.)
    tot_loops = col_loops * row_loops
    return tot_loops * 256


def FCFS(net_names):
    # running_cycles = dict(zip(net_names,[0 for i in range(len(net_names))]))
    multi_cycles = []
    single_cycles = []
    total_cycle = 0
    for net_name in net_names:
        net = import_network(net_name)
        single_cycle = 0
        for layer_name in net:
            cur_layer = net[layer_name]
            cur_layer_type = cur_layer.type
            if(cur_layer_type == None):
                N = cur_layer.nofm
                H = cur_layer.hofm
                W = cur_layer.wofm
                print("Shape ", N, H, W)
            #convolutional layer
            elif(cur_layer_type == "Conv"):
                compute_cycles = compute_conv(cur_layer)
                n_bytes = get_conv_kernel_bytes(cur_layer)
                read_w_cycles = read_weight_cycles(n_bytes)
                single_cycle += max(compute_cycles, read_w_cycles)

            #fully-connected layer
            elif(cur_layer_type == "FC"):
                compute_cycles = compute_fc(cur_layer)
                n_bytes = get_fc_kernel_bytes(cur_layer)
                read_w_cycles = read_weight_cycles(n_bytes)
                single_cycle += max(compute_cycles, read_w_cycles)
        total_cycle += single_cycle
        single_cycles.append(single_cycle)
        # running_cycles[net_name] += total_cycles
        multi_cycles.append(total_cycle)
    return single_cycles,multi_cycles

def RR(net_names):
    running_cycles = dict(zip(net_names,[0 for i in range(len(net_names))]))
    nets = {}
    for net_name in net_names:
        net = import_network(net_name)
        layers = []
        for layer_name in net:
            cur_layer = net[layer_name]
            layers.append(cur_layer)
        nets[net_name] = layers
    
    total_cycles = 0
    layer_indexes = dict(zip(net_names,[0 for i in range(len(net_names))]))
    while(True):
        remaining = False
        for net_name, cur_layer_index in layer_indexes.items():
            if(cur_layer_index<len(nets[net_name])):
                remaining = True
                cur_layer = nets[net_name][cur_layer_index]
                cur_layer_type = cur_layer.type
                if(cur_layer_type == None):
                    N = cur_layer.nofm
                    H = cur_layer.hofm
                    W = cur_layer.wofm
                    print("Shape ", N, H, W)

                #convolutional layer
                elif(cur_layer_type == "Conv"):
                    compute_cycles = compute_conv(cur_layer)
                    n_bytes = get_conv_kernel_bytes(cur_layer)
                    read_w_cycles = read_weight_cycles(n_bytes)
                    total_cycles += max(compute_cycles, read_w_cycles)

                #fully-connected layer
                elif(cur_layer_type == "FC"):
                    compute_cycles = compute_fc(cur_layer)
                    n_bytes = get_fc_kernel_bytes(cur_layer)
                    read_w_cycles = read_weight_cycles(n_bytes)
                    total_cycles += max(compute_cycles, read_w_cycles)
            
            if(cur_layer_index == len(nets[net_name]) - 1):
                running_cycles[net_name] += total_cycles
            layer_indexes[net_name]+=1
        if not remaining:
            break
    
    return list(running_cycles.values())

def main():
    # net_names = ['alex_net','vgg','resnet50']
    net_names = ['alex_net','vgg','resnet50','mlp_m','mlp_l','lstm_m','lstm_l']
    # net_names = ['alex_net','vgg','resnet50','mlp_m','mlp_l']

    FCFS_single, FCFS_multi = FCFS(net_names)
    FCFS_stp = STP(FCFS_single, FCFS_multi)
    FCFS_antt = ANTT(FCFS_single,FCFS_multi)
    FCFS_fairness = Fairness(FCFS_single, FCFS_multi)
    
    RR_multi = RR(net_names)
    RR_single = FCFS_single
    RR_stp = STP(RR_single, RR_multi)
    RR_antt = ANTT(RR_single, RR_multi)
    RR_fairness = Fairness(RR_single, RR_multi)

    print(FCFS_stp)
    print(FCFS_antt)
    print(FCFS_fairness)

    print(RR_stp)
    print(RR_antt)
    print(RR_fairness)

if __name__ == "__main__":
    main()