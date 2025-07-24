import copy

from .config import *
import _io
import os
from collections import OrderedDict
from io import BytesIO
from .Error_process import dealError

def copy_file_object(file_obj) -> _io.BufferedReader:
    result = None
    if hasattr(file_obj,"name"):

        file_path = file_obj.name
        if os.path.exists(file_path) and os.path.isfile(file_path):
            result =  open(file_path,file_obj.mode)
    else:
        result =  copy.copy(file_obj)

    result.seek(0)
    return result

    # result = None
    # if isinstance(file_obj,_io.BytesIO):
    #     result = copy.copy(file_obj)
    # else:
    #     """复制文件对象，返回一个指针独立的新对象"""
    #     new_fd = os.dup(file_obj.fileno())
    #     result =  open(new_fd, file_obj.mode,closefd=True)  # 保持相同的打开模式
    # # result.seek(0)
    # return result

#
# def create_independent_fileobj(original):
#     """创建具有独立指针的文件对象"""
#     # 获取原始文件路径
#     if hasattr(original, 'name') and os.path.exists(original.name):
#         return open(original.name, original.mode)
#
#     # 对于没有路径的对象（如套接字、管道）
#     return reopen_via_tempfile(original)


class bitRange():
    # t = 0
    def __init__(self,file,range):
        # print(f"tell:{file.tell()}")
        self.file :_io.BufferedReader = copy_file_object(file)

        self.range = range if not isinstance(range,int) else [range , range+1]
        if not isinstance(self.range,tuple):
            self.range = (self.range[0],self.range[1])

        # assert self.range[0] >=0


        self.len = self.range[1] - self.range[0]
        self.seek(0)


    def value(self):
        self.file.seek(0)
        # print(self.file.read())
        self.file.seek(self.range[0])
        # print(self.len,self.range)

        return self.file.read(self.len)

    def is_single(self):
        if self.len == 1:
            return True
        else:
            return False


    def Range(self):
        return self.range

    def __str__(self):
        return f"{self.file}[{self.range[0]}:{self.range[1]}]"
    def read(self,n = -1):
        # print(self.len,n)

        if n <= 0:
            # print(0)
            return self.file.read(self.range[1] - self.file.tell())
        else:
            if self.file.tell() + n > self.range[1]:
                # print(1)
                return self.read(-1)
            else:
                # print(2)
                # print(self.file.tell())
                r = self.file.read(n)
                # print(n , len(r),self.file.tell())
                return r
    def seek(self,n):
        if n > self.size():
            self.file.seek(self.range[1])
        if n < 0:
            n = 0


        self.file.seek(self.range[0] + n)

    def peek(self,index = -1,n = 1):
        peek(self.file,index,n)



    def tell(self):
        return self.file.tell() - self.range[0]

    def size(self):
        return self.len

    def __len__(self):
        return self.size()


class __BASE__():
    def __init__(self,file_path,print_f):
        self.print = print_f
        if isinstance(file_path, _io.BufferedReader):

            self.file = file_path
        elif isinstance(file_path, str):
            self.file = open(file_path, "rb")
        elif isinstance(file_path,bytes):
            self.file = BytesIO()
            self.file.write(file_path)  # 注意要写入bytes类型数据
            self.file.flush()
        elif isinstance(file_path,_io.BytesIO):
            self.file = file_path
            # print(self.file.fileno())



        if file_path == None:
            self.file = None
            self.size = -1
        elif isinstance(file_path, bytes):
            self.size = len(file_path)
        elif isinstance(file_path,_io.BytesIO):
            self.size = len(self.file.getbuffer())  # 直接获取内存视图的大小，不复制数据
        else:
            self.size = os.fstat(self.file.fileno()).st_size

    @dealError
    def __del__(self):
        if not hasattr(self,"file"):
            return

        if not getattr(self.file,"closed",True):
            self.file.close()



def peek(file : _io.BufferedReader,index = -1,n = 1):
    now_i = file.tell()
    if index >= 0:
        file.seek(index)
    result = file.read(n)
    file.seek(now_i)
    return result

