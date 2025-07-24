import copy
import re,math
import warnings

"""本模块基本单位:字节"""
Size_level_dict =  {
    "B" : 1,
    "KB" : 1024,
    "MB" : 1024**2,
    "G" : 1024**3,
    "T" : 1024**4,
    "PB" : 1024**5,
    "EB" : 1024**6,
    "ZB" : 1024**7,
    "YB" : 1024**8
}



Size_list = ["B","KB","M","G","T","P","E","Z","Y"]
Size_unit_convert = {
    "字节" : "B",
    "By".upper() : "B",
    "Bytes".upper() : "B",

    "千字节" : "KB",
    "Kilobytes".upper() : "KB",
    "K" : "KB",
    "K-byte".upper() : "KB",
    "KiB".upper() : "KB",

    "兆字节" : "M",
    "MB".upper() : "M",
    "Megabytes".upper() : "M",
    "M-Byte".upper() : "M",
    "MiB".upper() : "M",


    "吉字节": "G",
    "Gigabyte".upper(): "G",
    "Gigabytes".upper(): "G",
    "G-byte".upper(): "G",
    "GiB".upper(): "G",
    "GB".upper() : "G",

    "太字节": "T",
    "Terabyte".upper(): "T",
    "Terabytes".upper(): "T",
    "T-byte".upper(): "T",
    "TiB".upper(): "T",
    "TB".upper() : "T",

    "拍字节": "P",
    "Petabyte".upper(): "P",
    "Petabytes".upper(): "P",
    "P-byte".upper(): "P",
    "PiB".upper(): "P",
    "PB".upper() : "P",

    "艾字节": "E",
    "Exabyte".upper(): "E",
    "Exabytes".upper(): "E",
    "E-byte".upper(): "E",
    "EiB".upper(): "E",
    "EB".upper() :"E",

    "泽字节": "Z",
    "Zettabyte".upper(): "Z",
    "Zettabytes".upper(): "Z",
    "Z-byte".upper(): "Z",
    "ZiB".upper(): "Z",
    "ZB".upper():"Z",

    "尧字节": "Y",
    "Yottabyte".upper(): "Y",
    "Yottabytes".upper(): "Y",
    "Y-byte".upper(): "Y",
    "YiB".upper(): "Y",
    "YB".upper() :"Y"
}
for i in Size_list:
    Size_unit_convert[i] = i



