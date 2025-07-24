import copy
from .Size import Size

CSM = b"\xFF" # 块起始符

DS_LIST = [b"\xE0" , b"\xEF"] # 可用的数据段

TS = b"\xE0"
BS = b"\xEF"

Tef_dict = {b"\x00\x00\x00" : "UTF-8",
            b"\x00\x00\x01" : "ASCII",} # 字符对照表

TEF_SIZE = 3 # 字符占用字节数


RPF_SIZE = TEF_SIZE
RPF = b"\x00"*RPF_SIZE # 默认保留位


DLD_SIZE = 8 # 数据长度声明字节数

DLD_BITODER = "big" # 大小端解码


Tef_dict_opposite = {v : k for k , v in Tef_dict.items()}



from types import SimpleNamespace
FileConfig = SimpleNamespace()
FileConfig.DEFAULT_BUFFER_SIZE = Size("4MB").Int()
FileConfig.MODE_WB = "wb"
FileConfig.MODE_RB = "rb"
FileConfig.MODE_ALLOWS = [FileConfig.MODE_WB ,FileConfig.MODE_RB ]

