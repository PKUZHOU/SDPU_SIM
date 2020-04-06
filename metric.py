
def STP(single_cycles = None, multi_cycles = None):
    if(single_cycles is None):
        return("STP")
    assert(len(single_cycles) == len(multi_cycles))
    n_tasks = len(single_cycles)
    stp = 0
    for task_id in range(n_tasks):
        stp += single_cycles[task_id]/float(multi_cycles[task_id])
    return stp

def ANTT(single_cycles = None, multi_cycles = None):
    if(single_cycles is None):
        return("ANTT")
    antt = 0
    assert(len(single_cycles) == len(multi_cycles))
    n_tasks = len(single_cycles)
    for task_id in range(n_tasks):
        antt += float(multi_cycles[task_id])/single_cycles[task_id]
    antt/=n_tasks
    return antt

def Fairness(single_cycles = None, multi_cycles = None):
    if(single_cycles is None):
        return("Fairness")

    fairness = 100
    # multi_cycles = {}
    assert(len(single_cycles) == len(multi_cycles))
    N = len(multi_cycles)
    for i in range(N):
        for j in range(N):
            if(i == j):
                continue
            fairness = min(fairness, ((single_cycles[i])/float(multi_cycles[i]))/((single_cycles[j])/float(multi_cycles[j])))
    return fairness
