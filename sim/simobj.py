class SimObj:
    def __init__(self,name = ""):
        self.obj_name = name
        self.modules = {}

    def add_module(self, module):
        self.modules[module.obj_name] = module
    
    def get_type(self):
        raise NotImplementedError

    def startup(self):  
        """
        * startup() is the final initialization call before simulation.
        * All state is initialized so this is the appropriate place to
        * schedule initial event(s) for objects that need them.
        """
        raise NotImplementedError
    
    def name(self):
        return self.obj_name
