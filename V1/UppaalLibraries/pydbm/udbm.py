#    Copyright 2011 Aalborg University and Peter Bulychev
#
#    This file is part of Python binding to the UPPAAL DBM library.
#
#    This binding is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This binding is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this binding.  If not, see <http://www.gnu.org/licenses/>.

import logging

import pdb

import udbm_int
import copy

my_logger = logging.getLogger('Python-UDBM')
my_logger.setLevel(logging.DEBUG)

class Clock:
    def __sub__(self, var2):
        assert(isinstance(var2, Clock)) 
        return VariableDifference([self, var2])
    def __le__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(self, None, c, False))
    def __ge__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(None, self, -c, False))
    def __lt__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(self, None, c, True))
    def __gt__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(None, self, -c, True))
    def __eq__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(self, None, c, False)) & Federation(Constraint(None, self, -c, False)) 
    def __ne__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(self, None, c, True)) | Federation(Constraint(None, self, -c, True)) 
    def __hash__(self):
        return hash(self.getFullName())
    def getFullName(self):
        if self.context.name:
            return self.context.name +'.' + self.name
        else:
            return self.name
    def __str__(self):
        return self.getFullName()

class _Clock(Clock): # clocks can be created only in this module
    def __init__(self, context, name, index):
        self.context = context
        self.index = index 
        self.name = name
        self.dbm_index = index+1

class Valuation (dict):
    def __init__(self, context):
        self.context = context
    def __setitem__(self, key, value):
        if not isinstance(key, Clock):
            assert(type(key) == str)
            l = [v for v in self.context.clocks if v.name == key]
            if len(l) != 1:
                raise KeyError
            key = l[0]
        assert(key.context == self.context)
        dict.__setitem__(self, key, value)
    def check(self):
        for v in self.context.clocks:
            if not self.has_key(v):
                my_logger.error("Clock %s is not present in clock valuation"%(v.name,))
                assert(0)

class IntValuation(Valuation):
    def __setitem__(self, key, value):
        if not (type(value) == int):
            raise TypeError
        Valuation.__setitem__(self, key, value)

class FloatValuation(Valuation):
    def __setitem__(self, key, value):
        assert(type(value) in [float, int])
        Valuation.__setitem__(self, key, value)

class VariableDifference:
    def __init__(self, vars):
        assert(len(vars) == 2)
        assert(vars[0].context == vars[1].context)
        self.vars = vars 
        self.context = vars[0].context
    def __le__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(self.vars[0], self.vars[1], c, False))
    def __ge__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(self.vars[1], self.vars[0], -c, False))
    def __lt__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(self.vars[0], self.vars[1], c, True))
    def __gt__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(self.vars[1], self.vars[0], -c, True))
    def __eq__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(self.vars[0], self.vars[1], c, False)) & Federation(Constraint(self.vars[1], self.vars[0], -c, False)) 
    def __ne__(self, c):
        assert(type(c) == int)
        return Federation(Constraint(self.vars[0], self.vars[1], c, True)) | Federation(Constraint(self.vars[1], self.vars[0], -c, True)) 

class Constraint: 
    def __init__(self, arg1, arg2, val, isStrict):            
            self.arg1 = arg1
            self.arg2 = arg2
            assert(isinstance(arg1, Clock) or (arg1 is None))
            assert(isinstance(arg2, Clock) or (arg2 is None))
            assert(not (arg1 is None) or not (arg2 is None))
            assert(type(val) == int)
            if arg1 is None and arg2 is None:
                assert(arg1.context == arg2.context)
            if arg1 is None:
                self.context = arg2.context
            else:
                self.context = arg1.context
            args = [arg1, arg2]
            dbm_indexes = [None, None]
            for i in (0,1):
                if args[i] is None:
                    dbm_indexes[i]=0
                else:
                    dbm_indexes[i] = args[i].dbm_index            
            self._constraint = udbm_int.Constraint(dbm_indexes[0], dbm_indexes[1], val, isStrict)

