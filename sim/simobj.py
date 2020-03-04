from .event import Event

class SimObj:
    def __init__(self,name = ""):
        self.obj_name = name
        self.type = ""
        self.modules = {}
        self.eventQueue = None

    def add_event(self, call_back_func, latency):
        assert self.eventQueue is not None
        curTick = self.eventQueue.curTick
        event = Event(call_back_func)
        self.eventQueue.schedule(event,curTick + latency)

    def add_module(self, module):
        self.modules[module.obj_name] = module
    
    def get_type(self):
        return self.type

    def startup(self):  
        """
        * startup() is the final initialization call before simulation.
        * All state is initialized so this is the appropriate place to
        * schedule initial event(s) for objects that need them.
        """
        raise NotImplementedError
    
    def name(self):
        return self.obj_name
