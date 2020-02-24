from queue import PriorityQueue
from collections import OrderedDict

class Event:
    def __init__(self, call_back):
        self.when = 0
        self.priority = 1
        self.queue = None
        self.call_back = call_back

    def setWhen(self,when, event_queue):
        self.when = when
        self.queue = event_queue

    def process(self):
        if(self.call_back is not None):
            self.call_back()
    
    def name(self):
        pass

class EventQueue:
    def __init__(self):
        self.objName = ""
        self.curTick = 0
        self.eventQueue = {}

    def insert(self, event):
        raise NotImplementedError
    
    def removeEvents(self, when):
        self.eventQueue.pop(when)
    
    def removeEvent(self, event):
        raise NotImplementedError

    
    def getEvents(self, when):
        if(when in self.eventQueue.keys()):
            return self.eventQueue[when]
        else:
            return []

    def name(self):
        return self.objName

    def schedule(self, event, when):

        if(when in self.eventQueue.keys()):
            self.eventQueue[when].append(event)
        else:
            self.eventQueue[when] = [event]
        #TODO priority 

    def deschedule(self, event):
        raise NotImplementedError
    
    def reschedule(self, even):
        raise NotImplementedError
    
    def nextTick(self):
        if(len(self.eventQueue)==0):
            return -1
        return sorted(self.eventQueue.keys())[0]
    
    def setCurTick(self, when):
        self.curTick = when
    
    def getCurTick(self):
        return self.curTick
    
    def empty(self):
        return len(self.eventQueue) == 0
