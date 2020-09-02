from sim.simobj import SimObj
from sim.event import Event
from .defines import *

class Controller(SimObj):
    def __init__(self,name):
        super(Controller,self).__init__(name)
        self.eventQueue = None
        self.acc_config = None 
        self.insts = {}
        self.pc = 0
        self.current_task = None

    def configure(self,acc_config):
        self.acc_config = acc_config

    def load_insts(self, insts):
        self.insts = insts

    def finish_load_IA(self):
        self.add_event(self.run_inst, 1)

    def finish_load_W(self):
        self.add_event(self.run_inst, 1)

    def finish_load_from_host(self):
        self.add_event(self.run_inst, 1)

    def finish_gemm(self):

        # W_buffer = self.get_global_module(W_BUF_)
        # assert(len(W_buffer.weight_fifo)>0)
        # len(W_buffer.weight_fifo).pop(0)

        self.add_event(self.run_inst, 1)

    def run_inst(self):
        # check if the task is finished 
        if(self.pc >= len( self.insts[self.current_task])):
            return

        inst = self.insts[self.current_task][self.pc]

        print(inst)
        
        # inst type, GEMM or LOAD 
        inst_type = inst.split("-")[0]

        if(inst_type == LOAD_):
            load_type = inst.split("-")[1]
            load_bytes = int(inst.split("-")[2])

            tag = inst.split("-")[-1]

            if(load_type == "IA"):
                IA_buffer = self.get_global_module(IA_BUF_)
                IA_buffer.bytes_to_load = load_bytes
                self.add_event(IA_buffer.load_from_host, 1)

            elif(load_type == "W"):
                self.add_event(self.run_inst, 1)
                # W_buffer = self.get_global_module(W_BUF_)
                # W_buffer.bytes_to_load = load_bytes 
                
                # W_buffer.weight_fifo.push(tag)
                # self.add_event(W_buffer.load_from_ddr, 1)

        if(inst_type == GEMM_):
            a_rows,a_cols,b_rows,b_cols, tag = [int(x) for x in inst.split("-")[1:]]

            W_buffer = self.get_global_module(W_BUF_)
            # if(tag in W_buffer.weight_fifo):

            systolic_array = self.get_global_module(SYSTOLIC_ARRAY_)
            systolic_array.IA_shape = [a_rows,a_cols]
            systolic_array.W_shape = [b_rows,b_cols]

            
            self.add_event(systolic_array.compute, 1)

        self.pc += 1
    
    def startup(self, eventQueue):
        if(self.eventQueue is None):
            self.eventQueue = eventQueue
        
        for module in self.modules.values():
            module.startup(eventQueue)

        assert len(self.insts) > 0
        self.current_task = list(self.insts.keys())[0]
        self.add_event(self.run_inst, 1)