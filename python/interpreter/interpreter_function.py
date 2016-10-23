# -*- coding:utf-8 -*-

from __future__ import print_function
import operator
import dis
import types
import inspect
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

u"""
    3  函数
    基于栈的 解释器


python 代码的编译结果就是 PyCodeObject
typedef struct {

    PyObject_HEAD
    
    int co_argcount;        /* 位置参数个数 */
    
    int co_nlocals;         /* 局部变量个数 */
    
    int co_stacksize;       /* 栈大小 */
    
    int co_flags;
    
    PyObject *co_code;      /* 字节码指令序列 */
    
    PyObject *co_consts;    /* 所有常量集合 */
    
    PyObject *co_names;     /* 所有符号名称集合 */
    
    PyObject *co_varnames;  /* 局部变量名称集合 */
    
    PyObject *co_freevars;  /* 闭包用的的变量名集合 */
    
    PyObject *co_cellvars;  /* 内部嵌套函数引用的变量名集合 */
    
    /* The rest doesn’t count for hash/cmp */
    
    PyObject *co_filename;  /* 代码所在文件名 */
    
    PyObject *co_name;      /* 模块名|函数名|类名 */
    
    int co_firstlineno;     /* 代码块在文件中的起始行号 */
    
    PyObject *co_lnotab;    /* 字节码指令和行号的对应关系 */
    
    void *co_zombieframe;   /* for optimization only (see frameobject.c) */

} PyCodeObject;


"""

def make_cell(value):
    u""" 待研究 """
    # Thanks to Alex Gaynor for help with this bit of twistiness.#=> 曲折
    # Construct an actual cell object by creating a closure right here, # 构造一个真的闭包cell
    # and grabbing the cell object out of the function we create.#不会在创造该函数结束时被回收
    fn = (lambda x: lambda: x)(value)
    #if PY3:
    #    return fn.__closure__[0]
    #else:
    #    return fn.func_closure[0]
    print (fn.func_closure,value,fn)
    return fn.func_closure[0]

class Method(object):
    def __init__(self, obj, _class, func):
        self.im_self = obj
        self.im_class = _class
        self.im_func = func

    def __repr__(self):         # pragma: no cover
        name = "%s.%s" % (self.im_class.__name__, self.im_func.func_name)
        if self.im_self is not None:
            return '<Bound Method %s of %s>' % (name, self.im_self)
        else:
            return '<Unbound Method %s>' % (name,)

    def __call__(self, *args, **kwargs):
        if self.im_self is not None:
            return self.im_func(self.im_self, *args, **kwargs)
        else:
            return self.im_func(*args, **kwargs)



class Cell(object):
    u"""
       用于闭包
       闭包不是存在栈帧里面的,存在cell对象里面,frame 存着cell的引用
    """
    def __init__(self,value):
        
        self.contents = value

    def get(self):
        return self.contents

    def set(self,value):
        self.contents = value

