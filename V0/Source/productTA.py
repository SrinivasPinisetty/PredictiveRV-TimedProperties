import pyuppaal
###########################################################################################################
### Method to perform product of two TAs TA1 (defining psi) and TA2 (defining varphi).#####################
### Two sets of final locations F = F_TA1*F_TA2, F' = F_TA1*{L_TA2\F_TA2}##################################
### Input: Two TAs(in the form of UPPAAL template) on which the product operation has to be performed #####
### Output: Product TA, and two sets of final locations F and F'.########################################## 
###########################################################################################################
def Product(ta1,ta2):
    productTA = pyuppaal.Template("TA_Product",
                             declaration=ta1.declaration + "\n" + ta2.declaration)
    ##set of locations in the resulting TA (initially empty)##
    locations = {}
    
    ##Variable used to count the number of final locations in the resulting TA used for purposes such as labeling locations in the TA.##
    #finalLocCounter = 0
    
    ### final locations F (F = F_TA1*F_TA2)
    finalLocF = []
    
    ### final locations Fneg (intersection of two TA's, "finalLocFneg = F_TA1*neg(F_TA2)")
    finalLocFneg = []

    ### Computing locations in the product automaton ######
    for loc1 in ta1.locations:
        for loc2 in ta2.locations:
            ##Labels of accepting locations in the input TAs should start with "Final".## 
            locID = str(loc1.name) + str(loc2.name)
            l_product = pyuppaal.Location(name=locID)
            l_product.id = locID
            
            productTA.locations.append(l_product)
            locations[(loc1, loc2)] = l_product
            if str(loc1.invariant):
                if str(loc2.invariant):
                    l_product.invariant = pyuppaal.Label("invariant", str(loc1.invariant) + ' && ' + str(loc2.invariant))
                else:
                    l_product.invariant = pyuppaal.Label("invariant", str(loc1.invariant))
            elif str(loc2.invariant):
                l_product.invariant = pyuppaal.Label("invariant", str(loc2.invariant))
            if ta1.initlocation == loc1 and ta2.initlocation == loc2:
                productTA.initlocation = l_product
    
    
    ### Computing final location set F ###
    for loc in productTA.locations:
        if str(loc.name).find("Final") != -1 and  str(loc.name).find("Final", 6) != -1:
            #print "final location is.."+str(loc.name)
            #finalLocF.append(loc)
            finalLocF.append(str(loc.name))
            
    
    ### Computing final location set Fneg ###
    for loc in productTA.locations:
        if str(loc.name).find("Final",0,6) != -1 and  str(loc.name).find("Final", 6) == -1:
            #print "finalneg location is.."+str(loc.name)
            #finalLocFneg.append(loc)
            finalLocFneg.append(str(loc.name))
    
    ### Transitions in the product automaton #################  
    for tr1 in ta1.transitions:
        for tr2 in ta2.transitions:
            if str(tr1.synchronisation) == str(tr2.synchronisation): 
                tr_product = pyuppaal.Transition(source=locations[(tr1.source,tr2.source)], \
                                             target = locations[(tr1.target,tr2.target)], \
                                             synchronisation = str(tr1.synchronisation))
                if str(tr1.guard):
                    if str(tr2.guard):
                        tr_product.guard = pyuppaal.Label("guard", str(tr1.guard)+' && '+str(tr2.guard))
                    else:
                        tr_product.guard = pyuppaal.Label("guard", str(tr1.guard))
                elif str(tr2.guard):
                    tr_product.guard = pyuppaal.Label("guard", str(tr2.guard))
                    
                if str(tr1.assignment):
                    if str(tr2.assignment):
                        tr_product.assignment = pyuppaal.Label("assignment", str(tr1.assignment)+', '+str(tr2.assignment))
                    else:
                        tr_product.assignment = pyuppaal.Label("assignment", str(tr1.assignment))
                elif str(tr2.assignment):
                    tr_product.assignment = pyuppaal.Label("assignment", str(tr2.assignment))
                productTA.transitions.append(tr_product)
    return (productTA, finalLocF, finalLocFneg)
###########################################################################################################
###########################################################################################################