class Size():
    # Size_list = Size_list
    BaseSize = -1
    SaveBit = 2
    default_Type = str

    allow_Type = [str,int,tuple,float]

    re_check = r"(\d+(?:\.\d+)?)([a-zA-Z]+)"
    re_check_numOnly = r"\d+\b(?![^\s]*[a-zA-Z])"

    def __init__(self,Size):
        self.reset(Size)



    def _round_(self,num,n = SaveBit):
        if n > 0:
            return round(num,n)
        elif n == 0:
            return int(num)
        else:
            return num

    def __str__(self):

        b = int(math.log(self.BaseSize,1024)) if self.BaseSize > 0 else 0
        return f"{self._round_(self.BaseSize/(1024**b) , self.SaveBit)}{Size_list[b]}"

    def string(self,Basesize = BaseSize,savebit = SaveBit,Designated_Units = None,Type = -1):
        if (not Type) or (isinstance(Type,int) and Type <= 0):
            Type = self.default_Type
        elif Type not in self.allow_Type:
            warnings.warn(f"不合法的参数Type:{Type} 应为:{self.allow_Type}.以自动设置为默认值:{self.default_Type}")
            Type = self.default_Type

        if Basesize < 0:
            Basesize = self.BaseSize
        if Designated_Units and Designated_Units.upper() not in Size_unit_convert:
            Designated_Units = None

        if Designated_Units:
            b = Size_list.index(Size_unit_convert[Designated_Units.upper()])
        else:
            b = int(math.log(Basesize, 1024))
            b = b if b < len(Size_list) else len(Size_list) - 1


        return self._transfromType_((self._round_(Basesize / (1024 ** b), savebit) , Size_list[b]),Type)
        # return f"{self._round_(Basesize / (1024 ** b), savebit)}{Size_list[b]}"



    def Expanding(self,n = -1,v = BaseSize,sep = " ",Type = -1):
        if v < 0:
            v = self.BaseSize

        if (not Type) or (isinstance(Type,int) and Type <= 0):
            Type = self.default_Type
        elif Type not in self.allow_Type:
            warnings.warn(f"不合法的参数Type:{Type} 应为:{self.allow_Type}.以自动设置为默认值:{self.default_Type}")
            Type = self.default_Type

        # print(v)

        b = int(math.log(v, 1024))
        b = b if b < len(Size_list) else len(Size_list) - 1
        # print(b,int(v / (1024 ** b)),(1024**b),sep=" ")

        if b == 0 or n == 0:
            if Type == str:
                return self.string(v, 0,Type=Type)
            else:
                return [self.string(v, 0,Type=Type)]


        if n != 0:
            if Type == str:
                return self.string(v,0,Type=Type) + sep+self.Expanding(n-1,v - int(v / (1024 ** b))*(1024**b) ,sep,Type=Type)
            else:
                # print(type(self.string(v,0,Type=Type)),type(self.Expanding(n-1,v - int(v / (1024 ** b))*(1024**b) ,sep,Type=Type)))
                return [self.string(v,0,Type=Type)] + self.Expanding(n-1,v - int(v / (1024 ** b))*(1024**b) ,sep,Type=Type)

    def find_from_string(self,string : str):
        result = 0
        for i in re.findall(self.re_check,string):
            i = list(i)
            if i[-1] not in Size_unit_convert:
                warnings.warn(f"'{string}'中遇到未知单位{i[-1]}",Warning)
                continue
            i[-1] = Size_unit_convert[i[-1].upper()]
            if i[-1] in Size_list:
                result += int(float(i[0])*(1024**(Size_list.index(i[-1]))))


        for i in re.findall(self.re_check_numOnly,string):
            try:
                result += int(i)
            except Exception as e:
                warnings.warn(f"'{string}'中添加{i}遇到未知错误{e}",Warning)

        return result

    def reset(self,Size : int):
        if isinstance(Size, int):
            self.BaseSize = Size
        if isinstance(Size, str):
            self.BaseSize = self.find_from_string(Size)
        if isinstance(Size, float):
            self.BaseSize = int(Size)
        if type(Size) == type(self):
            self.BaseSize = Size.BaseSize


    def Int(self):
        return self.BaseSize

    def __int__(self):
        return self.BaseSize

    def __add__(self, other):
        if isinstance(other,int):
            self.BaseSize += other
            return self
        if isinstance(other,str):
            self.BaseSize += self.find_from_string(other)
            return self

        if isinstance(other,Size):
            self.BaseSize += other.BaseSize
            return self

    def __sub__(self, other):
        if isinstance(other,int):
            self.BaseSize = abs(self.BaseSize - other)
            return self
        if isinstance(other,str):
            self.BaseSize = abs(self.BaseSize - self.find_from_string(other))
            return self

        if isinstance(other,Size):
            self.BaseSize = abs(self.BaseSize - other.BaseSize)
            return self

    def _formToInt_(self,other):
        if isinstance(other,int):
            return other
        if isinstance(other,float):
            return int(other)
        if isinstance(other,str):
            return self.find_from_string(other)
        if isinstance(other,Size):
            return other.BaseSize

    def _transfromType_(self,data : tuple , Type = -1):
        if (not Type) or (isinstance(Type,int) and Type <= 0):
            Type = self.default_Type
        elif Type not in self.allow_Type:
            warnings.warn(f"不合法的参数Type:{Type} 应为:{self.allow_Type}.以自动设置为默认值:{self.default_Type}")
            Type = self.default_Type

        if not (isinstance(data[0],int) or isinstance(data[0],float)) and (isinstance(data[1],str)):
            warnings.warn(f"不合法的参数data:{data} 应为(float/int , str)")
            return ""


        if Type == str:
            return "{}{}".format(*data)
        if Type == int:
            return int(data[0])
        if Type == float:
            return float(data[0])
        if Type == tuple:
            return data






    def __lshift__(self, other:int):
        self.BaseSize *=1024**other
        return self
    def __rshift__(self, other:int):
        self.BaseSize = int(self.BaseSize/1024**other)
        return self

    def __lt__(self, other):
        other = self._formToInt_(other)
        return self.BaseSize < other

    def __le__(self, other):
        other = self._formToInt_(other)
        return self.BaseSize <= other

    def __eq__(self, other):
        other = self._formToInt_(other)
        return self.BaseSize == other

    def __ne__(self, other):
        other = self._formToInt_(other)
        return self.BaseSize != other

    def __gt__(self, other):
        other = self._formToInt_(other)
        return self.BaseSize > other

    def __ge__(self, other):
        other = self._formToInt_(other)
        return self.BaseSize >= other

    def __mul__(self, other):
        temp = copy.copy(self)
        if isinstance(other,int) or isinstance(other,float):
            temp.BaseSize *= other
            return temp

if __name__ == "__main__":
    print(Size(3935570231).Expanding())
    # print(Size("10.154024G").Expanding(Type=tuple))
    # print((Size("10G")+"1MB"+364574).Expanding())
    # print(int(Size("10G")))
    ...