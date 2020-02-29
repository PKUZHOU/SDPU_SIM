from .simobj import SimObj
from .event import Event
from .router import Router
from .sram import SRAM
from .defines import *

class GlobalBuffer(SimObj):
    def __init__(self, name):
        super(GlobalBuffer,self).__init__(name)
        self.config_regs = []
        self.eventQueue = None

    def get_type(self):
        return GBUF_

    def load_config_regs(self, config_regs):
        self.config_regs = config_regs

    def add_sram(self, sram_type, acc_config):
        """
        Args: 
            sram_type: "INPUT","WEIGHT","OUTPUT"
        """
        sram_name = self.name().replace(GBUF_,"{}-{}-{}".format(SRAM_,GBUF_,sram_type.upper()))
        sram = SRAM(sram_name)
        sram.set_depth(acc_config[sram_type + '_SRAM_DEPTH'])
        sram.set_width(acc_config[sram_type + '_SRAM_WIDTH'])
        self.add_module(sram)

    def get_sram(self, sram_type):
        """
        Args: 
            sram_type: "INPUT","WEIGHT","OUTPUT"
        """
        sram_name = self.name().replace(GBUF_,"{}-{}-{}".format(SRAM_,GBUF_,sram_type.upper()))
        return self.modules[sram_name]

    def get_router(self):
        router = self.modules[self.name().replace(GBUF_,"{}-{}".format(ROUTER_,GBUF_))]
        return router

    def connect_to(self, neighbor, direction):
        """
        Set the router to connect the neighbor PEs
        Args: 
            neighbor_pe: the neighbor pe to connect
            direction: "N","S","W","E" 
        Returns:
            No returns
        """
        router = self.get_router()
        neighbor_router = neighbor.get_router()
        router.set_neighbor(neighbor_router, direction)

    def configure(self, acc_config):
        """
        configure the modules in the GBUF, including srams, router
        Args:
            acc_config: The dict of the accelerator config
        """
        # add the router
        router_name = self.name().replace(GBUF_,"{}-{}".format(ROUTER_,GBUF_))
        router = Router(router_name)
        self.add_module(router)
        # add the input sram
        self.add_sram('INPUT', acc_config)
        self.add_sram('WEIGHT',acc_config)
        self.add_sram('OUTPUT',acc_config)

    def send_packet(self, dst, packet_type):
        # local router
        router = self.get_router()
        # send the packet through local router
        router.add_to_buffer(dst, packet_type)
        event = Event(router.forward)
        when = self.eventQueue.curTick + 1
        router.eventQueue.schedule(event,when)

    def multicast_inputs(self):
        """
        Read the input data from input sram and send them to different PE rows through NOC
        """
        input_sram = self.get_sram("INPUT")
        # multicast to each PE row
        PE_rows = self.config_regs['PE_ROWS']
        for row in range(PE_rows):
            bytes_in_word = 8
            ret = input_sram.read(bytes_in_word)
            if(ret == 0):
                # the first PE of each row
                dst_router_name = self.name().replace(GBUF_,"{}-{}".format(ROUTER_,PE_))\
                    + "-{}-{}".format(row, 0)
                self.send_packet(dst_router_name, MULTICAST_)
            else:
                return
        # start another pass in the next tick 
        multicast_event = Event(self.multicast_inputs)
        curTick = self.eventQueue.curTick
        self.eventQueue.schedule(multicast_event,curTick + 1)

    def unicast_weights(self):
        """
        Read the weight data from weight sram and send them to different PE through NOC
        """
        weight_sram = self.get_sram("WEIGHT")
        # unicast to each PE
        # TODO: consider the NOC bandwidth
        PE_rows = self.config_regs['PE_ROWS']
        PE_cols = self.config_regs['PE_COLS']
        for row in range(PE_rows):
            for col in range(PE_cols):
                bytes_in_word = 8
                ret = weight_sram.read(bytes_in_word)
                if(ret == 0):
                    # the first PE of each row
                    dst_router_name = self.name().replace(GBUF_,"{}-{}".format(ROUTER_,PE_))\
                        + "-{}-{}".format(row,col)
                    self.send_packet(dst_router_name, UNICAST_)
                else:
                    return
        # start another pass in the next tick 
        multicast_event = Event(self.multicast_inputs)
        curTick = self.eventQueue.curTick
        self.eventQueue.schedule(multicast_event,curTick + 1)

    def startup(self, eventQueue):
        for module in self.modules.values():
            module.startup(eventQueue)
        self.eventQueue = eventQueue

        # In this version, the input and weight are pre-loaded in the sram
        multicast_bytes = self.config_regs[MULTICAST_]
        unicast_bytes = self.config_regs[UNICAST_]

        PE_rows = self.config_regs['PE_ROWS']
        PE_cols = self.config_regs['PE_COLS']

        # pre-load the inputs and weights
        # TODO read weight and input from external memory
        input_sram = self.get_sram("INPUT")
        ret = input_sram.write(multicast_bytes * PE_rows)
        assert(ret == 0)
        weight_sram = self.get_sram("WEIGHT")
        ret = weight_sram.write(unicast_bytes * PE_cols * PE_rows)
        assert(ret == 0)

        # start sending the inputs and weights
        curTick = eventQueue.curTick
        multicast_event = Event(self.multicast_inputs)
        eventQueue.schedule(multicast_event,curTick + 1)
        unicast_event = Event(self.unicast_weights)
        eventQueue.schedule(unicast_event,curTick + 1)



    