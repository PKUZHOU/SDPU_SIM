import yaml
import os
def read_acc_config(cfg_file_name):
    print("Read accelerator config file "+cfg_file_name)
    assert(os.path.isfile(cfg_file_name))

    cfg_file = open(cfg_file_name, 'r', encoding="utf-8")
    cfg_data = cfg_file.read()
    cfg_file.close()
    
    cfg = yaml.load(cfg_data)
    return cfg