import pprint
import sys
from lang import bprint

class A(object):
    a = 'module string'

    def __init__(self):
        self.b = 'constructor string ' + str(id(self))

a = A()
a.a = A()
a.c = {1:None, 'are': ['a', 'r', 'e'], 'not':(0, False)}

p1 = pprint.pformat(a)

p2 = bprint.pformat(a)

if p1 == p2:
    sys.exit(1)