class Function(object):
    u"""  函数对象  """
    __slots__ = [
        'func_code', 'func_name', 'func_defaults', 'func_globals',
        'func_locals', 'func_dict', 'func_closure',
        '__name__', '__dict__', '__doc__',
        '_vm', '_func',
    ]

    def __init__(self,name,code,globs,defaults,closure,vm):
        u"""
            name,函数名称
            code,函数代码
            globs,全局变量
            defaults,函数默认值
            closure,闭包
            vm,解析器
        """
        self._vm = vm
        self.func_code = code
        self.func_name = self.__name__ = name or code.co_name
        self.func_defaults = tuple(defaults)
        self.func_globals = globs
        self.func_locals = self._vm.frame.f_locals
        self.__dict__ = {}
        self.func_closure = closure
        self.__doc__ = code.co_consts[0] if code.co_consts else None

        #下面的还不知道是用来做什么的
        # Sometimes, we need a real Python function.  This is for that.
        kw = {
            'argdefs': self.func_defaults,
        }
        if closure:
            _test =  tuple(make_cell(0) for _ in closure)
            print ("test. what's this :",_test)
            kw['closure'] = _test#tuple(make_cell(0) for _ in closure)
        self._func = types.FunctionType(code, globs, **kw)
        
    def __repr__(self):         # pragma: no cover
        return '<Function %s at 0x%08x>' % (
            self.func_name, id(self)
        )

    def __get__(self, instance, owner):
        if instance is not None:
            return Method(instance, owner, self)
        if PY2:
            return Method(None, owner, self)
        else:
            return self

    def __call__(self, *args, **kwargs):

        #如下 情况待研究
        #if PY2 and self.func_name in ["<setcomp>", "<dictcomp>", "<genexpr>"]:
        #    # D'oh! http://bugs.python.org/issue19611 Py2 doesn't know how to
        #    # inspect set comprehensions, dict comprehensions, or generator
        #    # expressions properly.  They are always functions of one argument,
        #    # so just do the right thing.
        #    assert len(args) == 1 and not kwargs, "Surprising comprehension!"
        #    callargs = {".0": args[0]}
        #else:
        #    callargs = inspect.getcallargs(self._func, *args, **kwargs)
        callargs = inspect.getcallargs(self._func, *args, **kwargs) #参数匹配检查,个数等

        print("callargs -- __call__",callargs)

        frame = self._vm.make_frame(
            self.func_code, callargs, self.func_globals, {}
        )

        CO_GENERATOR = 32           # flag for "this code uses yield"
        if self.func_code.co_flags & CO_GENERATOR:
            gen = Generator(frame, self._vm)
            frame.generator = gen
            retval = gen
        else:
            retval = self._vm.run_frame(frame)
        return retval


class Frame(object):
    u"""  栈帧  """
    def __init__(self,f_code,f_globals,f_locals,f_back):
        
        self.f_code = f_code #函数代码对象
        self.f_globals = f_globals #全局变量
        self.f_locals = f_locals # 本地变量
        self.f_back = f_back # 前一个栈帧 链式存储

        self.stack = []
        
        if f_back:
            self.f_builtins = f_back.f_builtins
        else:
            self.f_builtins = f_globals['__builtins__']
            if hasattr(self.f_builtins,'__dict__'):
                self.f_builtins = self.f_builtins.__dict__

        self.f_lineno = f_code.co_firstlineno
        self.f_ip = 0

        if f_code.co_cellvars:
            self.cells = {}
            if not f_back.cells:
                f_back.cells = {}
            for var in f_code.co_cellvars:
                print(u"内部嵌套函数 引用变量: ",var)
                cell = Cell(self.f_locals.get(var))
                f_back.cells[var] = self.cells[var] = cell
        else:
            self.cells = None

        if f_code.co_freevars:
            if not self.cells:
                self.cells = {}
            for var in f_code.co_freevars:
                assert self.cells is not None
                assert f_back.cells,"f_back.cells: %r"%(f_back.cells)
                self.cells[var] = f_back.cells[var]

        self.block_stack = []
        self.generator = None

    def __repr__(self):
        return '<Frame at 0x%08x: %r @ %d>'%(
            id(self),self.f_code.co_filename,self.f_lineno
       )

    def line_number(self):
        u"""    
            获取当前函数执行到的行数
        """
        lnotab = self.f_code.co_lnotab
        byte_increments = six.iterbytes(lnotab[0::2])
        line_increments = six.iterbytes(lnotab[1::2])

        byte_num = 0
        line_num = self.f_code.co_firstlineno

        for byte_incr,line_incr in zip(byte_increments,line_increments):
            byte_num += byte_incr
            if byte_num > self.f_ip:
                break
            line_num += line_incr

        return line_num
            
    

