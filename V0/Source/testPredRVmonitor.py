#############################################################################################################
#### To test the input-output behavior of the predictive RV monitor.  ######################################
#### Invokes PredictiveRVMonitor method with the input property, the property to verify, and a sample input trace/word (which belongs to the input property).
#############################################################################################################
import PredictiveRVMonitor
import os.path
import sys
############################
# Current working directory
projdir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
examplePropPath = projdir+"/ExampleProperties" 
# system path
sys.path = [projdir] + sys.path
############################

####################################################################################################################
####### "testPredRVmonitor" is the main test method. 
####### Input parameters:
#-  the input property, 
#-  the prop to verify, and 
#- sample input trace/word (which belongs to the input property).
####################################################################################################################
def testPredRVmonitor(inpProperty, prop, inputTrace):
    print "Input property is:" + str(inpProperty)
    print "Property to verify is..:" + str(prop)
    print "sample/test input trace is: " + str(inputTrace)
    PredictiveRVMonitor.predictiveRVmonitor(inpProperty, prop, inputTrace)
####################################################################################################################

##Input property: "InputProp1.xml". Input property described in the motivating examples section in the paper. ####
##Property to verify: "PropVerify1.xml". property considered to be verified described in the motivating examples section in the paper. 
############# Sigma = {a,b,c}, Sample input trace = "('a',10),('b',9),('b',13),('c',30)"###
##
testPredRVmonitor(examplePropPath+'/InputProp1.xml',  examplePropPath+'/PropVerify1.xml',  [('a',10),('b',9),('b',13),('c',30)])           
print "#####################################################################"
print "#####################################################################"
 
 
##Input property: "InputProp1.xml". Input property described in the motivating examples section in the paper. ####
##Property to verify: "PropVerify1.xml". property considered to be verified described in the motivating examples section in the paper. 
############# Sigma = {a,b,c}, Sample input trace = "('a',10),('a',34),('b',10),('c',10)"###
testPredRVmonitor(examplePropPath+'/InputProp1.xml',  examplePropPath+'/PropVerify1.xml',  [('a',10),('a',34),('b',10),('c',10)])
print "#####################################################################"
print "#####################################################################"


##Input property: "InputPropUni.xml". Input property accepts all timed words over alphabet {a,b,c}. ####
##Property to verify: "PropVerify2.xml". Safety property expressing "there should be atleast 5 t.u delay between any two b actions". 
############# Sigma = {a,b,c}, Sample input trace = "('a',10),('a',34),('b',10),('a',12),('b',1)"###
testPredRVmonitor(examplePropPath+'/InputPropUni.xml',  examplePropPath+'/PropVerify2.xml',  [('a',10),('a',34),('b',10),('a',12),('b',1)])
print "#####################################################################"
print "#####################################################################"



##Input property: "InputPropUni.xml". Input property accepts all timed words over alphabet {a,b,c}. ####
##Property to verify: "PropVerify2.xml". Safety property expressing "there should be atleast 5 t.u delay between any two b actions". 
############# Sigma = {a,b,c}, Sample input trace = "('a',10),('a',34),('b',10),('a',1),('b',2)"###
testPredRVmonitor(examplePropPath+'/InputPropUni.xml',  examplePropPath+'/PropVerify2.xml',  [('a',10),('a',34),('b',10),('a',1),('b',2)])
print "#####################################################################"
print "#####################################################################"
#####################################################################################



##Input property: "InputPropUni.xml". Input property accepts all timed words over alphabet {a,b,c}. ####
##Property to verify: "PropVerify3.xml". Property expressing "there should be a "c" action which should be immediately followed by a "a" action after atleast 6 t.u. after action "a" has occured". 
############# Sigma = {a,b,c}, Sample input trace = "('a',10),('a',34),('b',10),('a',1),('b',2)"###
testPredRVmonitor(examplePropPath+'/InputPropUni.xml',  examplePropPath+'/PropVerify3.xml',  [('a',10),('b',10),('b',12),('c',1),('a',14)])
print "#####################################################################"
print "#####################################################################"
#####################################################################################













