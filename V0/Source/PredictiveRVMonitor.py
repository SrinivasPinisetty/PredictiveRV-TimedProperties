# Imports
##################################################################
import sys
import os.path
import pyuppaal
import dbmpyuppaal
import pydbm.udbm
import subprocess
import re
import time
import copy
import productTA
import shutil
#########################################################################
# Current working directory
projdir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
# system path
sys.path = [projdir] + sys.path
# #######################################################################
def takeTrans2CR(state, transition):
    newState = state.copy()
    newState.federation &= transition.guard
    fed = newState.federation
    
    if newState.federation.isEmpty():
        return None
    for (clock, value) in transition.update:
        newState.federation = newState.federation.updateValue(clock, value)
    newState.federation &= transition.target.invariant
    if newState.federation.isEmpty():
        return None
    newState.locations[transition.target.template.name] = transition.target
        
    newState = newState.delay().extrapolateMaxBounds()
    if newState:
        return (newState, transition.update, fed)
    else:
        return None 
######################################################################
######################################################################
def computeReachPaths(goal_template, start_loc, goal_locations):
    start = start_loc.delay().extrapolateMaxBounds()
    waiting_list = [start_loc.delay().extrapolateMaxBounds()]
    numPaths = 0
    passed_list = []
    paths= [list((start, [],[],[]))]
    reachable = False
    
    while waiting_list:
        state = waiting_list.pop()
        for transition in goal_template.transitions:
            if not transition.source.name == state.locations[transition.template.name].name:
                continue
            else:
                s = takeTrans2CR(state, transition)
                 
                if s !=None:
                    if transition.source.id == start.locations[transition.template.name].id:
                        newPath = list((s[0], [s[0]],[s[1]],[s[2]]))
                        paths.append(newPath)
                        numPaths=numPaths+1
                        #print "test.."+ str(transition.source.id) + str(start.locations[transition.template.name].id)
                    else:    
                        for path in paths:
                            if transition.source.id == path[0].locations[transition.template.name].id:
                                if not(path[0].locations[str(goal_template.name)].name in goal_locations):
                                    path[1].append(s[0])
                                    path[2].append(s[1])
                                    path[3].append(s[2])
                                    path[0]=s[0]
                                            
                if s !=None and not s[0] in waiting_list + passed_list:
                    waiting_list.append(s[0])
                    if s[0].locations[str(goal_template.name)].name in goal_locations:
                        reachable = True
                if not state in passed_list:
                    passed_list.append(state)
     
    paths.pop(0)        
    return (reachable,paths)
###########################################################################
###########################################################################
def takeTransition2(state, transition):
    newState = state.copy()
    newState.federation &= transition.guard 
    if newState.federation.isEmpty():
        return None
    for (clock, value) in transition.update:
        newState.federation = newState.federation.updateValue(clock, value)
    newState.federation &= transition.target.invariant
    if newState.federation.isEmpty():
        return None
    newState.locations[transition.target.template.name] = transition.target
    newState = newState.delay().extrapolateMaxBounds()
    if newState:
        return newState
    else:
        return None 
######################################################################
######################################################################
def checkReachability(goal_template, start_loc, goal_locations):
    waiting_list = [start_loc.delay().extrapolateMaxBounds()]
    passed_list = []
    #print goal_template.name
    #print "goal loc are.."+str(goal_locations)
    while waiting_list:
        state = waiting_list.pop()
        #print state
        for transition in goal_template.transitions:
            if not transition.source.name == state.locations[transition.template.name].name:
                continue
            else:
                #print "ids match..taking trans.."
                s = takeTransition2(state, transition)
                #print s
                               
                if s and not s in waiting_list + passed_list:
                    waiting_list.append(s)
                    #print "goal loc are.."+str(goal_locations)
                    #print "reached state loc.." + str(s.locations["Property"].id)
                    if s.locations[str(goal_template.name)].name in goal_locations:
                        #print "goal locations reachable in future!!"
                        return True
                if not state in passed_list:
                    passed_list.append(state)
            
    return False
###########################################################################
###########################################################################