class CdcParser(__BASE__):

    def __init__(self,file_path = None,print_f = print):
        __BASE__.__init__(self,file_path,print_f)

    def parse(self,file_path = None):
        file = None
        size = -1

        if file_path == None:
            file = self.file

            size = self.size
        elif isinstance(file_path, _io.BufferedReader):

            file = file_path
            size = os.fstat(self.file.fileno()).st_size
        elif isinstance(file_path, str):
            file = open(file_path, "rb")
            size = os.fstat(file.fileno()).st_size
        elif isinstance(file_path,bytes):
            self.file = BytesIO()
            self.file.write(file_path)  # 注意要写入bytes类型数据
            self.file.flush()
            size = len(file_path)

        file.seek(0)
        """
        result  : 

        {
         00 : {   01  :     {type : DS/TS,
                    flag : range,
                    sizeBit : range,
                    size : range,
                    bitorder : big
                    data : range},
                    }
        
        
        }
        """

        result = OrderedDict()

        file.seek(0)

        current_CSM = -1
        current_DS = -1
        current_DS_d = OrderedDict()
        while True:
            if file.tell() >= size:
                if current_CSM >= 0:
                    result[current_CSM] = current_DS_d
                break

            if current_DS < 0:

                content = file.read(1)
                if content == CSM:
                    if current_CSM >= 0:
                        result[current_CSM] = current_DS_d
                    current_CSM = file.tell() - 1
                    current_DS = -1
                    current_DS_d = OrderedDict()
                    continue


                if content in DS_LIST:
                    current_DS = file.tell() - 1

                continue

            """"FF E0 xx xx xx xx| aa EF xx xx xx xx | dd ff  """
            # print(f"current_DS : {current_DS}")
            current_DS_d[current_DS] = self.parse_DS(file)
            current_DS = -1

        return result
    def parse_DS(self,file : _io.BufferedReader,index : int = -1,dict_obj = None):
        if index >= 0:
            file.seek(index)
        else:
            file.seek(file.tell()-1)


        if dict_obj == None:
            dict_obj = {}
        s = file.tell()

        T = file.read(1)

        if T == TS:
            dict_obj["type"] = "TS"
        elif T == BS:
            dict_obj["type"] = "BS"



        to = file.tell() + TEF_SIZE
        dict_obj["flag"] = bitRange(file,(file.tell(),to))
        file.seek(to)


        to = file.tell() + DLD_SIZE
        sizeBit = bitRange(file,(file.tell(),to))
        file.seek(to)
        bitOrder = DLD_BITODER



        size = int.from_bytes(sizeBit.value(),bitOrder)


        dict_obj["sizeBit"] = sizeBit
        dict_obj["size"] = size
        dict_obj["bitorder"] = bitOrder



        to = file.tell() + size
        dict_obj["data"] = bitRange(file,(file.tell(),to))
        file.seek(to)


        dict_obj["range"] = bitRange(file,(s,file.tell()))
        return dict_obj


class CdcDecoder(CdcParser):

    def __init__(self,file_path = None,print_f = print):
        CdcParser.__init__(self,file_path,print_f)

    def decode(self,file_path = None,out_dictFormat = False,use_bitrange = False,use_bitrange_minSize = 1024):
        """
        :param out_dictFormat: 是否使用字典类型返回？
        :param use_bitrange: 是否使用bitrange类型返回数据？（仅二进制有效）
        :param use_bitrange_minSize: 当字节数多余这个值的时候使用bitrange，否则直接返回数据 (仅在use_bitrange = True有效)
        :return:
        """
        parser_result = self.parse(file_path)
        # print(f"debug:{parser_result}")
        # print(parser_result[0][1]["sizeBit"].value())
        # print(parser_result)
        result = []
        for Csm in parser_result.values():
            t = []
            for Ds in Csm.values():
                # print(f"debug:{Ds}")
                Type = Ds["type"]
                flag = Ds["flag"].value()
                size = Ds["size"]
                data : bitRange = Ds["data"]

                if Type == "TS":
                    Encoding = Tef_dict[flag] if Tef_dict.get(flag,None) != None else "UTF-8"
                    data = data.value().decode(Encoding)
                    if out_dictFormat:
                        t.append( {"encoding" : Encoding,"data":data})
                    else:
                        t.append(data)
                elif Type == "BS":
                    if use_bitrange and size >= use_bitrange_minSize:
                        data = data
                    else:
                        data = data.value()
                    if out_dictFormat:
                        t.append( {"encoding" : flag,"data":data})
                    else:
                        t.append(data)

            result.append(t)


        return result