class Federation:
    def __init__(self, arg):
        if isinstance(arg, Constraint):
            self._fed = udbm_int.Federation(len(arg.context.clocks)+1, arg._constraint)
            self.context = arg.context
            self.context_hash = hash(arg.context)
        elif isinstance(arg, Context):
            context = arg
            self._fed = udbm_int.Federation(len(context.clocks)+1)
            self._fed.setZero()
            self.context = context 
            self.context_hash = hash(context)
        else:
            assert(0)
        for c in self.context.clocks:            
            assert(not (hasattr(self, c.name)))
            setattr(self, c.name, c) 

    def __str__(self):
            a = udbm_int.VarNamesAccessor()
            for i in range(len(self.context.clocks)):
                var = self.context.clocks[i]
                a.setClockName(var.dbm_index, var.getFullName())
            return self._fed.toStr(a).replace(' && ', ' & ').replace(' || ', ' | ')
    __repr__ = __str__
    def copy(self):
        ret = self.__class__(self.context)
        ret._fed = udbm_int.Federation(self._fed)
        return ret
    __deepcopy__ = lambda self, memo: self.copy()
    __copy__ = copy
    def __and__(self, arg2):
        assert(isinstance(arg2, Federation))
        assert(arg2.context == self.context)        
        assert(arg2.context_hash == self.context_hash) 
        ret = self.__class__(self.context)
        ret._fed = self._fed.andOp(arg2._fed)
        return ret
    def __iand__(self, arg2):        
        assert(isinstance(arg2, Federation))
        assert(arg2.context == self.context)
        self._fed &= arg2._fed
        return self
    def __or__(self, arg2):
        assert(isinstance(arg2, Federation))
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        ret = self.__class__(self.context)
        ret._fed = self._fed.orOp(arg2._fed)
        return ret
    def __ior__(self, arg2):        
        assert(isinstance(arg2, Federation))
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        self._fed |= arg2._fed
        return self
    def __add__(self, arg2):
        assert(isinstance(arg2, Federation))
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        ret = self.__class__(self.context)
        ret._fed = self._fed.addOp(arg2._fed)
        return ret
    def __iadd__(self, arg2):
        assert(isinstance(arg2, Federation))
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        self._fed += arg2._fed
        return self
    def __sub__(self, arg2):
        assert(isinstance(arg2, Federation))
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        ret = self.__class__(self.context)
        ret._fed = self._fed.minusOp(arg2._fed)
        return ret
    def __isub__(self, arg2):
        assert(isinstance(arg2, Federation))
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        self._fed -= arg2._fed
        return self
    def __invert__(self):
        return self.context.getTautologyFederation() - self
    def up(self):
        ret = self.copy()
        ret.upInPlace()
        return ret 
    def upInPlace(self):
        self._fed.up()
    def down(self):
        ret = self.copy()
        ret.downInPlace()
        return ret 
    def downInPlace(self):
        self._fed.down()
    def reduce(self, level=2):
        self._fed.mergeReduce(0, level)
        return self
    def freeClock(self, c):
        ret = self.copy()
        ret.freeClockInPlace(c)
        return ret 
    def freeClockInPlace(self, c):
        self._fed.freeClock(c.dbm_index)
    def setZero(self):
        self._fed.setZero()
        return self
    def hasZero(self):
        return self._fed.hasZero()
    def setInit(self):
        self._fed.setInit()
        return self
    def convexHullInPlace(self):
        self._fed.convexHull()
    def convexHull(self):
        ret =self.copy()
        ret.convexHullInPlace()
        return ret 
    def __eq__(self, arg2):
        assert(arg2.context == self.context)        
        assert(arg2.context_hash == self.context_hash) 
        return self._fed.eq(arg2._fed)
    def __ne__(self, arg2):
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        return not (self == arg2)
    def __le__(self, arg2):
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        return self._fed.le(arg2._fed)
    def __ge__(self, arg2):
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        return self._fed.ge(arg2._fed)
    def __lt__(self, arg2):
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        return self._fed.lt(arg2._fed)
    def __gt__(self, arg2):
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        return self._fed.gt(arg2._fed)    
    def intern(self):
        return self._fed.intern()
    def predtInPlace(self, arg2):
        self._fed.predt(arg2._fed)
    def predt(self, arg2):
        assert(arg2.context == self.context)
        assert(arg2.context_hash == self.context_hash) 
        ret = self.copy()
        ret.predtInPlace(arg2)
        return ret 
    def contains(self, valuation):
        valuation.check()
        if isinstance(valuation, IntValuation):
            p = udbm_int.IntClockValuation(len(self.context.clocks)+1)
            f = self._fed.containsIntValuation
        elif isinstance(valuation, FloatValuation):
            p = udbm_int.DoubleClockValuation(len(self.context.clocks)+1)
            f = self._fed.containsDoubleValuation
        else:
            my_logger.error("Unknown valuation type")
            assert(0)
        for v in self.context.clocks:
            p.setClockValue(v.dbm_index, valuation[v])
        return f(p) 
    def updateValue(self, clock, value):
        assert(clock.context == self.context)
        ret = self.copy()
        ret.updateValueInPlace(clock, value)
        return ret 
    def updateValueInPlace(self, clock, value):
        assert(clock.context == self.context)
        self._fed.updateValue(clock.dbm_index, value)
    def resetValue(self, clock):
        return self.updateValue(clock, 0)
    def resetValueInPlace(self, clock):
        self.updateValueInPlace(clock, 0)
    def updateIncrement(self, clock, value):
        assert(clock.context == self.context)
        ret = self.copy()
        ret.updateIncrementInPlace(clock, value)
        return ret 
    def updateIncrementInPlace(self, clock, value):
        assert(clock.context == self.context)
        self._fed.updateIncrement(clock.dbm_index, value)
    def getSize(self):
        return self._fed.size()
    def extrapolateMaxBoundsInPlace(self, a):                
        if len(a) != len(self.context.clocks):
            my_logger.error("extrapolateMaxBounds without all clocks setted")
            assert(0)
        v = udbm_int.IntVector(len(self.context.clocks)+1)                
        v.setElement(0, 0) # we don't care about first element, but let's exclude possible nedetermenism
        for clock in a.keys():
            if a[clock] is None:
                val = 0
            else:
                val = a[clock]
            v.setElement(clock.dbm_index, val)
        self._fed.myExtrapolateMaxBounds(v)
    def extrapolateMaxBounds(self, a):
        ret = self.copy()        
        ret.extrapolateMaxBoundsInPlace(a)
        return ret
    def isZero(self):
        return self == self.context.getZeroFederation()
    def isEmpty(self):
        return self._fed.isEmpty()
    def __hash__(self):
        return self._fed.hash()
    def hash(self):
        return hash(self)
    def tightenDownInPlace(self):
        self._fed.tightenDown()
    def tightenDown(self):
        ret = self.copy()
        ret.tightenDownInPlace()
        return ret
    def tightenUpInPlace(self):
        self._fed.tightenUp() 
    def tightenUp(self):
        ret = self.copy()
        ret.tightenUpInPlace()
        return ret
    def relaxUpInPlace(self):
        self._fed.relaxUp()
    def relaxUp(self):
        ret = self.copy()
        ret.relaxUpInPlace()
        return ret
    def relaxDown(self):
        ret = self.copy()
        ret.relaxDownInPlace()
        return ret
    def relaxDownInPlace(self):
        self._fed.relaxDown()
    def relaxAllInPlace(self):
        self._fed.relaxAll()
    def relaxAll(self):
        ret = self.copy()
        ret.relaxAllInPlace()
        return ret   
    def depends(self, clock):
        return self._fed.depends(clock.dbm_index)

