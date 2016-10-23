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
    
    dis_code(code)

    print (">-------------------------<")

    if vm:
        vm.run_code(code)


if '__main__' == __name__:

    test("""\
        g = 1
        def test(a):
            c = a + g
            print c,a,g

        test(1)

        def first():
            print "first"
        first()

    """)