###########################################################################
##Function to compute extra delay##########################################
## TODO: Need to be replaced with another alternative. ####################
##### (should be done better). ############################################
###########################################################################
def computeExtraDelay(conditions,clks):
    extraDelay = 0.0
    c = False
    while c!=True:
    #for i in range(1,100):
        for i in range(0, clks.__len__()):
            clks[i] = (clks[i][0], clks[i][1]+1.0)
        #counter=counter + 1.0
        extraDelay = extraDelay+1.0
        
        for i in range(0,conditions.__len__()):
            c = conditions[i]       
            for clk in clks:
                c = c.replace(clk[0], str(clk[1]))
                #print "cond is.."+str(c)
            res = eval(c)
            if res:
                c = True
            else:
                c = False
                break
        if c == True:
#            print "extra delay is.."+str(extraDelay)
            return extraDelay   
############################################################################        
############################################################################
            
############################################################################
##Compute the minimal duration of the given path. ##########################
############################################################################
def getDelays(path, constraints, resets, clks):
    delays = []
    sumDelays = 0.0
    
    #for states in path:
    for i in range(0, path.__len__()):
        stateWithResets = resets[i]
        fed = str(constraints[i])
        fed=fed.replace("(", "")
        fed=fed.replace(")", "")
        
        conditions = fed.split("&")
        for i in range(0,conditions.__len__()):
            c = conditions[i]
            if c=="true":
                additionalDelay = 0.0
            else:
                for clk in clks:
                    c = c.replace(clk[0], str(clk[1]))
                #print "cond is.."+str(c)
                res = eval(c)
                if not res:
                    additionalDelay = computeExtraDelay(conditions,clks)
                    break
                else:
                    additionalDelay = 0.0
        
        #print "additional delay is.."+str(additionalDelay)            
        for i in range(0,clks.__len__()):
            clks[i] = (clks[i][0], clks[i][1]+additionalDelay)
        delays.append(additionalDelay)
        sumDelays = sumDelays+additionalDelay 
        
        for (clock,value) in stateWithResets:
            for clk in clks:
                if clk[0]== str(clock):
                    clks[clks.index(clk)] = (clk[0],0)
        #pathIndex = pathIndex+1
    #print "sum delays is.."+str(sumDelays)
    return(sumDelays,delays,clks)
#######################################################################
#######################################################################

#########################################################################################
### Picks a path among the given set of paths whose sum of delays is minimal.############
### Returns the total duration of the selected path (which is the minimal duration).#####
#########################################################################################
def getOptimalDelays(paths, clks):
    optimalDelays = []
    optimalPath = []
    optimalSum = None
    for p in paths:
        path = p[1]
        constraints = p[3]
        resets= p[2]
        newC=list(clks)
        result = getDelays(path, constraints, resets, newC)
        if optimalSum==None:
            optimalSum = result[0]
            optimalDelays= result[1]
            optimalPath = p
        else:
            if optimalSum > result[0]:
                optimalSum = result[0]
                optimalDelays = result[1]
                optimalPath = p
        #print "opt sum is.."+str(optimalSum)        
    return optimalSum
##################################################################################################
##################################################################################################
#

##################################################################################################
### Move in the given automaton from a given current state consuming a give event.################
################################################################################################## 
def moveAut(automaton, Parsed_aut_DbmPyUppaal, currState, act, clks):
    guardStr = None
    for clock in clks:
        if guardStr==None:
            guardStr= clock[0]+"=="+str(clock[1])
        else:
            guardStr= guardStr+"&&"+clock[0]+"=="+str(clock[1])
    
    for transition in automaton.transitions:
        if transition.source.id == currState.locations[transition.template.name].id:
            guard2 = dbmpyuppaal.parse_invariant_or_guard(guardStr,Parsed_aut_DbmPyUppaal.clocks, Parsed_aut_DbmPyUppaal.global_consts) or Parsed_aut_DbmPyUppaal.context.getTautologyFederation()
            newState = currState.copy()
            if str(transition.synchronisation)[0]== act:
                newState.federation &= transition.guard & guard2
                
                if newState.federation.isEmpty():
                    continue
                for (clock, value) in transition.update:
                    newState.federation = newState.federation.updateValue(clock, value)
                newState.federation &= transition.target.invariant 
                if newState.federation.isEmpty():
                    continue
                newState.locations[transition.target.template.name] = transition.target    
                newState = newState.delay().extrapolateMaxBounds()
                if newState:
                    return (newState, transition.update)
                    exit
                else:
                    continue
    return None 
