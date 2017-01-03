import re
import pdb

import pyuppaal

import logging 
import copy

import pydbm 

logging.basicConfig(level=logging.DEBUG)

my_logger = logging.getLogger('Parsing TA')

class Sync:
    def __init__(self, channel, type):
        assert(type in ('?', '!'))
        self.channel = channel
        self.type = type    
    def matches(self, sync2):
        return self.channel == sync2.channel and \
            (self.type, sync2.type) in [('?', '!'), ('!', '?')]
    def __str__(self):
        return self.channel.name + self.type

class Channel:
    def __init__(self, name):
        self.name = name 
    def getSync(self, c):
        return Sync(self, c) 
    def __str__(self):
        return self.name

class Action(str):
    pass

class Declaration:
    def __init__(self, type, name, isconst=False, init_val = None):
        self.type = type
        self.name = name
        self.isconst = isconst
        if self.type == 'int': # TODO is it hack?
            self.init_val = int(init_val)
        else:
            self.init_val = init_val
    def __str__(self):
        r = ''
        if self.isconst:
            r+= 'const '
        r+=self.type + ' ' + self.name
        if self.init_val:
            r += ' = ' + self.init_val
        return r

class Locations(dict):    
    def __init__(self, **args):
        dict.__init__(self, **args)
        self._updateHash()
    def __setitem__(self, k, v):
        dict.__setitem__(self, k, v) 
        self._updateHash()
    def _updateHash(self):
        self._hash = 0
        for v in self.values():
            self._hash += hash(v)
    def __hash__(self):
        return self._hash
    def __eq__(self, arg2):
        return dict.__eq__(self, arg2)

def parse_declarations(arg):
    ss = arg.split('\n')     
    for s in ss:
        if s.find('//')==0:
            continue
        if re.search('^\s*$', s):
            continue        
        r = re.search('^\s*(\w+)\s+(\w+)\s*;\s*$', s)
        if r:
            yield (Declaration(type=r.group(1), name=r.group(2)))
            continue
        r = re.search('^\s*const\s+int\s+(\w+)\s*=\s*(\d+)\s*;\s*$', s)
        if r:
            yield (Declaration(type='int', name=r.group(1), isconst = True, init_val = r.group(2)))
            continue
        my_logger.error("can't parse declaration " + s)

def parse_invariant_or_guard(guard_str, clocks, consts):
    if guard_str == '':
        return None
    guard_str = guard_str.replace('&&', '__AND__')
    guard_str= '&'.join(['(' + s + ')' for s in guard_str.split('__AND__')])
    c = compile(guard_str, "<guard>", 'eval') 
    a = dict(clocks.items() + consts.items()) 
    try:
        dbm = eval(c, a)            
        assert(isinstance(dbm, pydbm.Federation))
    except Exception as e:
        my_logger.error('can\'t parse expression "' + guard_str + '": ' + str(e))
        dbm = None
    return dbm

def parse_update(update_str, clocks, consts):
    if update_str == '':
        return []
    update_l = update_str.split(',')        
    ret = []
    for s in update_l:
        r = re.search('^\s*([a-zA-Z_]\w*)\s*=(.*)', s)
        if not r:
            my_logger.error("Can't parse update " + s)
        clock_name = r.group(1)
        if clocks.has_key(clock_name):
            clock = clocks[clock_name]
        else:
            my_logger.error('assigning to non-clock variable in ' + s)
            continue
        expr_str = r.group(2).strip()
        c = compile(expr_str, "<action>", 'eval') 
        try:
            value = eval(c, copy.copy(consts))
            assert(isinstance(value, int))
        except Exception as e:
            my_logger.error('can\'t parse update value"' + expr_str + '": ' + str(e))
            continue
        ret.append((clock, value))
    return ret

