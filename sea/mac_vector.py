from sim.simobj import SimObj
from sim.event import Event
from .defines import *

class MAC_Vector(SimObj):
    def __init__(self,name):
        super(MAC_Vector,self).__init__(name)
        #add router
        self.lanes = 0

    def get_type(self):
        return MAC_VECTOR_

    def set_lanes(self, lanes):
        self.lanes = lanes

    def startup(self, eventQueue):
        pass