import torch
import torch.nn as nn
import torchvision.models as models
import time

class Model0(torch.nn.Module):
    def __init__(self):
        super(Model0,self).__init__()
        self.layers=models.alexnet(pretrained=False)
    def generate_input(self):
        return torch.rand(1,3,224,224)

    def forward(self,x):
        start = time.time()
        x = self.layers(x)
        end = time.time()
        print("model0: %f"%(end-start))
        return x

class Model1(torch.nn.Module):
    def __init__(self):
        super(Model1,self).__init__()
        self.layers=models.vgg16(pretrained=False)
    def generate_input(self):
        return torch.rand(1,3,224,224)

    def forward(self,x):
        start = time.time()
        x = self.layers(x)
        end = time.time()
        print("model1: %f"%(end-start))
        return x

class Model2(torch.nn.Module):
    def __init__(self):
        super(Model2,self).__init__()
        self.layers=models.resnet50(pretrained=False)
    def generate_input(self):
        return torch.rand(1,3,224,224)

    def forward(self,x):
        start = time.time()
        x = self.layers(x)
        end = time.time()
        print("model2: %f"%(end-start))
        return x 

class Model3(torch.nn.Module):
    def __init__(self):
        super(Model3,self).__init__()
        self.layers = torch.nn.Sequential(
            nn.Linear(784,1000),
            nn.Linear(1000,500),
            nn.Linear(500,250),
            nn.Linear(250,10)
        )
    def generate_input(self):
        return torch.rand(1,784)

    def forward(self,x):
        start = time.time()
        x = self.layers(x)
        end = time.time()
        print("model3: %f"%(end-start))
        return x

class Model4(torch.nn.Module):
    def __init__(self):
        super(Model4,self).__init__()
        self.layers = torch.nn.Sequential(
            nn.Linear(784,1500),
            nn.Linear(1500,1000),
            nn.Linear(1000,500),
            nn.Linear(500,10)
        )
    def generate_input(self):
        return torch.rand(1,784)

    def forward(self,x):
        start = time.time()
        x = self.layers(x)
        end = time.time()
        print("model4: %f"%(end-start))
        return x

class Model5(torch.nn.Module):
    def __init__(self):
        super(Model5,self).__init__()
        self.layers = torch.nn.Sequential(
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1)
        )
    def generate_input(self):
        return torch.rand(100,1000)

    def forward(self,x):
        start = time.time()
        x = self.layers(x)
        end = time.time()
        print("model5: %f"%(end-start))
        return x


class Model6(torch.nn.Module):
    def __init__(self):
        super(Model6,self).__init__()
        self.layers = torch.nn.Sequential(
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1000),
            nn.Linear(1000,1)
        )
    def generate_input(self):
        return torch.rand(100,1000)

    def forward(self,x):
        start = time.time()
        x = self.layers(x)
        end = time.time()
        print("model6: %f"%(end-start))
        return x