class ClockBounds(dict):
    def __init__(self, context):        
        for clock in context.clocks:
            self[clock] = None
    def updateBoundsByUpdateList(self, update):
        for (clock, value) in update:
            if self[clock] is None:
                self[clock] = value
            else:
                self[clock] = max(self[clock], value)
    def updateBoundsByGuardInvariantExpr(self, expr, clocks, constants):
        if not expr:
            return
        class A:
            def __init__(self, clock, cb):
                self.clock = clock 
                self.cb = cb
            def __sub__(self, arg):
                raise TypeError("diagonal constraints are not supported")
        def f(self, arg):
            if not type(arg) == int:
                raise TypeError("Comparing clock to non-int")
            if self.cb[self.clock] is None:
                self.cb[self.clock] = arg
            else:
                self.cb[self.clock] = max(self.cb[self.clock], arg)
            return False # we should return false 
        for s in ('__le__', '__ge__', '__lt__', '__gt__', '__eq__', '__ne__'): # defining the rest of class A
            setattr(A, s, f) 
        a = dict(constants.items())        
        expr = expr.replace('&&', 'and')
        expr= '&'.join(['(' + s + ')' for s in expr.split('and')])
        for (name, clock) in clocks.items():
            a[name] = A(clock, self)            
        try:
            c = compile(expr, "<guard>", 'eval')
            eval(c, a)            
        except Exception as e:
            my_logger.error('can\'t parse expression "' + expr + '": ' + str(e))

def _transition_str(self):
    s = str(self.source) + '->' + str(self.target) + '(' + str(self.action)
    if not self.controllable:
        s += ', uncontrollable'
    if self.synchronisation:
        s += ', ' + str(self.synchronisation)
    s += ')'
    return s

def getTemplateByName(self, name):
    ts = [t for t in self.templates if t.name == name] 
    if len(ts) != 1:
        raise KeyError
    return ts[0]
    
def getLocationByName(self, name):
    ls = [l for l in self.locations if l.name == name] 
    if len(ls) != 1:
        raise KeyError
    return ls[0]

def parse_clocks(fn): # returns Context with all the clocks in TA
    f = open(fn)
    nta = pyuppaal.NTA.from_xml(f)
    ret = pydbm.Context()
    #parsing global clocks
    for declaration in parse_declarations(nta.declaration): # parsing global chans and clocks and const in declarations
        if declaration.type == 'clock':            
            ret.addClockByName(declaration.name)
    for template in nta.templates: # parsing local clock declarations
        for declaration in parse_declarations(template.declaration):            
            if declaration.type == 'clock':
                clock_name = template.name + '.' + declaration.name
                ret.addClockByName(clock_name)                        
    return ret

def parse_xml(fn, context=None):
    f = open(fn)
    nta = pyuppaal.NTA.from_xml(f)
    #currently we're looking them only in declaration section but probably we should also look in system section
    channels = {}
    nta.clocks = {}
    if context:
        nta_clock_names     = set([clock.name for clock in parse_clocks(fn).clocks])
        context_clock_names = set([clock.name for clock in context         .clocks])
        assert(nta_clock_names <= context_clock_names)
        nta.context = context
    else:
        nta.context = parse_clocks(fn)
    nta.global_consts = {}    
    for declaration in parse_declarations(nta.declaration): # parsing global chans and clocks and const in declarations
        if declaration.type  == 'chan':
            channels[declaration.name] = Channel(declaration.name)
        elif declaration.type == 'clock':            
            nta.clocks[declaration.name] = nta.context[declaration.name] 
        elif declaration.type == 'int' and declaration.isconst:
            nta.global_consts[declaration.name] = declaration.init_val
        else:
             my_logger.error('ignoring declaration "' + str(declaration) + '"')
    for template in nta.templates: # parsing local clock declarations
        template.clocks = {}
        for declaration in parse_declarations(template.declaration):            
            if declaration.type == 'clock':
                clock_name = template.name + '.' + declaration.name
                template.clocks[declaration.name] = nta.context[clock_name]                 
            else:
                 my_logger.error('ignoring declaration "' + str(declaration) + '"')
    nta.clock_bounds = ClockBounds(nta.context)
    nta.__class__.getTemplateByName = getTemplateByName
    for template in nta.templates:
        clocks = dict(nta.clocks.items() +  template.clocks.items())
        template.__class__.getLocationByName = getLocationByName
        template.forward = {} 
        for location in template.locations:            
            invariant_str = str(location.invariant)
            nta.clock_bounds.updateBoundsByGuardInvariantExpr(invariant_str, clocks, nta.global_consts) 
            location.invariant = parse_invariant_or_guard(invariant_str, clocks, nta.global_consts) or nta.context.getTautologyFederation() # we're redefining invariant (not it's dbm)
            location.invariant_str = invariant_str
            location.name = str(location.name) # we don't need coordinates which are produced by pyuppaal
            location.template = template            
            template.forward[location] = []
            location.__class__.__str__ = lambda self: (self.template.name + '.' + self.name) # TODO hack here, it's better to form a new class
        for transition in template.transitions:
            guard_str = str(transition.guard)
            nta.clock_bounds.updateBoundsByGuardInvariantExpr(guard_str, clocks, nta.global_consts) 
            transition.template = template
            transition.guard = parse_invariant_or_guard(guard_str, clocks, nta.global_consts) or nta.context.getTautologyFederation()
            transition.guard_str = guard_str
            template.forward[transition.source].append(transition)
            if transition.action:
                transition.action = Action(transition.action)
            else:
                transition.action = None
            transition.update= parse_update(str(transition.assignment), clocks, nta.global_consts)
            transition.__class__.__str__ = _transition_str 
            nta.clock_bounds.updateBoundsByUpdateList(transition.update)
            del transition.assignment
            if str(transition.synchronisation):
                sync_type = str(transition.synchronisation)[-1]
                channel_name = str(transition.synchronisation)[:-1]
                assert(sync_type in ['?', '!'])
                if not channels.has_key(channel_name):
                    channels[channel_name] = Channel(channel_name)
                transition.synchronisation = channels[channel_name].getSync(sync_type)
            else:
                transition.synchronisation = None
    return nta

