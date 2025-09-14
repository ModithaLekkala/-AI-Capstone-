import ast
import brevitas.nn as qnn
from quantizer import CommonBinActQuant, CommonBinWeightQuant 
import torch
import torch.nn as nn
import numpy as np

DROPOUT = 0.3

# control plane dnn
class DeeperNN(nn.Module):
    def __init__(self, input_size, hidden_layers, output_size=2, last_act=None):
        super(DeeperNN, self).__init__()
        self.features = nn.ModuleList()
        in_features=input_size

        for out_features in hidden_layers:
            self.features.append(nn.Linear(in_features, out_features)),
            in_features = out_features
            self.features.append(nn.BatchNorm1d(num_features=in_features, affine=False, momentum=0.9))
            self.features.append(nn.ReLU())

        self.features.append(nn.Linear(in_features, output_size))

    def forward(self, x):
        for mod in self.features:
            x = mod(x)
        return x
    
def deeper(cfg, input_size, ):
    num_classes = cfg.getint('MODEL', 'NUM_CLASSES')
    out_features = ast.literal_eval(cfg.get('MODEL', 'OUT_FEATURES'))
    net = DeeperNN(input_size, out_features, num_classes)
    return net
    
# data plane dnn
class SmallerNN(nn.Module):
    def __init__(self, input_size, hidden_layers, output_size=2):
        super(SmallerNN, self).__init__()
        self.n_layers = len(hidden_layers)+1

        self.features = nn.ModuleList()
        in_features=input_size

        for out_features in hidden_layers:
            self.features.append(
                qnn.QuantLinear(
                    in_features=in_features,
                    out_features=out_features,
                    bias=False,
                    weight_quant=CommonBinWeightQuant))
            in_features = out_features
            # self.features.append(nn.BatchNorm1d(num_features=in_features, momentum=0.9))
            self.features.append(qnn.QuantIdentity(act_quant=CommonBinActQuant))
            self.features.append(nn.Dropout(p=DROPOUT))


        self.features.append(
            qnn.QuantLinear(
                in_features=in_features,
                out_features=output_size,
                bias=False,
                weight_quant=CommonBinWeightQuant))

        for m in self.modules():
            if isinstance(m, qnn.QuantLinear):
                torch.nn.init.uniform_(m.weight.data, -1, 1)

    def clip_weights(self, min, max):
        for lin in self.features:
            if(isinstance(lin, qnn.QuantLinear)):
                lin.weight.data.clamp_(min, max)

    def forward(self, x):
        x = x.view(x.shape[0], -1)
        x = 2.0 * x - torch.tensor([1.0], device=x.device)
        for mod in self.features:
            x = mod(x)
        return x
    
    def get_bin_weights(self):
        weights = []
        for _, module in self.features.named_modules():
            if isinstance(module, qnn.QuantLinear):
                bin_weights = module.quant_weight()
                weights.append(bin_weights)
        return weights
    
def smaller(cfg, input_size):
    num_classes = cfg.getint('MODEL', 'NUM_CLASSES')
    out_features = ast.literal_eval(cfg.get('MODEL', 'OUT_FEATURES'))
    net = SmallerNN(input_size, out_features, num_classes)
    return net