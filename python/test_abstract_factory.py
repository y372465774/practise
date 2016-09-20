#-*- coding:utf-8 -*-
# 创建型设计模式
u"""
    多对象进行组合的情况
"""


"""
1 
"""
# class X_A  , class Y_A , class Z_A
class A:
    def x(self):
        return X_A()

    def y(self):
        return Y_A()

    def z(self):
        return Z_A()

# class X_B  , class Y_B , class Z_B
class B(A):
    def x(self):
        return X_B()

    def y(self):
        return Y_B()

    def z(self):
        return Z_B()

"""
    2   better
"""

class A():
    #class X , class Y ,class Z

    @classmethod
    def x(cls):
        return cls.X()

    @classmethod
    def y(cls):
        return cls.Y()

    @classmethod
    def z(cls):
        return cls.Z()

class B(A):
    #class X , class Y ,class Z

#def create(obj):
#    obj.x()
#    obj.y()
#    obj.z()
#
#def test1():
#
#    create(A())
#    create(B())

  
