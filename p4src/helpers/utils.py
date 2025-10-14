from configparser import ConfigParser
import os
from pathlib import Path
import warnings

def suppress_warnings():
    # Suppress brevitas Warning
    warnings.filterwarnings(
        "ignore",
        message="Defining your `__torch_function__` as a plain method is deprecated",
        category=UserWarning,
    )

def generate_14bit():
    """
    Yields (binary14, hex4, popcount_int) for all 14-bit values 0..(2^14-1).
    """
    for i in range(1 << 14):                            # 0..16383
        bin_str = format(i, '014b')                     # 14-bit binary with leading zeros
        hex_str = format(i, '04X')                      # 4-digit uppercase hex (up to 3FFF)
        popcnt  = format(bin(i).count('1'), '01X')      # integer popcount
        yield bin_str, hex_str, popcnt

def generate_16bit_hex():
    """
    Yields (binary16, hex4, popcount_hex1) for all values 1..(2^16-2).
    """
    for i in range(1, (1 << 16) - 1):
        bin_str = format(i, '016b')    # 16-bit binary
        hex_str = format(i, '04X')     # 4-digit uppercase hex
        popcnt  = format(bin(i).count('1'), '01X')
        yield bin_str, hex_str, popcnt

def hex_lists_to_ints(*hex_lists):
    return [[int(h, 16) for h in lst] for lst in hex_lists]

def get_cfg(name='cicisds2017'):
    cfg = ConfigParser()
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join('/home/sgeraci/inet-hynn/p4src', 'configs', name.lower() + '.ini')
    assert os.path.exists(config_path), f"{config_path} not found."
    cfg.read(config_path)
    
    return cfg

def none_or_str(value):
    if value == "None":
        return None
    return value

def none_or_int(value):
    if value == "None":
        return None
    return int(value)

def get_file_from_keyword(directory, keyword):
    path = Path(directory)
    for file in path.iterdir():
        if file.is_file() and keyword in file.name:
            return file
    return None