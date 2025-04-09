from brevitas.core.bit_width import BitWidthImplType
from brevitas.core.quant import QuantType
from brevitas.core.restrict_val import FloatToIntImplType
from brevitas.core.restrict_val import RestrictValueType
from brevitas.core.scaling import ScalingImplType
from brevitas.core.zero_point import ZeroZeroPoint
from brevitas.inject import ExtendedInjector
from brevitas.quant.solver import ActQuantSolver
from brevitas.quant.solver import WeightQuantSolver


class CommonBinQuant(ExtendedInjector):
    quant_type = QuantType.BINARY
    bit_width_impl_type = BitWidthImplType.CONST
    scaling_impl_type = ScalingImplType.CONST
    restrict_scaling_type = RestrictValueType.FP
    zero_point_impl = ZeroZeroPoint
    float_to_int_impl_type = FloatToIntImplType.ROUND
    scaling_per_output_channel = False
    narrow_range = True
    signed = True
    bit_width = 1

class CommonBinWeightQuant(CommonBinQuant, WeightQuantSolver):
    scaling_const = 1

class CommonBinActQuant(CommonBinQuant, ActQuantSolver):
    min_val = -1.0
    max_val = 1.0
    scaling_const = 1

