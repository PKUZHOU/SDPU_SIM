from nn_dataflow.nns import import_network
import math

Weight_Buff_BW = 30e9
Activation_Buff_BW = 167e9
MAC_Rows = 256
MAC_Cols = 256
Frequency = 700e6


def STP(net_cycles):
    stp = 0
    multi_cycles = {}
    tot_cycles = 0
    for net_name, cycles in net_cycles.items():
        tot_cycles += cycles
        multi_cycles[net_name] = tot_cycles
        
    for net_name, single_cycles in net_cycles.items():
        stp += single_cycles/float(multi_cycles[net_name])

    return stp

def ANTT(net_cycles):
    antt = 0
    multi_cycles = {}
    tot_cycles = 0
    for net_name, cycles in net_cycles.items():
        tot_cycles += cycles
        multi_cycles[net_name] = tot_cycles
        
    for net_name, single_cycles in net_cycles.items():
        antt += float(multi_cycles[net_name])/single_cycles

    antt/=len(multi_cycles)
    return antt

def Fairness(net_cycles):
    fairness = 100
    multi_cycles = {}
    tot_cycles = 0
    for net_name, cycles in net_cycles.items():
        tot_cycles += cycles
        multi_cycles[net_name] = tot_cycles

    N = len(multi_cycles)
    for i in range(N):
        for j in range(N):
            name_i = list(net_cycles.keys())[i]
            name_j = list(net_cycles.keys())[j]
            fairness = min(fairness, ((net_cycles[name_i])/float(multi_cycles[name_i]))/((net_cycles[name_j])/float(multi_cycles[name_j])))

    return fairness


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

def run(net_names):
    running_cycles = dict(zip(net_names,[0 for i in range(len(net_names))]))

    for net_name in net_names:
        net = import_network(net_name)
        total_cycles = 0
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
                total_cycles += max(compute_cycles, read_w_cycles)

            #fully-connected layer
            elif(cur_layer_type == "FC"):
                compute_cycles = compute_fc(cur_layer)
                n_bytes = get_fc_kernel_bytes(cur_layer)
                read_w_cycles = read_weight_cycles(n_bytes)
                total_cycles += max(compute_cycles, read_w_cycles)

        running_cycles[net_name] += total_cycles

    return running_cycles



def main():
    # net_names = ['alex_net','resnet50','mlp_m','mlp_l']
    net_names = ['alex_net','vgg','resnet50','mlp_m','mlp_l']
    net_cycles = run(net_names)
    stp = STP(net_cycles)
    antt = ANTT(net_cycles)
    fairness = Fairness(net_cycles)
    print(stp)
    print(antt)
    print(fairness)

if __name__ == "__main__":
    main()