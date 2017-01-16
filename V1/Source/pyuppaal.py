### This is the pyuppaal library source downloaded from http://people.cs.aau.dk/~adavid/python/ ##
## This library has be modified (some functions are added/removed according to our requirements).## 
##################################################################################################

#import pygraphviz
import cgi
import xml.etree.cElementTree as ElementTree
import subprocess
import re
import tempfile, os
import math

def require_keyword_args(num_unnamed):
    """Decorator s.t. a function's named arguments cannot be used unnamed"""
    def real_decorator(fn):
        def check_call(*args, **kwargs):
            if len(args) > num_unnamed:
                raise TypeError("%s should be called with only %s unnamed arguments" 
                    % (fn, num_unnamed))
            return fn(*args, **kwargs)
        return check_call
    return real_decorator

UPPAAL_LINEHEIGHT = 15
class NTA:
    def __init__(self, declaration="", system="", templates=None):
        self.declaration = declaration
        self.system = system
        self.templates = templates or []

    def add_template(self, t):
        if not t in self.templates:
            self.templates += [t]

    def to_xml(self):
        templatesxml = ""
        for t in self.templates:
            templatesxml += t.to_xml() + "\n"
        return """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE nta PUBLIC "-//Uppaal Team//DTD Flat System 1.1//EN" "http://www.it.uu.se/research/group/darts/uppaal/flat-1_1.dtd">
<nta>
  <declaration>%s</declaration>
  %s
  <system>%s</system>
</nta>""" % (cgi.escape(self.declaration), templatesxml, cgi.escape(self.system))
    @classmethod
    def from_xml(cls, xmlsock):
        nta = cls()
        nta._from_xml(xmlsock)
        return nta

    def _from_xml(self, xmlsock):
        xmldoc = ElementTree.ElementTree(file=xmlsock).getroot()

        def int_or_none(text):
            if text != None:
                return int(text)
            return None

        #ntaxml = xmldoc.getElementsByTagName("nta")[0]
        ntaxml = xmldoc
        self.declaration = ntaxml.findtext('declaration') or ""
        self.system = ntaxml.findtext('system') or ""
        self.templates = []
        for templatexml in ntaxml.getiterator("template"):
            locations = {}
            for locationxml in templatexml.getiterator("location"):
                name = locationxml.findtext("name")
                location = Location(id=locationxml.get('id'),
                    xpos=int(locationxml.get('x', 0)),
                    ypos=int(locationxml.get('y', 0)), name=name)
                namexml = locationxml.find('name')
                if namexml != None:
                    (location.name.xpos, location.name.ypos) = \
                        (int_or_none(namexml.get('x', None)),
                        int_or_none(namexml.get('y', None))
                        )
                if locationxml.find("committed") != None:
                    location.committed = True
                if locationxml.find("urgent") != None:
                    location.urgent = True
                for labelxml in locationxml.getiterator("label"):
                    if labelxml.get('kind') == 'invariant':
                        location.invariant = Label("invariant", labelxml.text)
                        location.invariant.xpos = int_or_none(labelxml.get('x', None))
                        location.invariant.ypos = int_or_none(labelxml.get('y', None))
                    elif labelxml.get('kind') == 'exponentialrate':
                        location.exprate = Label("exponentialrate", labelxml.text)
                        location.exprate.xpos = int_or_none(labelxml.get('x', None))
                        location.exprate.ypos = int_or_none(labelxml.get('y', None))
                    #TODO other labels
                locations[location.id] = location
            for branchpointxml in templatexml.getiterator("branchpoint"):
                branchpoint = Branchpoint(id=branchpointxml.get('id'),
                    xpos=int_or_none(branchpointxml.get('x', None)),
                    ypos=int_or_none(branchpointxml.get('y', None)))
                locations[branchpoint.id] = branchpoint
            transitions = []
            for transitionxml in templatexml.getiterator("transition"):
                transition = Transition(
                    locations[transitionxml.find('source').get('ref')],
                    locations[transitionxml.find('target').get('ref')],
                    )            
                transition.controllable = ('controllable', 'false') not in transitionxml.items()
                if 'action' in transitionxml.keys():
                    l = [s[1] for s in transitionxml.items() if s[0] == 'action']
                    transition.action = l[0]
                else:
                    transition.action = None
                for labelxml in transitionxml.getiterator("label"):
                    if labelxml.get('kind') in ['select', 'guard', 'assignment', 
                                                'synchronisation']:
                        label = getattr(transition, labelxml.get('kind'))
                        label.value = labelxml.text
                        label.xpos = int_or_none(labelxml.get('x', None))
                        label.ypos = int_or_none(labelxml.get('y', None))
                for nailxml in transitionxml.getiterator("nail"):
                    transition.nails += [
                        Nail(int_or_none(nailxml.get('x', None)), 
                            int_or_none(nailxml.get('y', None)))]
                transitions += [transition]

            declaration = templatexml.findtext("declaration") or ""
            parameter = templatexml.findtext("parameter") or ""

            if templatexml.find("init") != None:
                initlocation=locations[templatexml.find("init").get('ref')]
            else:
                initlocation = None
            template = Template(templatexml.find("name").text,
                declaration,
                locations.values(),
                initlocation=initlocation,
                transitions=transitions,
                parameter=parameter)
            self.templates += [template]    

