from models import *
import torch.multiprocessing as mp
from torch.multiprocessing import Pool, Process, set_start_method


def run_model(model):
    x = model.generate_input().cuda()
    out = model(x)

# All_models = [Model0().cuda(),Model1().cuda(),Model2().cuda(),Model3().cuda(),Model4().cuda(),Model5().cuda(),Model6().cuda()]
All_models = [Model0().cuda(),Model1().cuda(),Model2().cuda(),Model3().cuda(),Model4().cuda()]
# All_models = [Model0().cuda(),Model1().cuda(),Model2().cuda()]


for model in All_models:
    model.eval()
    model.share_memory()

total_model = len(All_models)

def single():
    for model in All_models:
            run_model(model)

def multi():
    processes = []
    for model_idx in range(total_model):
        p = mp.Process(target=run_model, args=(All_models[model_idx],))
        processes.append(p)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

if __name__ == "__main__":
    set_start_method('spawn')
    # single()
    # "--------------------------"
    multi()

    

