import sys


__all__ = ["detail_level","get_now_error_information","dealError"]

DEFAULT_PRINT_FUNC = print
DEFAULT_DETAIL_LEVEL = "common"

def dealError(func : object) -> object:
    def inner(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except Exception as e:
            DEFAULT_PRINT_FUNC(get_Error_deal_string(DEFAULT_DETAIL_LEVEL))

    return inner







explain_Error_dict = {
  "SyntaxError": {
    "name": "语法错误",
    "cause": "代码中存在语法错误，比如缺少括号、错误的缩进、使用了错误的关键字等。或代码中使用了Python不支持的语法结构。"
  },
  "IndentationError": {
    "name": "缩进错误",
    "cause": "Python使用缩进来表示代码块，不正确的缩进会导致这个错误。"
  },
  "ImportError": {
    "name": "导入错误",
    "cause": "尝试导入一个不存在的模块或包。"
  },
  "NameError": {
    "name": "名称错误",
    "cause": "使用了一个未定义的变量或函数名。"
  },
  "TypeError": {
    "name": "类型错误",
    "cause": "对一个值进行了不适合其类型的操作，比如对字符串执行数值运算。"
  },
  "ValueError": {
    "name": "值错误",
    "cause": "使用了不适当的值，比如传递了一个无效的参数给函数。"
  },
  "IndexError": {
    "name": "索引错误",
    "cause": "尝试访问列表、元组、字符串等序列中不存在的索引。"
  },
  "KeyError": {
    "name": "键错误",
    "cause": "在字典中查找一个不存在的键。"
  },
  "AttributeError": {
    "name": "属性错误",
    "cause": "访问对象不存在的属性或方法。"
  },
  "IOError": {
    "name": "输入/输出错误",
    "cause": "在文件操作中，比如打开一个不存在的文件或读写文件时发生错误。"
  },
  "OSError": {
    "name": "操作系统错误",
    "cause": "操作系统相关的错误，比如文件权限问题。"
  },
  "RuntimeError": {
    "name": "运行时错误",
    "cause": "运行时发生的错误，比如递归太深导致的最大递归深度超出。"
  },
  "RecursionError": {
    "name": "递归错误",
    "cause": "递归调用过多，超过了Python的最大递归深度限制。"
  },
  "MemoryError": {
    "name": "内存错误",
    "cause": "可用内存不足，无法分配更多的内存。"
  },
  "NotImplementedError": {
    "name": "未实现错误",
    "cause": "调用了一个只实现了接口但没有实现具体功能的抽象方法。"
  },
  "AssertionError": {
    "name": "断言错误",
    "cause": "执行`assert`语句时，条件为假。"
  },
  "ZeroDivisionError": {
    "name": "零除错误",
    "cause": "尝试除以零。"
  },
  "OverflowError": {
    "name": "溢出错误",
    "cause": "数值运算结果太大，超出了Python可以表示的范围。"
  },
  "FloatingPointError": {
    "name": "浮点错误",
    "cause": "浮点运算失败，比如对NaN或无穷大进行操作。"
  },
  "KeyboardInterrupt": {
    "name": "键盘中断",
    "cause": "用户中断了程序的执行，通常是通过按Ctrl+C。"
  }
}
detail_level = {
    "simple" : {
        "own":["ErrorTypeName","ErrorDescription"],
        "form" : "发生错误:类型:{ErrorTypeName},描述:{ErrorDescription}"},

    "common" : {
        "own":["ErrorTypeName","ErrorDescription","explainErrorTypeName","explainErrorCause"],
        "form" : "发生错误：\n"
                "类型:{ErrorTypeName}/{explainErrorTypeName}\n"
                "描述:{ErrorDescription}\n"
                "说明:{explainErrorCause}\n"
    },

    "detailed" : {
        "own":["ErrorTypeName","ErrorDescription","ErrorPlace","explainErrorTypeName","explainErrorCause"],
        "form" : "发生错误：\n"
                "类型:{ErrorTypeName}/{explainErrorTypeName}\n"
                "描述:{ErrorDescription}\n"
                "说明:{explainErrorCause}\n"
                "位置:{ErrorPlace}\n"
                "错误深度:{ErrorDeep}\n"

    }
}
detail_levels = list(detail_level.keys())
ErrorPlaceToString_Form = "\'{code}\' 位于 {file} 的 {line} 行， {function} 中\n"
def ErrorPlaceToString(ErrorPlace:list,tip = "    ",ErrorPlaceToStringForm = ErrorPlaceToString_Form,start_postion = 0,__t = ""):
    __t += tip if start_postion > 0  else ""
    if start_postion == len(ErrorPlace):
        # return __t + ErrorPlaceToStringForm.format(**ErrorPlace[start_postion])
        return ""
    return __t + ErrorPlaceToStringForm.format(**ErrorPlace[start_postion]) + ErrorPlaceToString(ErrorPlace = ErrorPlace,tip = tip,__t=__t,ErrorPlaceToStringForm = ErrorPlaceToStringForm,start_postion = start_postion+1)
def get_Error_deal_string(selected_detail_Level = detail_levels[-1]):
    if not selected_detail_Level in detail_levels:
        print(f"错误:传入的selected_detail_Level:{selected_detail_Level}不可用，应为{detail_levels}其中任一。")
        return
    Error_information = get_now_error_information(True)
    deal_string = detail_level[selected_detail_Level]["form"]
    if "ErrorPlace" in detail_level[selected_detail_Level]["own"]:
        deal_string = deal_string.replace("{ErrorPlace}",ErrorPlaceToString(Error_information["ErrorPlace"]))
    deal_string = deal_string.format(**Error_information)

    return deal_string
def get_now_error_information(get_explain = True):
    from traceback import extract_tb
    Error = {}

    exc_type, exc_value, exc_traceback = sys.exc_info()
    Error["ErrorType"] = exc_type
    Error["ErrorTypeName"] = exc_type.__name__
    Error["ErrorDescription"] = str(exc_value)
    Error["ErrorPlace"] = []
    for filename, lineno, fu, code in extract_tb(exc_traceback):
        Error["ErrorPlace"].append(
            {"file": filename,
             "line": lineno,
             "function": fu,
             "code": code
             },
        )
    Error["ErrorDeep"] = len(Error["ErrorPlace"])

    if get_explain:
        # Error["explain"] = {}
        is_in_explain_Error_dict = Error["ErrorTypeName"] in list(explain_Error_dict.keys())
        Error["explainErrorTypeName"] = explain_Error_dict[Error["ErrorTypeName"]]["name"] \
            if is_in_explain_Error_dict \
            else "未知错误类型"
        Error["explainErrorCause"] = explain_Error_dict[Error["ErrorTypeName"]]["cause"] if is_in_explain_Error_dict else ""


    return Error


if __name__ == '__main__':
    @dealError
    def t():
        try:
            assert 1 == 0
        except:
            pass
        print(get_now_error_information())
    t()



        # traceback.print_exception(*sys.exc_info())



















