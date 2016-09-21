# -*- coding:utf-8 -*-

from __future__ import print_function

import dis
import textwrap
import types

import six

def dis_code(code):
    u"""    
        反汇编 字节码 
    """
    for const in code.co_consts:
        if isinstance(const,types.CodeType):
            dis_code(const)
    print ("")
    print (code)
    dis.dis(code)


def test(code,vm=None):
    u"""  测试
        -- code : 源码
    """
    code = textwrap.dedent(code) #去多余空格,格式化
    
    code = compile(code,"<test>","exec",0,1)
    
    #dis_code(code)

    if vm:
        vm.run_code(code)


if '__main__' == __name__:

    test("""\
        a = 6
        b = 2
        print a + b
        print a - b
        print a * b
        print a / b
        print a ** b
        print a % b
        print a << b
        print a >> b
        print a&b
        print a|b
        print a^b

        #x = 1
        #y = 2
        #c = x + y
        #f = x - y
        #d = x * y
        #e = y / x
        #def f():
        #    g = 1
        #    return g
        #f()
    """)