class Template:
    def __init__(self, name, declaration="", locations=None, initlocation=None, transitions=None, parameter=None):
        self.name = name
        self.declaration = declaration
        self.locations = locations or []
        self.transitions = transitions or []
        self.initlocation = initlocation
        self.parameter = parameter

    def assign_ids(self):
        i = 0
        for l in self.locations:
            l.oldid = getattr(l, 'id', None)
            l.id = 'id' + str(i)
            i = i + 1

    def dot2uppaalcoord(self, coord):
        return int(-float(coord)*1.5)

    def add_Transition(self, trans):
       
        self.transitions.append(trans)
        
    
    def add_Location(self, loc):
        #print "called add location..."
        self.locations.append(loc)
        
        
    def get_location_by_name(self, name):
        locs = [l for l in self.locations if l.name.value == name]
        assert len(locs) == 1
        return locs[0]
    
    def sharpenTransitions(self, nailAngleThreshold, nailInterDistanceThreshold):
        for transition in self.transitions:
            transition.sharpen(nailAngleThreshold, nailInterDistanceThreshold)


    def _parameter_to_xml(self):
        if self.parameter:
            return '<parameter>%s</parameter>' % (cgi.escape(self.parameter))
        return ""

    def to_xml(self):
        return """  <template>
    <name x="5" y="5">%s</name>
    %s
    <declaration>%s</declaration>
    %s
    %s
    <init ref="%s" />
    %s
  </template>""" % (self.name, 
    self._parameter_to_xml(),
    cgi.escape(self.declaration),
    "\n".join([l.to_xml() for l in self.locations if isinstance(l, Location)]),
    "\n".join([l.to_xml() for l in self.locations if isinstance(l, Branchpoint)]),
    self.initlocation.id,
    "\n".join([l.to_xml() for l in self.transitions]))

class Label:
    def __init__(self, kind, value=None, xpos=None, ypos=None):
        self.kind = kind
        self.value = value
        self.xpos = xpos
        self.ypos = ypos

    def get_value(self):
        if self.value:
            return self.value
        return ""

    def append(self, expr, auto_newline=True, sep=","):
        nl = auto_newline and '\n' or ''
        if self.get_value():
            self.value = self.get_value() + sep + nl + expr
        else:
            self.value = expr
            
    def append_and(self, expr, auto_newline=True):
        self.append(expr, auto_newline, sep=' && ')


    def append_or(self, expr, auto_newline=True):
        self.append(expr, auto_newline, sep=' || ')

    def move_relative(self, dx, dy):
        self.xpos += dx
        self.ypos += dy

    def to_xml(self):
        if self.value:
            attrs = ['kind="%s"' % self.kind]
            if self.xpos:
                attrs += ['x="%s"' % self.xpos]
            if self.ypos:
                attrs += ['y="%s"' % self.ypos]

            #special case for location names
            if self.kind == 'name':
                return '<name %s>%s</name>' % \
                    (" ".join(attrs[1:]), cgi.escape(self.value))
            else:
                return '<label %s>%s</label>' % \
                    (" ".join(attrs), cgi.escape(self.value))
        return ''

    def __str__(self):
        return self.get_value()

class Location:
    @require_keyword_args(1)
    def __init__(self, invariant=None, urgent=False, committed=False, name=None, id = None,
        xpos=0, ypos=0):
        self.invariant = Label("invariant", invariant)
        self.exprate = None
        self.committed = committed
        self.urgent = urgent
        self.name = Label("name", name)
        self.id = id
        self.xpos = xpos
        self.ypos = ypos

    def move_relative(self, dx, dy):
        self.xpos += dx
        self.ypos += dy
        for l in [self.invariant, self.name]:
            l.move_relative(dx, dy)

    def to_xml(self):
        namexml = self.name.to_xml()
        invariantxml = self.invariant.to_xml()
        if not (self.exprate is None):
            expratexml = self.exprate.to_xml()
        else:
            expratexml = ""
        return """
    <location id="%s" x="%s" y="%s">
      %s
      %s
      %s
      %s
      %s
    </location>""" % (self.id, self.xpos, self.ypos, namexml, invariantxml, expratexml,
        self.committed and '<committed />' or '', self.urgent and '<urgent />' or '')