class Context:
    def __init__(self, clock_names = [], name = None):
        self.clocks = []
        self.name = name
        for clock_name in clock_names:
            self.addClockByName(clock_name)
    def addClockByName(self, clock_name):
        clock = _Clock(self, clock_name, len(self.clocks))
        self.clocks.append(clock)
        assert(not (hasattr(self, clock_name)))
        setattr(self, clock_name, clock) 
        if hasattr(self, '_true'): # remove tautology federation from cache, cause the previos value is invalid now
            del(self._true)
    def hasClockByName(self, clock_name):
        for clock in self.clocks:
            if clock.name == clock_name:
                return True
        else:
            return False
    def setName(self, name):
        self.name = name
    def __getitem__(self, arg):
        names = [v for v in self.clocks if v.name == arg]
        if len(names)==0:
            raise KeyError
        assert(len(names)==1)
        return names[0]
    def items(self):
        return [(clock.name, clock) for clock in self.clocks]
    def getZeroFederation(self):
        return Federation(self)
    def getEmptyFederation(self):
        if not hasattr(self, '_false'):
            self._false = (~self.getTautologyFederation()).reduce()
        return self._false.copy()
    def getTautologyFederation(self):
        if not hasattr(self, '_true'):
            self._true = (self.clocks[0] > 0) | (self.clocks[0] <= 0)
            self._true = self._true.reduce()
        return self._true.copy()    
    def __hash__(self):
        return hash(tuple([clock.name for clock in self.clocks]))
