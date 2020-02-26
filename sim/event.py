from queue import PriorityQueue
from collections import OrderedDict

class Event:
    def __init__(self, call_back):
        self.when = 0 # when will this event be processed
        self.eventQueue = None # the eventQueue that holds this event
        self.call_back = call_back # the function that processes this event
        self.eventName = ""

    def setWhen(self, when, eventQueue):
        """
        Set the processing time and eventQueue of this event
        """
        self.when = when
        self.queue = eventQueue

    def process(self):
        """
        Call the call_back function to process this event
        """
        if(self.call_back is not None):
            self.call_back()
    
    def name(self):
        return self.eventName

class EventQueue:
    """
    Since it is an event-driven simulator, the EventQueue is the key componet that 
    manages all the events.
    """
    def __init__(self):
        # the global time
        self.curTick = 0
        # the eventQueue is a dict, in which the keys are the time, and values are list of evets.
        self.eventQueue = {}
    
    def removeEvents(self, when):
        """
        Remove the events list at the certain time
        Args:
            when: the time of the events
        """
        self.eventQueue.pop(when)
    
    def getEvents(self, when):
        if(when in self.eventQueue.keys()):
            return self.eventQueue[when]
        else:
            return []

    def schedule(self, event, when):
        """
        Schedule the event, set the event and add to the eventQueue
        """
        event.setWhen(when, self)
        if(when in self.eventQueue.keys()):
            self.eventQueue[when].append(event)
        else:
            self.eventQueue[when] = [event]

    def deschedule(self, event):
        raise NotImplementedError
    
    def reschedule(self, even):
        raise NotImplementedError
    
    def nextTick(self):
        """
        The next tick that events should be processed
        Args:
            No args
        Returns:
            -1: if no events
            nextTick: the next time that some events are going to be processed
        """
        if(self.empty()):
            return -1
        return sorted(self.eventQueue.keys())[0]
    
    def setCurTick(self, when):
        self.curTick = when
    
    def getCurTick(self):
        return self.curTick
    
    def empty(self):
        return len(self.eventQueue) == 0
