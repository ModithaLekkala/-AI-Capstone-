import ast
import brevitas.nn as qnn
import brevitas.quant.binary as qbin
from brevitas.core.scaling import ConstScaling

import torch
import torch.nn as nn

from quantizer import CommonBinActQuant, CommonBinWeightQuant 

# control plane dnn
class DeeperNN(nn.Module):
    def __init__(self, input_size, hidden_layers, output_size=2, last_act=None):
        super(DeeperNN, self).__init__()
        self.seq = nn.Sequential(
            nn.Linear(input_size, hidden_layers[0]),
            nn.BatchNorm1d(hidden_layers[0], affine=False, momentum=0.9),
            nn.ReLU(),
            nn.Linear(hidden_layers[0], hidden_layers[1]),
            nn.BatchNorm1d(hidden_layers[1], affine=False, momentum=0.9),
            nn.ReLU(),
            nn.Linear(hidden_layers[1], hidden_layers[2]),
            nn.BatchNorm1d(hidden_layers[2], affine=False, momentum=0.9),
            nn.ReLU(),
            nn.Linear(hidden_layers[2], output_size),
        )
        

    def forward(self, x):
        return self.seq(x)
    
def deeper(cfg, input_size, ):
    num_classes = cfg.getint('MODEL', 'NUM_CLASSES')
    out_features = ast.literal_eval(cfg.get('MODEL', 'OUT_FEATURES'))
    net = DeeperNN(input_size, out_features, num_classes)
    return net
    
# data plane dnn
class SmallerNN(nn.Module):
    def __init__(self, input_size, hidden_layers, output_size=2):
        super(SmallerNN, self).__init__()
        
        self.model = nn.Sequential(
            qnn.QuantLinear(input_size, hidden_layers[0], bias=False, weight_quant=CommonBinWeightQuant),
            qnn.QuantIdentity(act_quant=CommonBinActQuant),
            qnn.QuantLinear(hidden_layers[0], hidden_layers[1], bias=False, weight_quant=CommonBinWeightQuant),
            qnn.QuantIdentity(act_quant=CommonBinActQuant),
            qnn.QuantLinear(hidden_layers[1], output_size, bias=False, weight_quant=CommonBinWeightQuant)
        )

    # def clip_weights(self, min, max):
    #     for lin in self.model:
    #         if(isinstance(lin, qnn.QuantLinear)):
    #             lin.weight.data.clamp_(min, max)

    def forward(self, x):
        return self.model(x)
    
def smaller(cfg, input_size):
    num_classes = cfg.getint('MODEL', 'NUM_CLASSES')
    out_features = ast.literal_eval(cfg.get('MODEL', 'OUT_FEATURES'))
    net = SmallerNN(input_size, out_features, num_classes)
    return net