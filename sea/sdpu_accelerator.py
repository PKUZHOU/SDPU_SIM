from sim.event import EventQueue
from .tile import Tile
from .pe import PE
from .gbuffer import GlobalBuffer
from .router import Router
from sim.DRAM import DRAM
from .defines import *
from .runtime_scheduler import Runtime_Scheduler

class SDPU_Accelerator:
    def __init__(self, acc_config):
        self.evetq = EventQueue()
        self.modules = {}
        # global_modules is a global dictionary accessiable to all modules  
        self.global_modules = {}
        # which tiles have finished the execution
        self.finished_tiles = []
        self.acc_config = acc_config
        self.runtime_scheduler = Runtime_Scheduler()
        self.task_queue = []
        self.tile2task = {}
        self.free_tiles = []
        # build the accelerator
        self.build()
        
    def add_module(self, module):
        """
        Add module to the system (top level)
        Args: 
            module: SimObj(), the module to add
        Returns:
            No returns  
        """
        self.modules[module.name()] = module
        self.global_modules[module.name()] = module

    def build(self):
        """
        Add all the top level modules to the system, and deal with the connections.
        """
        #read the Tile and PE array shape from configs.
        Tile_rows = self.acc_config["H_TILE"] # the number of rows of each Tile array
        Tile_cols = self.acc_config["W_TILE"] # the number of columns of each Tile array
        
        #Tile level loop
        for tile_row_id in range(Tile_rows):
            for tile_col_id in range(Tile_cols):
                #add tile
                tile_name = "{}-{}-{}".format(TILE_, tile_row_id, tile_col_id)
                tile = Tile(tile_name)
                tile.finished_tiles = self.finished_tiles
                tile.set_global_modules(self.global_modules)
                tile.configure(self.acc_config)
                self.add_module(tile)
        # Add external memory
        ext_mem = DRAM(EXT_MEM_)
        ext_mem.set_global_modules(self.global_modules)
        ext_mem.configure(self.acc_config)
        self.add_module(ext_mem)
        # config the runtime scheduler
        self.runtime_scheduler.load_acc_cfg(self.acc_config)

    def get_ext_mem(self, tile_row, tile_col):
        ext_mem_name = "{}-{}-{}".format(EXT_MEM_, tile_row, tile_col)
        return self.modules[ext_mem_name]

    def get_tile(self, tile_row, tile_col):
        tile_name = "{}-{}-{}".format(TILE_,tile_row, tile_col)           
        return self.modules[tile_name]

    def startup(self):
        """
        Initiate all the modules
        """
        for module in self.modules.values():
            module.startup(self.evetq)

    def load_tasks(self, task_queue):
        self.task_queue = task_queue

    def load_instr(self, instr):
        """
        Load the compiled config_regs to the corresponding modules
        Args:
            layer_config_regs: dict{} the compiled config_regs of a layer
                the key are the module names
        Returns:
            No returns
        """
        for module_name, config_regs in instr.items():
            module = self.modules[module_name]
            module.load_config_regs(config_regs)

    def get_per_tile_task(self):
        for task in self.task_queue.tasks:
            if(not task.finished):
                coarse_assigned_tiles = task.assigned_tiles
                for tile_id in coarse_assigned_tiles:
                    self.tile2task[tile_id] = [task]

    def simulate(self):
        """
        Run the simulation. This function fetch evens from 
        the evenqueue and run them.
        """
        # Tile_rows = self.acc_config["H_TILE"] 
        Tile_cols = self.acc_config["W_TILE"]
        
        # First run
        instrs = {}
        for task in self.task_queue.tasks:
            next_layer = task.get_next_layer()
            coarse_assigned_tiles = task.assigned_tiles
            instr = self.runtime_scheduler.mapping_layer(coarse_assigned_tiles, next_layer)
            instrs.update(instr)

        self.get_per_tile_task()

        # load the instructions to tiles and PEs 
        self.load_instr(instrs) 

        # start up all the modules
        self.startup()

        def tile_name_to_id(tile):
            _,row,col = tile.split("-")
            row = int(row)
            col = int(col)
            tile_id = row * Tile_cols + col
            return tile_id

        while(True):
            curTick = self.evetq.nextTick()
            if(curTick < 0):
                return
            # print("Tick: ",curTick)
            self.evetq.setCurTick(curTick)
            cur_events = self.evetq.getEvents(curTick)
            # print(len(cur_events))
            for event in cur_events:
                event.process()
            #all the events within current cycle are processes
            #so we remove these events from the event queue
            self.evetq.removeEvents(curTick)

            # check finish
            if(len(self.finished_tiles)==0):
                continue

            # Some tiles have finished
            for tile in self.finished_tiles:
                # get the id of the finished tile
                tile_id = tile_name_to_id(tile)
                task = self.tile2task[tile_id][0]
                if not task.finished: 
                    if(tile_id not in task.finished_tiles):
                        # collect how many assigned tiles have finished 
                        # wait for all tiles of this task to finish
                        task.finished_tiles.append(tile_id) 

                    if(len(task.finished_tiles) == len(task.assigned_tiles)):
                        # all the tiles have finished the pervious layer
                        next_layer = task.get_next_layer() # fetch the next layer
                        if(next_layer == -1):
                            task.finished = True # this task is over
                            # can reallocate
                            # for task in self.task_queue.tasks:
                            #     task.reallocated = False
                            print("Task: {} finishes at cycle {}".format(task.id, self.evetq.getCurTick()))
                            self.free_tiles += task.assigned_tiles
                            continue
                        
                        # n_free_tiles =  len(self.free_tiles)
                        # if(n_free_tiles>0):
                        #     total_tasks_to_reallocate = 0
                        #     for task in self.task_queue.tasks:
                        #         if(not task.finished and not task.reallocated):
                        #             total_tasks_to_reallocate += 1

                        #     n_reallocate = n_free_tiles // total_tasks_to_reallocate

                        #     if(not task.reallocated):
                        #         for i in range(n_reallocate):
                        #             task.assigned_tiles.append(self.free_tiles[i])
                        #         for i in range(n_reallocate):
                        #             self.free_tiles.pop(0)  
                        #         task.reallocated = True
                            
                        if(len(self.free_tiles)>0):
                            task.assigned_tiles += self.free_tiles
                            self.free_tiles.clear()
                            self.get_per_tile_task()

                        instr = self.runtime_scheduler.mapping_layer(task.assigned_tiles, next_layer)

                        # load new instrs
                        for tile_id in task.assigned_tiles:
                            tile_name = "{}-{}-{}".format(TILE_,tile_id//Tile_cols,tile_id%Tile_cols)
                            self.global_modules[tile_name].load_config_regs(instr[tile_name]) 
                            self.global_modules[tile_name].startup(self.evetq)
                            self.finished_tiles.remove(tile_name)

                        task.finished_tiles.clear()