class FlyMachine(object):
    u"""  虚拟机  """
    def __init__(self):

        #存放栈帧的栈
        self.frames = []
        #当前栈帧
        self.frame = None

        #当前函数返回值
        self.return_val = None

    def top(self):
        u""" 栈顶  """
        return self.frame.stack[-1]

    def pop(self):
        u""" 出栈  """
        return self.frame.stack.pop()

    def popn(self,n):
        u"""  n个出栈  """
        ret = []
        if n:
            ret = self.frame.stack[-n:]
            self.frame.stack[-n:] = []
        return ret

    def push(self,*vals):
        u""" 入栈  """
        return self.frame.stack.extend(vals)

    def push_frame(self,frame):
        self.frames.append(frame)
        self.frame = frame

    def pop_frame(self):
        self.frames.pop()
        if self.frames:
            self.frame = self.frames[-1]
        else:
            self.frame = None

    def jump(self,jump):
        u""" 指令跳转,指针改变  """
        self.frame.f_ip = jump

    def delta_jump(self,jump):
        u""" 
            JUMP_FORWARD(delta)¶
                Increments bytecode counter by delta  
        """
        self.frame.f_ip += jump

    def parse_byte_and_args(self):
        u"""
            每次解释 1-3个字节:
                指令 [参数]
                指令一个字节 -> 8位  所以理论上可以有256个
                参数2位 -> 16位 所以理论上寻址可以达到 65536个
        """

        f = self.frame
        ip = f.f_ip
        #byteCode ==> 指令码
        byteCode = ord(f.f_code.co_code[ip]) # TODO 需要写个兼容py3的
        f.f_ip += 1
        byteName = dis.opname[byteCode]
        argument = []
        
        # 判断指令是否有参数
        if byteCode >= dis.HAVE_ARGUMENT:
            arg = f.f_code.co_code[f.f_ip:f.f_ip+2]
            f.f_ip += 2
            #不同栈(或者说记录 常量,names,等)的下标地址
            intArg = ord(arg[0])+ (ord(arg[1]) <<8)
            if byteCode in dis.hasconst:
                arg = f.f_code.co_consts[intArg]
            elif byteCode in dis.hasfree:
                if intArg < len(f.f_code.co_cellvars):
                    arg = f.f_code.co_cellvars[intArg]
                else:
                    var_idx = intArg - len(f.f_code.co_cellvars)
                    arg = f.f_code.co_freevars[var_idx]
            elif byteCode in dis.hasname:
                arg = f.f_code.co_names[intArg]
            elif byteCode in dis.hasjrel:
                print("hasjrel")
                arg = f.f_ip + intArg
            elif byteCode in dis.hasjabs:
                print("hasjabs")
                arg = intArg
            elif byteCode in dis.haslocal:
                arg = f.f_code.co_varnames[intArg]
            else:
                #整数常量
                arg = intArg
            argument = [arg]

        return byteName,argument,ip


    def dispatch(self,byteName,arguments):
        u"""  调用对应的指令函数  """
        if byteName.startswith('BINARY_'):
            self.binaryOperator(byteName[7:])
        else:
            bytecode_fn = getattr(self,byteName,None)
            if not bytecode_fn:
                raise ValueError("未知的指令 %s" % byteName)
            ret = bytecode_fn(*arguments)
            return ret

    def make_frame(self,code,callargs={},f_globals=None,f_locals=None):

        print("make frame: code=%r, callargs=%s" % (code,callargs))
        if f_globals is not None:
            f_globals = f_globals
            if f_locals is None:
                f_locals = f_globals
        elif self.frames:
            f_globals = self.frame.f_globals
            f_locals = {}
        else:
            f_globals = f_locals = {
                '__builtins__': __builtins__,
                '__name__': '__main__',
                '__doc__': None,
                '__package__': None,
            }

        f_locals.update(callargs)
        frame = Frame(code,f_globals,f_locals,self.frame)
        return frame


    def run_frame(self,frame):

        self.push_frame(frame)

        while 1:
            byteName,arguments,ip = self.parse_byte_and_args()
            #print ("-------",byteName,arguments,ip)
            ret = self.dispatch(byteName,arguments)
            #print ("<---ret---->",ret)
            if ret == 'return':
                break

        self.pop_frame()

        return self.return_val

    def run_code(self,code,f_globals=None,f_locals=None):
        frame = self.make_frame(code,f_globals=f_globals,f_locals=f_locals)
        val = self.run_frame(frame)
        #while 1:
        #    byteName,argument,ip = self.parse_byte_and_args()
        #    #print ("-------",byteName,argument,ip)
        #    ret = self.dispatch(byteName,argument)
        #    if ret == "return":
        #        break

    #FUNCTIONS
    u"""
        函数解析后,变成一个 code 对象
    """

    def MAKE_FUNCTION(self,argc):
        u"""
            函数生成
        """
        #if PY3:
        #    name = self.pop()
        name = None
        code = self.pop()
        defaults = self.popn(argc) #默认参数个数
        globs = self.frame.f_globals
        fn = Function(name,code,globs,defaults,None,self)
        self.push(fn)

    def CALL_FUNCTION(self,arg):
        u"""  函数调用  """
        return self.call_function(arg,[],{})

    def CALL_FUNCTION_VAR(self,arg):
        u"""  函数调用  """
        args = self.pop()
        return self.call_function(arg,args,{})

    def CALL_FUNCTION_KW(self,arg):
        u"""  函数调用  """
        kwargs = self.pop()
        return self.call_function(arg,[],kwargs)

    def CALL_FUNCTION_VAR_KW(self,arg):
        u"""  函数调用  """
        args,kwargs = self.popn(2)
        return self.call_function(arg,args,kwargs)

    def call_function(self,arg,args,kwargs):
        u"""
        kv 参数个数 放在高位
        arg 参数个数 放在低位 
        """
        lenKw,lenPos = divmod(arg,256)
        namedargs = {}
        for i in range(lenKw):
            key,val = self.popn(2)
            namedargs[key] = val

        namedargs.update(kwargs)
        posargs = self.popn(lenPos)
        posargs.extend(args)

        func = self.pop()
        frame = self.frame

        #调用类的方法
        # func.im_self: 函数所属对象  func.im_class: 函数所属类
        if hasattr(func,'im_func'):
            # Methods get self as an implicit first parameter.
            if func.im_self:
                posargs.insert(0, func.im_self)
            # The first parameter must be the correct type.
            if not isinstance(posargs[0], func.im_class):
                raise TypeError(
                    'unbound method %s() must be called with %s instance '
                    'as first argument (got %s instance instead)' % (
                        func.im_func.func_name,
                        func.im_class.__name__,
                        type(posargs[0]).__name__,
                    )
                )
            func = func.im_func
           
        retval = func(*posargs,**namedargs)
        self.push(retval)

    def MAKE_CLOSURE(self, argc):
        u"""  闭包函数   """
        #if PY3:
        #    # TODO: the py3 docs don't mention this change.
        #    name = self.pop()
        #else:
        #    name = None
        name = None
        closure, code = self.popn(2)
        defaults = self.popn(argc)
        globs = self.frame.f_globals
        fn = Function(name, code, globs, defaults, closure, self)
        self.push(fn)



    # 栈的维护

    def LOAD_CONST(self,const):
        self.push(const)

    def POP_TOP(self):
        self.pop()


    #names 维护

    def STORE_NAME(self,name):
        u""" 存:  a = 1  """
        self.frame.f_locals[name] = self.pop()

    def LOAD_NAME(self,name):
        u""" 取: 使用变量  """
        if name in self.frame.f_locals:
            val = self.frame.f_locals[name]
        elif name in self.frame.f_globals:
            val = self.frame.f_globals[name]
        elif name in self.frame.f_builtins:
            val = self.frame.f_builtins[name]
        else:
            raise NameError("变量名 '%s' 不存在"% name)
        self.push(val)

    def STORE_FAST(self, name):
        self.frame.f_locals[name] = self.pop()

    def LOAD_FAST(self,name):
        if name in self.frame.f_locals:
            val = self.frame.f_locals[name]
        else:
            raise UnboundLocalError(
                "local variablev '%s' referenced before assignment" % name
            )
        self.push(val)

    def LOAD_GLOBAL(self, name):
        f = self.frame
        if name in f.f_globals:
            val = f.f_globals[name]
        elif name in f.f_builtins:
            val = f.f_builtins[name]
        else:
            raise NameError("global name '%s' is not defined" % name)
        self.push(val)

    def STORE_DEREF(self,name):
        self.frame.cells[name].set(self.pop())

    def LOAD_CLOSURE(self,name):
        self.push(self.frame.cells[name])

    def LOAD_DEREF(self, name):
        self.push(self.frame.cells[name].get())




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


    #比较操作
    COMPARE_OPERATORS = [
        operator.lt,
        operator.le,
        operator.eq,
        operator.ne,
        operator.gt,
        operator.ge,
        lambda x, y: x in y,
        lambda x, y: x not in y,
        lambda x, y: x is y,
        lambda x, y: x is not y,
        lambda x, y: issubclass(x, Exception) and issubclass(x, y),
    ]

    def COMPARE_OP(self, opnum):
        x, y = self.popn(2)
        self.push(self.COMPARE_OPERATORS[opnum](x, y))


    #Attrbutes and indexing 获取属性 索引查找
    def LOAD_ATTR(self, attr):
        obj = self.pop()
        val = getattr(obj, attr)
        self.push(val)

   

    #Building
    def BUILD_TUPLE(self, count):
        tp = self.popn(count)
        self.push(tuple(tp))

   
    def BUILD_LIST(self,count):
        ls = self.popn(count)
        self.push(ls)


    # Print 打印
    def PRINT_ITEM(self):
        item = self.pop()
        print(item,end="")

    def PRINT_NEWLINE(self):
        print("")


    # JUMP 跳转
    def JUMP_FORWARD(self,jump):
        self.delta_jump(jump)
        #self.jump(jump)

    def JUMP_ABSOLUTE(self,jump):
        self.jump(jump)


    def POP_JUMP_IF_FALSE(self,jump):
        val = self.pop()
        if not val:
            self.jump(jump)


    #Blocks 块
    def SETUP_LOOP(self,dest):
        self._block.append(('loop',dest))

    def POP_BLOCK(self):
        self._block.pop()

    def GET_ITER(self):
        self.push(iter(self.pop()))

    def FOR_ITER(self,jump):
        iterobj = self.top()
        try:
            v = next(iterobj)
            self.push(v)
        except StopIteration:
            self.pop()
            self.delta_jump(jump)
   
    
    # 结束
    def RETURN_VALUE(self):
        u"""  over  """
        self.return_val = self.pop()
        print("over")
        return "return"
        

    #导入 import 
    def IMPORT_NAME(self,name):
        u"""
            import name 

            level : 导入层级 >> -1 代表绝对导入或相对导入.  0,1,2表示导入包目录层级.
            fromlist : gives the names of objects or submodules that should be imported from the module given by name
        """
        level,fromlist = self.popn(2)
        frame = self.frame
        self.push(
            __import__(name,frame.f_globals,frame.f_locals,fromlist,level)
        )

    def IMPORT_FROM(self,name):
        u"""
            from xx import name
        """
        mod = self.top()
        self.push(getattr(mod,name))

    def IMPORT_STAR(self):
        u"""
            from xx import *
        """
        #TODO 没有使用 __all__ 属性
        mod = self.pop()
        frame = self.frame
        for attr in dir(mod):
            if attr[0] != '_':
                frame.frame.f_locals[attr] = getattr(mod,attr)



if __name__ == '__main__':

    import test_ip
    test_ip.test("""\
        #g = 1
        #def test(a):
        #    c = a + g
        #    print c,a,g
        #    return c

        #d = test(1)

        #def first(a,b=[],c=1,d=2):
        #    test(a)
        #    print "first"
        #first(d)

        #print("=========closure============")

        #def dec(func):
        #    print("....dec....")
        #    rc = []
        #    g = 1
        #    gg = 1
        #    def wrap(*arg,**kv):
        #        rt = func(*arg,**kv)
        #        rc.append(rt)
        #        print g
        #        gg = 2 # error gg += 2
        #        return rt
        #    return wrap

        ##def f():
        ##    return 1

        ##f = dec(f)
        ##print f()

        #@dec
        #def m():
        #    return 1

        #print m()
        import time
        print time.time()

        aa = 'a'
        b = 10
        c = 1000
        d = 999999999999

        #class T(object):
        #    def t(self):
        #        print 'i am test'

        print("======= yield===========")

        def yd():
            yield 1
            yield 2
        y = yd()
        print(y.next())
        print(y.nect())

       

   """,vm = FlyMachine())
    pass
