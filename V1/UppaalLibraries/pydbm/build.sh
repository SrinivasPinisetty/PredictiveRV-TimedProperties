rm *so
python ./setup.py build_ext --inplace
#echo 1
#swig -c++ -python udbm_int.i 
#echo 2
#g++ -O2 -fPIC -L/usr/local/uppaal/lib -I/usr/local/uppaal/include -c udbm_int.cpp
#echo 3
#g++ -O2 -fPIC -c -I/usr/local/uppaal/include udbm_int_wrap.cxx -I/usr/include/python2.6
#echo 4
#g++ -shared udbm_int.o udbm_int_wrap.o -o _udbm_int.so -L/usr/local/uppaal/lib -ludbm
