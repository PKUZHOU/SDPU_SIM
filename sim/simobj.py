from .event import Event

class SimObj:
    def __init__(self,name = ""):
        self.obj_name = name
        self.type = ""
        self.modules = {}
        self.global_modules = None
        self.eventQueue = None

    def add_event(self, call_back_func, latency):
        assert self.eventQueue is not None
        curTick = self.eventQueue.curTick
        event = Event(call_back_func)
        self.eventQueue.schedule(event,curTick + int(latency))

    def add_module(self, module):
        self.modules[module.obj_name] = module
        self.global_modules[module.obj_name] = module
    
    def set_global_modules(self, global_modules):
        self.global_modules = global_modules

    def get_type(self):
        return self.type

    def startup(self):  
        """
        * startup() is the final initialization call before simulation.
        * All state is initialized so this is the appropriate place to
        * schedule initial event(s) for objects that need them.
        """
        raise NotImplementedError
    
    def get_module(self,name):
        return self.modules[name]

    def get_global_module(self,name):
        return self.global_modules[name]

    def name(self):
        return self.obj_name
