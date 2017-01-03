import sys
import pdb

from dbmpyuppaal import parse_xml, NTAState

def takeTransition(state, transition, transition2=None):
    if transition2:
        update = transition.update + transition2.update
        guard = transition.guard & transition2.guard
        target_invariant = transition.target.invariant & transition2.target.invariant
    else:
        update = transition.update
        guard = transition.guard
        target_invariant = transition.target.invariant
    ret = state.copy()        
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
    ret = ret.delay().extrapolateMaxBounds()
    return ret

def checkReachability(nta_name, location):
    nta = parse_xml(sys.argv[1])
    goal_template = nta.getTemplateByName(sys.argv[2].split('.')[0])
    goal_location = goal_template.getLocationByName(sys.argv[2].split('.')[1])

    waiting_list = [NTAState(nta).delay().extrapolateMaxBounds()]
    passed_list = []

    while waiting_list:
        state = waiting_list.pop()
        for template in nta.templates:
            for transition in template.transitions:
                if not transition.source == state.locations[transition.template]:
                    continue
                if not transition.synchronisation:
                    s =  state.takeTransition(transition)
                    if s and not s in waiting_list + passed_list:
                        waiting_list.append(s)
                        if s.locations[goal_template] == goal_location:
                            return True
                else:
                    for template2 in nta.templates:
                        for transition2 in template2.transitions:
                            if not transition2.source == state.locations[transition2.template]:
                                continue
                            if not transition2.synchronisation or \
                                not transition2.synchronisation.matches(transition.synchronisation):
                                continue
                            s = state.takeTransition(transition, transition2)
                            if s and not s in waiting_list + passed_list:
                                waiting_list.append(s)    
                                if s.locations[goal_template] == goal_location:
                                    return True
        if not state in passed_list:
            passed_list.append(state)
    return False

result = checkReachability(sys.argv[1], sys.argv[2])

if result:
    print 'Location ' + sys.argv[2] + ' is reachable'
else:
    print 'Location ' + sys.argv[2] + ' is unreachable'
