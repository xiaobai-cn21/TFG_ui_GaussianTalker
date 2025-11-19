import re
import json
import numpy as np

# ==========================
# HParams
# ==========================
def get_hparams_from_file(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        data = f.read()
    config = json.loads(data)
    hparams = HParams(**config)
    return hparams

class HParams:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, dict):
                v = HParams(**v)
            self[k] = v

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()

    def values(self):
        return self.__dict__.values()

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __contains__(self, key):
        return key in self.__dict__

    def __repr__(self):
        return self.__dict__.__repr__()

# ==========================
# Bit utils
# ==========================
def string_to_bits(string, pad_len=8):
    ascii_values = [ord(char) for char in string]
    binary_values = [bin(value)[2:].zfill(8) for value in ascii_values]
    bit_arrays = [[int(bit) for bit in binary] for binary in binary_values]
    numpy_array = np.array(bit_arrays)
    numpy_array_full = np.zeros((pad_len, 8), dtype=numpy_array.dtype)
    numpy_array_full[:, 2] = 1
    max_len = min(pad_len, len(numpy_array))
    numpy_array_full[:max_len] = numpy_array[:max_len]
    return numpy_array_full

def bits_to_string(bits_array):
    binary_values = [''.join(str(bit) for bit in row) for row in bits_array]
    ascii_values = [int(binary, 2) for binary in binary_values]
    return ''.join(chr(value) for value in ascii_values)

# ==========================
# Sentence splitting
# ==========================
def split_sentence(text, min_len=10, language_str='[EN]'):
    if language_str in ['EN']:
        return split_sentences_latin(text, min_len)
    else:
        return split_sentences_zh(text, min_len)

# 省略 split_sentences_latin, merge_short_sentences_latin, split_sentences_zh, merge_short_sentences_zh
# 可以沿用你原来的代码

# ==========================
# text_to_sequence
# ==========================
# 简单字符->id映射，你可以根据模型 symbols 调整
_symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,!?[]"
_symbol_to_id = {s: i for i, s in enumerate(_symbols)}

def text_to_sequence(text, symbols, cleaners=[]):
    """
    Convert text to sequence of symbol IDs.
    text: 输入文本
    symbols: 模型支持的字符集列表
    cleaners: 文本清理函数列表，目前可忽略
    """
    sequence = []
    for char in text:
        if char in symbols:
            sequence.append(symbols.index(char))
        else:
            sequence.append(symbols.index(' ') if ' ' in symbols else 0)
    return sequence