class Branchpoint:
    @require_keyword_args(1)
    def __init__(self, id=None, xpos=0, ypos=0):
        self.id = id
        self.xpos = xpos
        self.ypos = ypos

    def to_xml(self):
        return """
    <branchpoint id="%s" x="%s" y="%s" />""" % (self.id, self.xpos, self.ypos)


last_transition_id = 0
class Transition:
    @require_keyword_args(3)
    def __init__(self, source, target, select='', guard='', synchronisation='',
                    assignment='', action = None, controllable=True):
        self.source = source
        self.target = target
        self.select = Label("select", select)
        self.guard = Label("guard", guard)
        self.synchronisation = Label("synchronisation", synchronisation)
        self.assignment = Label("assignment", assignment)
        self.nails = []
        self.action = action
        self.controllable = controllable

        global last_transition_id
        self.id = 'Transition' + str(last_transition_id)
        last_transition_id = last_transition_id + 1

    def __copy__(self):
        newone = Transition(self.source, self.target, 
            select=self.select.value, 
            guard=self.guard.value,
            synchronisation=self.synchronisation.value,
            assignment=self.assignment.value)
        return newone

    def sharpen(self, angleThreshold, lengthThreshold):
        count = 0
        while True: # do while? 
            removed = False
            nail_to_pos = lambda nail: (nail.xpos, nail.ypos)

            for (prev, curnail, next) in zip(
                    [(self.source.xpos, self.source.ypos)] + map(nail_to_pos, self.nails[:-1]), 
                    self.nails, 
                    map(nail_to_pos, self.nails[1:]) + [(self.target.xpos, self.target.ypos)]
                    ):
                cur = nail_to_pos(curnail)
                v1 = (prev[0]-cur[0], prev[1]-cur[1])
                v2 = (next[0]-cur[0], next[1]-cur[1])
                v1len = (math.sqrt((v1[0]*v1[0])+(v1[1]*v1[1])))
                v2len = (math.sqrt((v2[0]*v2[0])+(v2[1]*v2[1])))
                if v1len<lengthThreshold or v2len<lengthThreshold:
                    self.nails.remove(curnail)
                    count += 1
                    removed=True
                    break
                dot = (v1[0] * v2[0] + v1[1] * v2[1])/(v1len*v2len)
                #clamp input to between 1...-1
                dot = max(-1.0, min(dot, 1.0))
                angle = math.degrees(math.acos(dot))
                if angle > angleThreshold:
                    self.nails.remove(curnail)
                    count += 1
                    removed=True
                    break
            if not removed:
                break
        return count
    def to_xml(self):
        if self.action is None:
            action_str = ''
        else:
            action_str = ' action="' + str(self.action) + '"'
        if self.controllable is False:
            controllable_str = ' controllable="false"'
        else:
            controllable_str = ''
        return """
    <transition%s%s>
      <source ref="%s" />
      <target ref="%s" />
      %s
      %s
      %s
      %s
      %s
    </transition>""" % (action_str,controllable_str,self.source.id, self.target.id,
        self.select.to_xml(), self.guard.to_xml(),
        self.synchronisation.to_xml(), self.assignment.to_xml(),
        "\n".join(map(lambda x: x.to_xml(), self.nails))
        )

    def set_num_nails(self, num):
        self.nails = []
        for i in range(num):
            self.nails += [Nail()]

last_nail_id = 0
class Nail:
    def __init__(self, xpos=0, ypos=0):
        global last_nail_id
        self.id = 'Nail' + str(last_nail_id)
        last_nail_id = last_nail_id + 1
        self.xpos = xpos
        self.ypos = ypos

    def to_xml(self):
        return """
    <nail x="%s" y="%s" />""" % \
            (self.xpos, self.ypos)

class QueryFile:
    def __init__(self, q = '', comment = ''):
        self.queries = []

        if q != '':
            self.addQuery(q, comment)

    def addQuery(self, q, comment=''):
        self.queries += [(q, comment)]

    def saveFile(self, fh):
        out = [''] + \
            ['/*\n' + comment + '*/\n' + (q == '' and '//NO_QUERY' or q) for (q, comment) in self.queries]
        fh.write("\n\n".join(out))

    
    #Call deleteTempFile to close and delete the tempfile
    def getTempFile(self):
        (fileh, path) = tempfile.mkstemp(suffix='.q')
        file = os.fdopen(fileh)
        file.close()
        file = open(path, 'r+w')
        self.saveFile(file)
        file.close()
        file = open(path, 'r')
        return (file, path)

    def deleteTempFile(self, file):
        path = file.name
        file.close()
        os.unlink(path)


