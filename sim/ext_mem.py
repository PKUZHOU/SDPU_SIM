from .simobj import SimObj
from .event import Event
from .router import Router
from .defines import * 

class query_task:
    def __init__(self, total_bytes, call_back):
        self.bytes = total_bytes
        self.call_back = call_back
        

class Ext_Memory(SimObj):
    def __init__(self,name):
        super(Ext_Memory,self).__init__(name)
        self.bandwidth = 0
        self.channels = 0
        self.acc_config = None
        self.has_tasks = False
        self.queue = [] 
        self.per_cycle_bytes = 0


    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth

    def set_channels(self, channels):
        self.channels = channels
    
    def configure(self, acc_config):
        self.acc_config = acc_config
        self.set_bandwidth(acc_config["EXT_MEM_BANDWIDTH"])
        self.set_channels(acc_config["EXT_MEM_CHANNELS"])

        Freq = self.acc_config["FREQUENCY"]
        BW = self.bandwidth * 1e9
        Freq = Freq * 1e6
        self.per_cycle_bytes = BW/Freq

        # self.add_router(acc_config)
    
    def process(self):
        total_tasks = len(self.queue)
        ten_cycles_bytes = int(10*self.per_cycle_bytes) 

        bytes_per_task = ten_cycles_bytes/total_tasks
        for task in self.queue:
            task.bytes-=bytes_per_task
            if(task.bytes<=0):
                self.add_event(task.call_back,1)
                self.queue.remove(task)

        # while(ten_cycles_bytes>0):
        #     for task in self.queue:
        #         task.bytes-=8
        #         ten_cycles_bytes-=8
        #         if(task.bytes<=0):
        #             self.queue.remove(task)
        #             self.add_event(task.call_back,1)

        if(len(self.queue)==0):
            self.has_tasks = False
        if(self.has_tasks):
            self.add_event(self.process,10)

    def query(self, total_bytes, call_back):
        self.queue.append(query_task(total_bytes,call_back))
        # self.concurrent_tasks+=1
        # print(self.concurrent_tasks)
        # BW = self.bandwidth/self.concurrent_tasks
        # Freq = self.acc_config["FREQUENCY"]
        # BW = BW * 1e9
        # Freq = Freq * 1e6
        # latency = int(Freq * total_bytes/BW) + 1
        # self.add_event(call_back,latency)
        if(not self.has_tasks):
            self.has_tasks = True
            self.add_event(self.process,200)


    def startup(self, eventQueue):
        if(self.eventQueue is None):
            self.eventQueue = eventQueue
        for module in self.modules.values():
            module.startup(eventQueue)