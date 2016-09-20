# -*- coding:utf-8 -*-

from __future__ import print_function
import operator
import dis

u"""
    1
    基于栈的 解释器
"""

class FlyMachine(object):
    u"""  虚拟机  """
    def __init__(self):

        #栈
        self.stack = []
        #代码
        self.code = None
        #解释器指针
        self.ip = 0
        #本地变量
        self._locals = {}

    def top(self):
        u""" 栈顶  """
        return self.stack[-1]

    def pop(self):
        u""" 出栈  """
        return self.stack.pop()

    def popn(self,n):
        u"""  n个出栈  """
        ret = []
        if n:
            ret = self.stack[-n:]
            self.stack[-n:] = []
        return ret

    def push(self,value):
        u""" 入栈  """
        return self.stack.append(value)

    def parse_byte_and_args(self):
        u"""
            每次解释 1-3个字节:
                指令 [参数]
        """

        ip = self.ip
        #byteCode ==> 指令码
        byteCode = ord(self.code.co_code[ip]) # TODO 需要写个兼容py3的
        self.ip += 1
        byteName = dis.opname[byteCode]
        argument = []
        
        # 判断指令是否有参数
        if byteCode >= dis.HAVE_ARGUMENT:
            arg = self.code.co_code[self.ip:self.ip+2]
            self.ip += 2
            #不同栈(或者说记录 常量,names,等)的下标地址
            intArg = ord(arg[0])+ (ord(arg[1]) <<8)
            if byteCode in dis.hasconst:
                arg = self.code.co_consts[intArg]
            elif byteCode in dis.hasname:
                arg = self.code.co_names[intArg]
            elif byteCode in dis.haslocal:
                arg = self.code.co_varnames[intArg]
            else:
                raise ValueError(u"现在还不支持更多的操作")
            argument = [arg]

        return byteName,argument,ip


    def dispatch(self,byteName,argument):
        u"""  调用对应的指令函数  """
        if byteName.startswith('BINARY_'):
            self.binaryOperator(byteName[7:])
        else:
            bytecode_fn = getattr(self,byteName,None)
            if not bytecode_fn:
                raise ValueError("未知的指令 %s" % byteName)
            ret = bytecode_fn(*argument)
            return ret

    def run_code(self,code):
        self.code = code
        while 1:
            byteName,argument,ip = self.parse_byte_and_args()
            #print ("-------",byteName,argument,ip)
            ret = self.dispatch(byteName,argument)
            if ret == "return":
                break

        pass

    # 栈的维护

    def LOAD_CONST(self,const):
        self.push(const)

    #names 维护

    def STORE_NAME(self,name):
        u"""  a = 1  """
        self._locals[name] = self.pop()

    def LOAD_NAME(self,name):
        u"""  使用变量  """
        if name in self._locals:
            val = self._locals[name]
        else:
            raise NameError("变量名 '%s' 不存在"% name)
        self.push(val)

    # 二元 操作 ? => 三元?-> if else
    BINARY_OPERATORS = {
        'POWER':    pow,
        'MULTIPLY': operator.mul,
        'DIVIDE':   getattr(operator, 'div', lambda x, y: None),
        'FLOOR_DIVIDE': operator.floordiv,
        'TRUE_DIVIDE':  operator.truediv,
        'MODULO':   operator.mod,
        'ADD':      operator.add,
        'SUBTRACT': operator.sub,
        'SUBSCR':   operator.getitem, # t = data[t]
        'LSHIFT':   operator.lshift,
        'RSHIFT':   operator.rshift,
        'AND':      operator.and_,
        'XOR':      operator.xor,
        'OR':       operator.or_,
    }

    def binaryOperator(self,op):
        u"""  二元 操作  """
        x,y = self.popn(2)
        self.push(self.BINARY_OPERATORS[op](x,y))

    # 打印
    def PRINT_ITEM(self):
        item = self.pop()
        print(item,end="")

    def PRINT_NEWLINE(self):
        print("")

    # 结束
    def RETURN_VALUE(self):
        u"""  over  """
        return_val = self.pop()
        print("over")
        return "return"
        


if __name__ == '__main__':
    a = 6
    b = 2
    c = (a+a)*(a/b) - a
    print(c)
    print(a + b)
    print(a - b)
    print(a * b)
    print(a / b)
    print(a ** b)
    print(a % b)
    print(a << b)
    print(a >> b)
    print(a&b)
    print(a|b)
    print(a^b)

    print("============")

    import test_ip
    test_ip.test("""\
        a = 6
        b = 2
        c = (a+a)*(a/b) - a
        print(c)
        print(a + b)
        print(a - b)
        print(a * b)
        print(a / b)
        print(a ** b)
        print(a % b)
        print(a << b)
        print(a >> b)
        print(a&b)
        print(a|b)
        print(a^b)
    """,vm = FlyMachine())
    pass
