
class Task:
    def __init__(self, nn):
        self.id = -1
        self.nn = nn
        self.layers = list(self.nn.layer_dict.values())
        self.total_layer = len(nn)
        self.current_layer = 1
        self.assigned_tiles = [] 
        self.finished_tiles = []
        self.finished = False
        self.reallocated = False

    def get_next_layer(self):
        """
        Return:
            next_layer: if next layer is Conv or FC
            -1: No layer remains
        """
        while(True):
            if(self.current_layer>=self.total_layer):
                return -1
            current_layer = self.layers[self.current_layer]
            self.current_layer += 1
            if(current_layer.type in ["FC","Conv"]):
                return current_layer

class TaskQueue:
    def __init__(self):
        self.tasks = []
        self.total_tasks = 0

    def add_task(self, nn):
        task = Task(nn)
        task.id = self.total_tasks
        self.tasks.append(task)
        self.total_tasks += 1

    def assign_tiles(self, allocation):
        """
        Assign tiles to each task (in tile ids)
        """
        base = 0
        for i in range(self.total_tasks):
            for j in range(allocation[i]):
                self.tasks[i].assigned_tiles.append(base + j)
            base += allocation[i]

    def __len__(self):
        return len(self.tasks)
