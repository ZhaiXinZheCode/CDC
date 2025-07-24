import _io,io,os

import copy

import warnings
from typing import Union
from .config import FileConfig
from .Error_process import dealError
from .Size import Size



class File():

    def __init__(self,*args,print_f = print,**kwargs):
        self.print = print_f
        self.write_offset = 0


        self.load_from(*args,**kwargs)
        """



        """
        self.args = args
        self.kwargs = kwargs


    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """上下文管理器退出时关闭资源"""
        self.close()

    def __del__(self):
        """析构函数确保资源释放"""
        self.close()

    def close(self):
        """安全关闭所有资源"""
        # 关闭文件对象
        try:
            self.file.close()
        except Exception as e:
            self.print(f"关闭文件时出错: {e}")





    def load_from(self,value,range = None, mode = "rb",bufferSize = FileConfig.DEFAULT_BUFFER_SIZE ,default_pos = -1):
        """


        :param value: 传入的值，目前可以是Union[_io.BufferedReader , _io.BytesIO , str , bytes],其中str会检查是否合理
        :param bufferSize: 缓冲区大小（只有在value: str时候有效）
        :param mode: 只有在value : str时候有效
        :param default_pos: 默认指针位置，对于range存在的对象则为相对于range的位置
        :param range : 文件范围，指定为list[int,int],对于>2的列表生效,否则为使用全部对象
        :return:
        """

        self.type : str = None
        self.file : Union[_io.BufferedReader ,_io.BufferedWriter, _io.BytesIO , str , bytes] = None
        self.len : int = -1
        self.Size : int = -1 # wb = self.len
        self.Range : tuple[int,int]= None # wb 失效

        self.mode = mode

        if isinstance(value,(_io.BufferedReader)):
            self.mode = FileConfig.MODE_RB
        elif isinstance(value,(_io.BufferedWriter)):
            self.mode = FileConfig.MODE_WB
        elif self.mode not in FileConfig.MODE_ALLOWS:
            self.mode = FileConfig.MODE_RB



        self.pos : int = -1


        self.bufferSize = bufferSize if (isinstance(bufferSize , int) and bufferSize > 0)\
            else FileConfig.DEFAULT_BUFFER_SIZE



        self.value = value



        if isinstance(value ,(_io.BufferedReader,_io.BufferedWriter)):


            self.print(f"因为你当前使用的是文件流传入，因此请tm自己负责缓冲区（反正我是负责不了了），否则乖乖传入str")

            self.file = value

            self.mode = FileConfig.MODE_RB if isinstance(self.file,_io.BufferedReader) else FileConfig.MODE_WB


        elif isinstance(value,(_io.BytesIO,bytes)):
            if isinstance(value,bytes):
                value = io.BytesIO(value)

            self.print(f"对于{value}不需要建立缓冲区。 | No buffer needed for {value}.")

            self.file = value

            self.len = self.file.getbuffer().nbytes

            assert self.len >= 0

            if self.len == 0:
                self.mode = FileConfig.MODE_WB # 如果传入数组为0则一定为写入



        else:
            assert isinstance(value,str)
            if os.path.exists(value) and os.path.isdir(value):
                raise TypeError(f"路径{value}是目录（需要：可读文件/可写路径）/Path {value} is a directory (expected: file for read/valid path for write)")


            self.Path = value

            if os.path.exists(value) and os.path.isfile(value) and self.mode != FileConfig.MODE_WB:
                self.mode = FileConfig.MODE_RB
                # self.len = os.path.getsize(value)
            else:
                self.mode = FileConfig.MODE_WB
                # self.len = 0

            self.file = open(value,self.mode,buffering=self.bufferSize)

        self.type = type(self.file)
        self.len = self.__get_len()





        if isinstance(range,(list,tuple)) and len(range) >= 2:
            self.Range = [range[0],range[1]]
            assert all(isinstance(i,int) and i >= 0 for i in self.Range)

            if  self.Range[1] > self.len:
                self.Range[1] = self.len
        else:
            self.Range = None

        self.update_Size()


        self.pos = self._get_abspos_place(default_pos)





    def __get_len(self):
        # print(f"type:{self.type}")
        if self.type in [_io.BufferedReader,_io.BufferedWriter ,str]:
            return os.fstat(self.file.fileno()).st_size + self.write_offset
        if self.type in [_io.BytesIO]:
            return self.file.getbuffer().nbytes

    def update_Size(self):
        self.len = self.__get_len()
        if self.is_all_file():
            self.Size = copy.deepcopy(self.len)
        else:
            self.Size = self.Range[1] - self.Range[0]

        return self.Size


    def _get_abspos_place(self,default_pos,check_less = True,check_more = True):
        if self.mode != FileConfig.MODE_RB:
            self.update_Size()

        Range = [0, self.len] if self.is_all_file() else self.range()

        if default_pos < 0 and check_less:
            default_pos = 0

        # print(f"default_pos : {default_pos}")
        if default_pos > self.size() and check_more:
            default_pos = self.size()

        return Range[0] + default_pos



    def _get_relativePos_place(self,absPos,check_less = True,check_more = True):
        if self.mode != FileConfig.MODE_RB:
            self.update_Size()

        Range = [0,self.len] if self.is_all_file() else self.range()

        if absPos < Range[0] and check_less:
            return 0

        if absPos > Range[1] and check_more:
            return Range[1]

        return absPos - Range[0]



    def get_path(self): # read_only
        if self.type in [_io.BufferedReader,_io.BufferedWriter ,str] and hasattr(self,"Path"):
            return self.Path
        else:
            warnings.warn(f"您试图访问路径但是模式却不是只读或者传入的是文件流QAQ/you try to get the Path but the mode is not the Read-only or get the _io.BufferedReader {self.value}")


    def copy(self):
        result = File(value=self.file,range=self.Range,mode=self.mode,bufferSize=self.bufferSize,default_pos=0,print_f=self.print)
        # result.load_from(value=self.file,range=self.Range,mode=self.mode,bufferSize=self.bufferSize,default_pos=0)

        return result



    def seek(self,n = -1):
        if self.mode != FileConfig.MODE_RB:
            self.update_Size()




        target_pos = self._get_abspos_place(n,check_more= self.mode != FileConfig.MODE_WB)
        # print(f"target_pos : {target_pos} ,{self.mode} ")

        self.file.seek(target_pos)
        self.pos = self.file.tell()
        self.update_Size()
        # print(self.pos)
        return self.tell()

    # def update_pos(self):
    #     Range = [0, self.len] if self.is_all_file() else self.range()
    #     self.pos = self.file.tell() - self.Range[0]


    # @dealError
    def read(self,n = -1):
        if self.mode != FileConfig.MODE_RB:
            self.update_Size()
            warnings.warn(f"不建议在{self.mode}的模式下使用read。这可能带来奇奇怪怪的问题。")

        if self.pos != self.file.tell():
            self.file.seek(self.pos)

        Range = [0, self.len] if self.is_all_file() else self.range()

        if n < 0 or n > self.size() - self.tell():
            read_length = self.size() - self.tell()

        else:
            read_length = n
        try:

            result = self.file.read(read_length)
            self.pos = self.file.tell()

            return result
        except Exception as e:
            warnings.warn(f"发生了错误{e},返回空值")
            return b""




    def write(self,data):
        if self.mode != FileConfig.MODE_WB:
            warnings.warn(f"在{self.mode}的情况下无法写文件！")
            return

        if self.pos != self.file.tell():
            self.file.seek(self.pos)


        if (not self.is_all_file())  and self.pos + len(data) > self.range()[1]:
            left_space = self.range()[1] - self.pos
            warnings.warn(f"由于限制大小为{Size(self.size())}({self.size()}) 可写{ Size(left_space) }（{left_space}）多出的部分将会被截断")
            data = data[:left_space]
        self.file.write(data)
        self.write_offset += len(data)
        self.pos = self.file.tell()
        self.update_Size()
        return data


    def peek(self,n):
        current_pos = self.tell()
        result = self.read(n)
        self.seek(current_pos)
        return n

    def tell(self):
        Range = [0, self.len] if self.is_all_file() else self.range()
        # print(self.pos,Range)
        return self.pos - Range[0]

    def range(self):
        return [0, self.len] if self.is_all_file() else self.Range

    def size(self):
        return self.Size

    def __len__(self):
        return self.len

    def is_all_file(self) -> bool:
        return self.Range == None
if  __name__ == "__main__":
    pass