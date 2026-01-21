import ast
import brevitas.nn as qnn
from .quantizer import CommonBinActQuant, CommonBinWeightQuant 
import torch
import torch.nn as nn
from torch.autograd import Function


DROPOUT = 0.4

# control plane dnn
class TeacherNN(nn.Module):
    def __init__(self, input_size, hidden_layers, output_size=2, last_act=None):
        super(TeacherNN, self).__init__()
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

def teacher(cfg, input_size, model_name):
    model_name = model_name.upper()
    num_classes = cfg.getint(model_name, 'NUM_CLASSES')
    out_features = ast.literal_eval(cfg.get(model_name, 'OUT_FEATURES'))
    print(f"Loading full model: [{input_size}, {', '.join(str(i) for i in out_features)}, {num_classes}].")
    net = TeacherNN(input_size, out_features, num_classes)
    return net
    
# data plane dnn
class StudentBNN(nn.Module):
    def __init__(self, input_size, hidden_layers, output_size=2):
        super(StudentBNN, self).__init__()
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
            # self.features.append(nn.BatchNorm1d(num_features=in_features, momentum=0.9, affine=False))
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
    
def student(cfg, input_size, model_name):
    model_name = model_name.upper()
    num_classes = cfg.getint(model_name, 'NUM_CLASSES')
    out_features = ast.literal_eval(cfg.get(model_name, 'OUT_FEATURES'))
    print(f"Loading binarized model: [{input_size}, {', '.join(str(i) for i in out_features)}, {num_classes}].")
    net = StudentBNN(input_size, out_features, num_classes)
    return net

class QuarkCNN(nn.Module):
    def __init__(self, in_len: int):
        super().__init__()

        self.features = nn.Sequential(
            qnn.QuantConv1d(1, 16, 3, padding=1, weight_bit_width=7),
            qnn.QuantReLU(bit_width=7),
            nn.MaxPool1d(2),

            qnn.QuantConv1d(16, 16, 3, padding=1, weight_bit_width=7),
            qnn.QuantReLU(bit_width=7),
            nn.MaxPool1d(2),

            qnn.QuantConv1d(16, 16, 3, padding=1, weight_bit_width=7),
            qnn.QuantReLU(bit_width=7),
            nn.MaxPool1d(2),
        )

        feat_len = in_len // 8
        fc_in = 16 * feat_len

        self.classifier = nn.Sequential(
            nn.Flatten(),
            qnn.QuantLinear(fc_in, 16, weight_bit_width=7),
            qnn.QuantReLU(bit_width=7),
            qnn.QuantLinear(16, 2, weight_bit_width=7)
        )

    def forward(self, x):
        if x.dim() == 2:
            x = x.unsqueeze(1)
        return self.classifier(self.features(x))
def quark(cfg, input_size, model_name):
    print(f"Loading QuarkCNNBinary model with input size {input_size}.")
    net = QuarkCNN(input_size)
    return net