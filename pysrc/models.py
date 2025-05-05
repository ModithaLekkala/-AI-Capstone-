import ast
import brevitas.nn as qnn
import brevitas.quant.binary as qbin
from brevitas.core.scaling import ConstScaling

import torch
import torch.nn as nn

from quantizer import CommonBinActQuant, CommonBinWeightQuant 

DROPOUT = 0.2

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


        # self.seq = nn.Sequential(
        #     nn.Linear(input_size, hidden_layers[0]),
        #     nn.BatchNorm1d(hidden_layers[0], affine=False, momentum=0.9),
        #     nn.ReLU(),
        #     nn.Linear(hidden_layers[0], hidden_layers[1]),
        #     nn.BatchNorm1d(hidden_layers[1], affine=False, momentum=0.9),
        #     nn.ReLU(),
        #     nn.Linear(hidden_layers[1], hidden_layers[2]),
        #     nn.BatchNorm1d(hidden_layers[2], affine=False, momentum=0.9),
        #     nn.ReLU(),
        #     nn.Linear(hidden_layers[2], output_size),
        #     nn.BatchNorm1d(hidden_layers[3], affine=False, momentum=0.9),
        #     nn.ReLU(),
        #     nn.Linear(hidden_layers[3], output_size),
        #     nn.BatchNorm1d(hidden_layers[4], affine=False, momentum=0.9),
        #     nn.ReLU(),
        #     nn.Linear(hidden_layers[4], output_size),
        # )
        

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
        self.features = nn.ModuleList()
        self.features.append(qnn.QuantIdentity(act_quant=CommonBinActQuant))
        in_features=input_size

        for out_features in hidden_layers:
            self.features.append(
                qnn.QuantLinear(
                    in_features=in_features,
                    out_features=out_features,
                    bias=False,
                    weight_quant=CommonBinWeightQuant))
            in_features = out_features
            self.features.append(nn.BatchNorm1d(num_features=in_features))
            self.features.append(qnn.QuantIdentity(act_quant=CommonBinActQuant))
            # self.features.append(nn.Dropout(p=DROPOUT))


        self.features.append(
            qnn.QuantLinear(
                in_features=in_features,
                out_features=output_size,
                bias=False,
                weight_quant=CommonBinWeightQuant))



        # self.model = nn.Sequential(
        #     qnn.QuantLinear(input_size, hidden_layers[0], bias=False, weight_quant=CommonBinWeightQuant),
        #     qnn.QuantIdentity(act_quant=CommonBinActQuant),
        #     qnn.QuantLinear(hidden_layers[0], hidden_layers[1], bias=False, weight_quant=CommonBinWeightQuant),
        #     qnn.QuantIdentity(act_quant=CommonBinActQuant),
        #     # nn.Dropout(),
        #     qnn.QuantLinear(hidden_layers[1], hidden_layers[2], bias=False, weight_quant=CommonBinWeightQuant),
        #     qnn.QuantIdentity(act_quant=CommonBinActQuant),
        #     qnn.QuantLinear(hidden_layers[2], output_size, bias=False, weight_quant=CommonBinWeightQuant),
        # )

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
    
def smaller(cfg, input_size):
    num_classes = cfg.getint('MODEL', 'NUM_CLASSES')
    out_features = ast.literal_eval(cfg.get('MODEL', 'OUT_FEATURES'))
    net = SmallerNN(input_size, out_features, num_classes)
    return net