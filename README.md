========================================================================================================================
Predictive Runtime Verification Monitor for Timed Properties.
(Prototype implementation (in Python) of the predictive runtime verification algorithm for timed properties described in the paper.) 
========================================================================================================================
-= License =-
This software is provided under the license GPL.

-= About =-

The source code and some properties formalized using UPPAAL which were used for testing are provided. 
The archive contains three directories:
- the  Source/ directory contains the source code. 
- The ExampleProperties/ directory contains some UPPAAL models (stored as .xml) defining some example properties we used for testing. 
- The UppaalLibraries/ directory contains UPPAAL libraries that were used taken from  (http://people.cs.aau.dk/~adavid/python/).
Note that the prototype was developed and tested on Linux only (Ububtu 14, 32-bit version). 

-= REMARKS =-

- Note that the PYUPPAAL, DBMPYUPPAAL, PYDBM are the required libraries, provided in the directory UppaalLibraries/ and are also available at 
 (http://people.cs.aau.dk/~adavid/python/).
- Some example properties are in the directory ../ExampleProperties/.

-= INSTALLATION =-

1. Install python.
2. Install the following UPPAAL libraries (that are in directory UppaalLibraries/, or can also be retrieved at http://people.cs.aau.dk/~adavid/python/):
- PyUPPAAL
- UPPAAL DBM
- DBMPyUPPAAL
- PYDBM

-= DESCRIPTION OF THE PROTOTYPE IMPLEMENTATION =-

Below is a description of the source files.

1. ProductTA.py
   This module contains functionality to compute product of two TAs. Note that in the algorithm, we need to compute the product of the automaton defining the input property (psi) and the 
   automaton defining the property to enforce (varphi), and two sets of final locations F and F_neg. Method "Product" in this module takes both the TA's as input parameters, 
   and returns the product TA and the two sets of final locations F anf F_neg.      
   
2. PredictiveRVMonitor.py
   The PredictiveRVMonitor.py module contains the method "predictiveRVmonitor" which is an implementation of the predictive RV monitoring algorithm discussed in the paper.  
   It takes the following as input parameters in the following order:
	- Input property psi: UPPAAL model as xml, containing automaton representing the input property psi.
    - Property to enforce varphi: UPPAAL model as xml, containing automaton representing the property to enforce varphi.
    - InputTrace: A sample input timed word belonging to the input property psi, where each event consists of an action and a delay. 
This module also contains other methods (that are used by the "predictiveRVmonitor" method) for checking reachability of a set of locations, and to move in a TA from its current state by consuming a given event.   	

3. testPredRVmonitor.py
   Test script to test the behavior of the predictiveRVmonitor using example properties under directory "ExampleProperties/"  
   Illustrates how to use/invoke the "predictiveRVmonitor" method. 

Note that in the TA defining properties (in UPPAAL format), labels of accepting locations should start with "Final". 	


-= USAGE =-

1. Import the PredictiveRVMonitor module.

2. Invoke the "testStoreProcess" method in the MainTest module, providing the following arguments in order:
   - Input property 
   - Property to enforce
   - Input trace
   
 For example, let "InputProperty1.xml" be the UPPAAL model containing the TA defining the input property and let "PropertyEnforce1.xml" be the UPPAAL model containing the TA defining the property to enforce, 
 and let the set of actions Sigma = {a,b,c}. 
 Then the predictiveRVmonitor method can be invoked with some test input trace e.g. "('a',10).('a',34).('b',10).('a',12).('b',1)" as follows: 
 "PredictiveRVMonitor.predictiveRVmonitor("InputProperty1.xml", "PropertyEnforce1.xml", [('a',10),('a',34),('b',10),('a',12),('b',1)])".  
 
3. Please check "testPredRVmonitor.py" that contains some examples. The following lines demonstrates how to execute these tests via python command line:

 - Browse to the folder containing the source code (which contains the file "testPredRVmonitor.py").
 - Execute the script "testPredRVmonitor.py" entering the following line in the command prompt "python testPredRVmonitor.py". 