#############################################################################################################
#############################################################################################################

#############################################################################################################
### Return set of all accepting locations in a given automaton. #############################################
### Note, in the automata (defining psi, and varphi), labels of accepting locations should start with "Final".
#############################################################################################################    
def getAccLoc(prop):
    accloc= []
    for loc in prop.locations:
        if str(loc.name).find("Final") != -1:
            accloc.append(str(loc.name))
    return accloc
#########################################################################################
#########################################################################################    


##############################################################################################################################################
##############################################################################################################################################    
####### Predictive Runtime Verification Monitor.##############################################################################################
####### INPUT parameters #####
##########--Input property psi--UPPAAL model as xml, containing automaton representing the input property psi.#################################
##########--Property to enforce-UPPAAL model as xml, containing automaton representing the property to enforce varphi. ########################
##########--inputTrace--a sample input timed word belonging to the input property psi, where each event consists of an action and a delay. ####
########################################################################################################################## #################### 
def predictiveRVmonitor(inputProp, prop, inputTrace):
    # PYUPPAAL
    psi = pyuppaal.NTA.from_xml(open(inputProp)).templates[0] # input property psi.
    varphi = pyuppaal.NTA.from_xml(open(prop)).templates[0] # property to enforce varphi.
    #CL_psi = psi.initlocation
    #CL_varphi = varphi.initlocation
    ## Accepting locations in  psi and in varphi ##
    accPsi = getAccLoc(psi)
    accVarphi=getAccLoc(varphi)
    ##################
    # DBMPYUPPAAL
    Parsed_psi_DbmPyUppaal = dbmpyuppaal.parse_xml(inputProp)
    Parsed_varphi_DbmPyUppaal = dbmpyuppaal.parse_xml(prop)
    Psi_Automaton = Parsed_psi_DbmPyUppaal.getTemplateByName("InputProperty")
    Varphi_Automaton = Parsed_varphi_DbmPyUppaal.getTemplateByName("Property")
    psiCurrentState = dbmpyuppaal.NTAState(Parsed_psi_DbmPyUppaal).delay().extrapolateMaxBounds()
    varphiCurrentState = dbmpyuppaal.NTAState(Parsed_varphi_DbmPyUppaal).delay().extrapolateMaxBounds()
    ###Clocks#########
    # Clocks in the psi and varphi and initializing all the clock values with 0.0. 
    clksPsi=[]
    clksVarphi=[]
    totalDuration=0.0
    for clock in Parsed_psi_DbmPyUppaal.clocks:
        clksPsi.append((str(clock),0))
    for clock in  Parsed_varphi_DbmPyUppaal.clocks:
        clksVarphi.append((str(clock),0))   
    ######################
    ## Compute product automaton B (product of psi and varphi), and the final location sets F and Fneg. ####
    ### first parameter is the input property, and the second parameter should be the property to enforce.## 
    result= productTA.Product(psi, varphi) 
    ## product aut B.
    automatonB = result[0]
    ## Final loc F (i.e. F_psi*F_varphi).
    locF = result[1]
    ## Final loc Fneg (i.e., F_psi*neg(F_varphi)).
    locFneg = result[2]
    ### Storing the product automaton as an UPPAAL model in xml format.###
    shutil.copy("baseData.xml", "productTA.xml")
    product = pyuppaal.NTA.from_xml(open("productTA.xml"))
    #product.templates[0] = automatonB
    product.add_template(automatonB)
    ####File operations (writing the updated model to file).### 
    f = open("productTA.xml", "r+")
    f.writelines(pyuppaal.NTA.to_xml(product))
    f.close()
    ######################
    Parsed_product_DbmPyUppaal = dbmpyuppaal.parse_xml("productTA.xml")
    productCurrentState = dbmpyuppaal.NTAState(Parsed_product_DbmPyUppaal).delay().extrapolateMaxBounds()
    autB_DBMpy = Parsed_product_DbmPyUppaal.getTemplateByName("TA_Product")
    ######################
    ####################################################################################################
    #### Online monitoring starts here. Read/process events in the given sample input trace ############
    print "given input sequence is.."+str(inputTrace)
    while True:
    #for i in range(0,inputTrace.__len__()):
        reachFneg = checkReachability(autB_DBMpy, productCurrentState, locFneg)
        reachF = checkReachability(autB_DBMpy, productCurrentState, locF)
        
        if not reachFneg:
            print "Conclusive verdict TRUE (Non-accepting loc is not reachable in future!!)"
            print "Computing minimal time..."
            res=computeReachPaths(Psi_Automaton, psiCurrentState,accPsi)
            minTime = getOptimalDelays(res[1],  clksPsi)
            print "min time to reach an accepting state in psi is.."+str(minTime)
            break
        elif not reachF:
            print "Conclusive verdict FALSE (Violation is unavoidable!!)"
            print "Computing minimal time..."
            res=computeReachPaths(Psi_Automaton, psiCurrentState,accPsi)
            minTime = getOptimalDelays(res[1],  clksPsi)
            #print "reach.."+str(res[0])
            #print "paths.."+str(res[1])
            print "min time to reach an acc state in psi is.."+str(minTime)
            break
        elif str(psiCurrentState.locations["InputProperty"].name) in accPsi and str(varphiCurrentState.locations["Property"].name) in accVarphi:
            print "Verdict is...CURRENTLY_TRUE."
        elif str(psiCurrentState.locations["InputProperty"].name) in accPsi and not str(varphiCurrentState.locations["Property"].name) in accVarphi:
            print "Verdict is...CURRENTLY_FALSE."
        else:
            print "Verdict is..UNKNOWN."  
        print "-----------------------------------------------------------------"
        ##
        if inputTrace.__len__()==0:
            break
        
        # Remove and take first event from the trace ##
        ## event is a tuple (action, delay) ###
        event = inputTrace.pop(0)          
        print "input event is: " + str(event)
        totalDuration = totalDuration+event[1] 
        
        ## Increment all clock values with the delay corresponding to the current event. ##
        for i in range(0,clksPsi.__len__()):
            #print clksPsi[i][1]+event[1]
            clksPsi[i] = (clksPsi[i][0], clksPsi[i][1]+event[1])
        for i in range(0,clksVarphi.__len__()):
            #print clksVarphi[i][1]+event[1]
            clksVarphi[i] = (clksVarphi[i][0], clksVarphi[i][1]+event[1])

        #print"psi loc before transition.." + str(psiCurrentState.locations["InputProperty"].name)
        #print"varphi loc before transition.." + str(varphiCurrentState.locations["Property"].name)
        
        ## Move in the automata ##
        movePsiRes = moveAut(Psi_Automaton,Parsed_psi_DbmPyUppaal, psiCurrentState, event[0], clksPsi)
        psiCurrentState = movePsiRes[0]
        moveVarphiRes = moveAut(Varphi_Automaton, Parsed_varphi_DbmPyUppaal, varphiCurrentState, event[0], clksVarphi)
        varphiCurrentState = moveVarphiRes[0]
        #print"psi loc after transition.." + str(psiCurrentState.locations["InputProperty"].name)
        #print"varphi loc after transition.." + str(varphiCurrentState.locations["Property"].name)
        #print "psi new state is.."+ str(psiCurrentState)
        #print "varphi new state is.."+ str(varphiCurrentState)
        #print"prod autB loc before transition.." + str(productCurrentState.locations["TA_Product"].name)
        moveProdB = moveAut(autB_DBMpy,Parsed_product_DbmPyUppaal, productCurrentState, event[0], clksPsi+clksVarphi)
        #print moveProdB
        productCurrentState = moveProdB[0]
        #print"prod autB loc after transition.." + str(productCurrentState.locations["TA_Product"].name)
        
        # Consider resets in the transition that is taken in the automata and reset clocks. ### 
        for (clock,value) in movePsiRes[1]:
            for clk in clksPsi:
                #print clksPsi.index(clk)
                if clk[0]== str(clock):
                    clksPsi[clksPsi.index(clk)] = (clk[0],0)

        for (clock,value) in moveVarphiRes[1]:
            for clk in clksVarphi:
                if clk[0]== str(clock):
                    clksVarphi[clksVarphi.index(clk)] = (clk[0],0) 
        #print "clocks varphi after reset.."+str(clksVarphi)
        #print "clocks psi after reset.."+str(clksPsi)                
########################################################################################
########################################################################################

