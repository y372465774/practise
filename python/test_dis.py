import dis

def test():
    print 'test'

def func(a,b):
    c = (a+b)+(a+a) - b
    print c

    d = {}
    d['a'] = 'ac'

    test()

    l = [1,2,3]
    l[0:2] = [3,4]
    print l

    x = 1
    y = 2
    z = x * y

    def f():
        print 'a'
    class T:
        pass
    yield z

func(1,2)
print dis.dis(func)