class NTAState:
    def __init__(self, nta):  
        self.nta = nta
        self.federation = nta.context.getZeroFederation()
        self.locations = Locations() # we need hashable locations here
        for template in nta.templates:
            self.locations[template] = template.initlocation
    def copy(self):
        ret = copy.copy(self)
        ret.locations = copy.copy(self.locations)
        ret.federation = self.federation.copy()         
        return ret
    def delay(self):
        ret = self.copy()
        ret.federation = ret.federation.up()
        for template in self.nta.templates:
            ret.federation &= self.locations[template].invariant
        return ret
    def extrapolateMaxBounds(self):
        ret = self.copy()
        ret.federation = ret.federation.extrapolateMaxBounds(self.nta.clock_bounds)
        return ret
    def isEmpty(self):
        return self.federation.isEmpty()
    def delay(self):
        ret = self.copy()
        ret.federation = ret.federation.up()
        ret._applyInvariants() 
        return ret            
    def takeTransition(self, transition, transition2=None):
        if (not transition2) and transition.synchronisation:
            my_logger.error('Transition has synchronisation but is taken without paired transition')
            return None
        if (transition2 and ( \
            (not (transition.synchronisation and transition2.synchronisation)) or \
            (not transition.synchronisation.matches(transition2.synchronisation)) ) ):
            my_logger.error('Two transitions are  given but they are not synchronized')
            return None
        if transition.source!= self.locations[transition.template] or \
            transition2 and transition2.source != self.locations[transition2.template]:
             my_logger.error('Source location for transition doesn\'t match')
             return None
        if transition2:
            update = transition.update + transition2.update
            guard = transition.guard & transition2.guard
            target_invariant = transition.target.invariant & transition2.target.invariant
        else:
            update = transition.update
            guard = transition.guard
            target_invariant = transition.target.invariant
        ret = self.copy()        
        ret.federation &= guard
        if ret.federation.isEmpty():
            return None
        for (clock, value) in update:
            ret.federation = ret.federation.updateValue(clock, value)
        ret.federation&=target_invariant
        if ret.federation.isEmpty():
            return None
        ret.locations[transition.target.template]  = transition.target
        if transition2:
            ret.locations[transition2.target.template] = transition2.target
        return ret
    def _applyInvariants(self):
        for loc in self.locations.values():
            if loc.invariant:
                self.federation &= loc.invariant     
    def __str__(self):
        ret = '(' +  ', '.join([t.name + '.' + self.locations[t].name for t in self.nta.templates]) + ')'
        ret +=  str(self.federation)
        return ret 
    def __eq__(self, arg2):
        return (self.locations == arg2.locations) and (self.federation == arg2.federation)
    def __ne__(self, arg2):
        return not (self == arg2)


if __name__ == '__main__':
    import sys
    parse_xml(sys.argv[1])