class CdcEncoder():
    def __init__(self, file_path, print_f = print,mode = "wb",flush = True):
        self.print = print_f
        if isinstance(file_path, (_io.BufferedWriter,_io.BytesIO)):

            self.file = file_path
        elif isinstance(file_path, str):
            self.file = open(file_path, mode)



        self.flush = flush
        self.buffer = []

    @dealError
    def __del__(self):
        if not getattr(self.file,"closed",True):
            self.file.close()
            return
        else:

            self.file.close()





    def write(self,*args,**kwargs):
        self.file : _io.BufferedWriter

        self.file.write(*args,**kwargs)
        if self.flush:
            self.file.flush()

    def is_list_of_non_empty_lists(self,var):
        # 检查变量是否是列表、非空，且所有元素都是非空列表
        return (
            isinstance(var, list) and
            len(var) > 0 and
            all(isinstance(item, list) and len(item) >= 0 for item in var)
        )

    def parse_single(self,data,encoding = "UTF-8",args = [] , kwargs = {},SIZE = 0,check_path = True):


        """
        对于所有数据先整理成[[dict]]的形式
        然后添加到self.buffer
        其中dict形式:
        {
        :type
        :flag
        :size : int
        :bitorder : big
        : data : { "format" : "data",
                    "value" : }
                    \
                    {"format" : "file",
                    "value" : fileobj,
                    "kwargs",
                    "args",
                    },
                    {
                    "format" : "function", # 此时SIZE = 必填,且必须一致，否则会出错
                    "value" : "funcobj",
                    "kwargs" :
                    "args" :
                    }
        }
        :param data:
        :return:
        """
        if (check_path and isinstance(data,str) and os.path.exists(data) and os.path.isfile(data)) or isinstance(data,_io.BufferedReader):
            flag = RPF
            Type = "BS"
            file = open(data,"rb") if not isinstance(data,_io.BufferedReader) else data
            size =   os.fstat(file.fileno()).st_size
            bitorder = "big"
            Data = {
                "format" : "file",
                "value" : file,
                "args" : args if args != [] else [1024],
                "kwargs" : kwargs
            }
        elif isinstance(data,str):
            encoding = encoding if Tef_dict_opposite.get(encoding,None) != None else "UTF-8"
            data = data.encode(encoding)
            flag = Tef_dict_opposite[encoding]
            size = len(data)
            Type = "TS"
            bitorder = "big"
            Data = {"format":"data","value":data}
        elif callable(data):
            flag = RPF
            Type = "BS"
            size =   SIZE
            bitorder = "big"
            Data = {
                "format" : "file",
                "value" : data,
                "args" : args,
                "kwargs" : kwargs
            }
        elif isinstance(data,bytes):
            flag = RPF
            Type = "BS"
            size = len(data)
            bitorder = "big"
            Data = {
                "format": "data",
                "value": data,
            }
        else:
            return {}
        return {
            "type":Type,
            "flag":flag,
            "size":size,
            "bitorder":bitorder,
            "data":Data
        }

    def Flush(self):
        self.file : _io.BufferedWriter
        # self.print(self.buffer)
        for Csm in self.buffer:
            self.write(CSM)

            # self.print(f"write {CSM}")

            for Ds in Csm:
                if Ds["type"] == "TS":
                    self.write(TS)
                elif Ds["type"] == "BS":
                    self.write(BS)
                self.write(Ds["flag"])

                size_pos = self.file.tell()
                self.write(Ds["size"].to_bytes(DLD_SIZE,byteorder=Ds["bitorder"]))
                size = 0
                while True:
                    d ,r= self.get_data(Ds["data"])
                    if not d:
                        if Ds["data"]["format"] == "file":
                            f = Ds["data"]["value"]
                            if not f.closed:
                                f.close()
                        break

                    self.write(d)
                    size += len(d)
                    if not r:
                        break

                if size != Ds["size"]:
                    # self.print(f"记录的大小{size}!=指定的大小{Ds['size']} 更改大小中")
                    # new_fd = os.dup(self.file.fileno())
                    # self.file = open(new_fd,"rb+")
                    # self.file.seek(size_pos)
                    # self.file.write(size.to_bytes(DLD_SIZE,byteorder=Ds["bitorder"]))
                    # new_fd = os.dup(self.file.fileno())
                    # self.file.close()
                    # self.file = open(new_fd,"ab")


                    self.print(f"记录的大小{size}!=指定的大小{Ds['size']} 更改大小中")
                    # new_fd = os.dup(self.file.fileno())
                    # self.file = open(new_fd,"rb+")
                    self.file.seek(size_pos)
                    self.file.write(size.to_bytes(DLD_SIZE,byteorder=Ds["bitorder"]))
                    # new_fd = os.dup(self.file.fileno())
                    # self.file.close()
                    # self.file = open(new_fd,"ab")
        self.file.flush()
    def add_CSM(self,value = [],flush = True,_index = "new",UseDict = False):

        value = [(i if  (UseDict and isinstance(i,dict)) else self.parse_single(i))  for i in value  ]
        if _index != "new" and len(self.buffer) >= 1:
            _index : int
            self.buffer[_index]+= value
        else:
            self.buffer.append(value)
        if flush and bool(value):
            self.Flush()
            self.buffer = []
        return value

    def add_newFile(self,value = [],flush = True):

        for i in value:
            self.add_CSM(i,flush,"new")
        return value

    def add_single(self,value , flush = True,_index = "new"):
        return self.add_CSM([value],flush,_index)

    def get_data(self,Dict):
        if Dict["format"] == "data":
            return (Dict["value"],False)
        if Dict["format"] == "file":
            f : _io.BufferedReader = Dict["value"]
            args = Dict["args"]
            kwargs = Dict["kwargs"]
            READ  = f.read(*args,**kwargs)
            return (READ,bool(READ))
        if Dict["format"] == "function":
            f  = Dict["value"]
            args = Dict["args"]
            kwargs = Dict["kwargs"]
            READ = f(*args, **kwargs)
            return (READ, bool(READ))



