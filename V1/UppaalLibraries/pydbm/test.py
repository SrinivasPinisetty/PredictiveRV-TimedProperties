import udbm

import unittest

import pdb

class UDBMTest(unittest.TestCase):
    def setUp(self):
        self.c = udbm.Context(["x", "y", "z"], name = "c")        
    def test_int_valuation(self):
        c = self.c
        v = udbm.IntValuation(c)
        self.assertRaises(KeyError, lambda :(v["not_in_federation"]))
        self.assertRaises(TypeError, v.__setitem__, ("x", 0.1)) # too bad we aren't using python 2.7 where it's possible to use "with self.assertRaises"
        v["x"] = 1
        v["y"] = 1
        v["z"] = 1
        self.assertTrue(( (c.x == 1) & (c.y == 1) & (c.z == 1)).contains(v))
        self.assertFalse(((c.x == 2) & (c.y == 1) & (c.z == 1)).contains(v))
    def test_float_valuation(self):
        c = self.c
        v = udbm.FloatValuation(c)
        self.assertRaises(KeyError, lambda :(v["not_in_federation"]))
        v["x"] = 1.0
        v["y"] = 1.01
        v["z"] = 1
        self.assertFalse(( (c.x == 1) & (c.y == 1) & (c.z == 1)).contains(v))
        self.assertTrue(((c.x == 1) & (c.y < 2) & (c.y > 1) & (c.z == 1)).contains(v))
    def test_set_operations(self):
        c = self.c
        self.assertTrue( (c.x == 1) == (c.x >= 1) & (c.x <= 1))
        self.assertFalse( (c.x == 1) == (c.x >= 1) & (c.x < 1))
        self.assertTrue( (c.x != 1) == ((c.x > 1) | (c.x < 1)))
        self.assertFalse( (c.x != 1) == ((c.x > 1) | (c.x <= 1)))
        self.assertTrue( (c.x == 1) & (c.y == 1)  == (c.y == 1) & (c.x == 1))
        self.assertTrue( (c.x == 1) | (c.y == 1)  == (c.y == 1) | (c.x == 1))
        self.assertFalse( (c.x == 1) | (c.y == 1)  != (c.y == 1) | (c.x == 1))
        self.assertFalse( (c.x == 1) & (c.y == 1)  != (c.y == 1) & (c.x == 1))
        self.assertTrue( (c.x == 1) & (c.y == 1)  != (c.y == 1) | (c.x == 1))
        self.assertTrue( (c.x == 1) & ((c.y == 1) | (c.z ==1))  == (c.x == 1) & (c.y == 1) |(c.x == 1) & (c.z ==1) )
        self.assertFalse( (c.x == 1) & ((c.y == 1) | (c.z ==1))  == (c.x == 1) & (c.y == 1) |(c.x == 1) )
        self.assertTrue( (c.x - c.y <= 1) == (c.y - c.x >= -1))
        self.assertFalse( (c.x - c.y <= 1) == (c.y - c.x > -1))
        self.assertTrue( ((c.x - c.y == 1) & (c.x == 1) ) == ((c.x == 1) & (c.y == 0)) )
        self.assertTrue( (c.x - c.y != 1)  == ((c.x - c.y > 1) | (c.x - c.y < 1)) )
    def test_zero(self):
        c = self.c
        self.assertFalse( (c.x == 1).hasZero())
        self.assertFalse( (c.x > 1).hasZero())
        self.assertTrue( (c.x < 1).hasZero())
        self.assertTrue( ((c.x == 1) & (c.z == 2)).setZero() ==  ((c.x == 0 ) & (c.z == 0) & (c.y ==0)  ))
        self.assertTrue( ((c.x == 1) & (c.z == 2)).setZero().hasZero())
    def test_update_clocks(self):
        c = self.c
        self.assertTrue( ((c.x == 1) | (c.z == 2)).updateValue(c.x, 2)  == (c.x == 2 ) )
        self.assertTrue( ((c.x == 1) & (c.z == 2)).resetValue(c.x)  == ((c.x == 0 ) & (c.z == 2) ) )    
        self.assertTrue( ((c.x == 1) & (c.x - c.y == 0)).updateValue(c.x, 2)  == ((c.x == 2) & (c.y == 1) ) )
    def test_str(self):
        c = self.c
        self.assertTrue(str((c.x == 1) & (c.y == 1)) == "(c.x==1 & c.x==c.y & c.y==1)")
    def test_copy(self):
        c = self.c
        a = ((c.x - c.y)==1)
        b = a.copy()
        d = b.copy()
        self.assertTrue( a == b)
        b &= (c.z == 1)
        d |= (c.z == 1)
        self.assertFalse( a == b)
        self.assertFalse( d == b)
    def test_reduce(self):
        c = self.c
        a = (c.x >= 1) | (c.x <= 1)
        self.assertTrue(a.getSize() == 2)
        a.reduce()
        self.assertTrue(a.getSize() == 1)
    def test_convex_hull(self):
        c = self.c
        d1 = (c.x >= 1) & (c.x <=2) & (c.y>=1) & (c.y <=2)
        d2 = (c.x >= 3) & (c.x <=4) & (c.y>=3) & (c.y <=4)
        d3 = (c.x - c.y <= 1) & (c.y - c.x <= 1) & (c.x >= 1) & (c.y >= 1) & (c.x <= 4) & (c.y <= 4)        
        self.assertTrue((d1 + d2) == d3)
        self.assertTrue((d1 | d2).convexHull() == d3)
        d1 += d2
        self.assertTrue(d1 == d3)
    def test_sub(self):
        c = self.c
        d1 = (c.x >= 1) & (c.x <=2) & (c.y>=1) & (c.y <=2)
        d2 = (c.x >= 3) & (c.x <=4) & (c.y>=3) & (c.y <=4)
        d3 = d1 | d2
        self.assertTrue(d3 - d1 == d2)
        d3 -= d2
        self.assertTrue(d3 == d1)
    def test_up_down(self):
        c = udbm.Context(["x", "y"]) # we need only two variables here
        d1 = (c.x >= 1) & (c.x <=2) & (c.y>=1) & (c.y <=2) 
        d2 = (c.x - c.y <= 1) & (c.y - c.x <= 1) & (c.x >= 1) & (c.y >= 1)
        d3 = (c.x - c.y <= 1) & (c.y - c.x <= 1) & (c.x <= 2) & (c.y <= 2)        
        self.assertTrue(d1.up() == d2)
        self.assertTrue(d1.down() == d3)
    def test_isnt_mutable(self):
        c = self.c
        d1 = (c.x - c.y <= 1) & (c.y - c.x <= 1) & (c.x >= 1) & (c.y >= 1) & (c.y <= 4) # some random 
        d2 = d1.copy()
        d2.up()
        self.assertTrue(d1 == d2)        
        d2.down()
        self.assertTrue(d1 == d2)        
        d2.down()
        self.assertTrue(d1 == d2)        
        d2.freeClock(c.x)
        self.assertTrue(d1 == d2)        
        d2.convexHull()
        self.assertTrue(d1 == d2)        
        d2.predt(d2)
        self.assertTrue(d1 == d2)        
        d2.resetValue(c.x)
        self.assertTrue(d1 == d2)        
    def test_set_init(self):
        c = self.c
        d = (c.x - c.y <= 1) & (c.y - c.x <= 1) & (c.x >= 1) & (c.y >= 1) & (c.y <= 4) # some random
        d.setInit()
        self.assertTrue(d == ((c.x >= 0) & (c.y >= 0) & (c.z >= 0)))
        self.assertTrue(d != ((c.x >= 1) & (c.y >= 0) & (c.z >= 0)))
    def test_federation_ops(self):
        c = self.c
        d1 = (c.x - c.y <= 1) & (c.y - c.x <= 1) & (c.x >= 1) & (c.y >= 1) & (c.y <= 4) # some random
        d2 = (c.x - c.y <= 1) & (c.y - c.x <= 1) & (c.x >= 1)
        self.assertTrue(d1 <= d2)
        self.assertTrue(d1 < d2)
        self.assertTrue(d2 >= d1)
        self.assertTrue(d2 > d1)
        self.assertFalse(d1 == d2)    
        self.assertTrue(d1 != d2)
    def test_intern(self):
        c = self.c
        d = (c["x"] - c["y"] <= 1)
        d.intern()
    def testExtrapolateMaxBounds(self):
        c = self.c
        v = (c.x - c.y <= 1) & (c.x < 150) & (c.z < 150) & (c.x - c.z <= 1000)  
        a = {c.x: 100, c.y:300, c.z:400}
        self.assertTrue(v.extrapolateMaxBounds(a) == ((c.x-c.y<=1) & (c.z<150)))
    def test_free_clock(self):
        c = self.c
        self.assertTrue(((c.x >= 10) & (c.y >= 10)).freeClock(c.x) == (c.y >= 10))
    def test_zero_federation(self):
        c = self.c
        self.assertTrue(c.getZeroFederation().isZero())
        self.assertTrue(c.getZeroFederation().hasZero())
        self.assertTrue(udbm.Federation(c).isZero())
        self.assertFalse((c.x==1).isZero())
        self.assertFalse((c.x==1) == c.getZeroFederation())
    def test_hash(self):
        c = self.c
        self.assertTrue((c.x==1).hash() == (c.x==1).hash())
        self.assertFalse((c.y==1).hash() == (c.x==1).hash())
        self.assertTrue(((c.x==1) | (c.y == 1)).hash() == ((c.y == 1) | (c.x==1)).hash())
    def test_isempty(self):
        c = self.c
        self.assertTrue(((c.x==1) & (c.x !=1)).isEmpty())
        self.assertFalse(((c.x==1) | (c.x !=1)).isEmpty())
        self.assertFalse((c.x==1).isEmpty())
        self.assertFalse(((c.x==1) & (c.y !=1)).isEmpty())
        self.assertTrue( (((c.x==1) & (c.x !=1)) | ((c.y==1) & (c.y !=1))).isEmpty())
    def test_tautology(self):
        c = self.c
        self.assertTrue(c.getTautologyFederation() == c.getTautologyFederation())
        a = c.getTautologyFederation()
        a &= (c.x == 1) # checking that we don't affect tautology federation
        self.assertTrue(c.getTautologyFederation() > (c.x == 1))
        self.assertTrue((c.getTautologyFederation() & (c.x == 1)) == (c.x == 1))
        c.addClockByName('xx')
        assert((c.x <=2) & c.getTautologyFederation() == (c.x <= 2))
        assert(c.getTautologyFederation() & (c.x <=2) == (c.x <= 2))
    def test_context_items(self):
        c = self.c
        assert(len(c.items()) == 3)
        assert(('x', c.x) in c.items())
        assert(('y', c.y) in c.items())
        assert(('z', c.z) in c.items())
    def test_tighten_relax(self):
        c = self.c
        a = ((c.x >= 1 ) & (c.x < 2) & (c.y >3) & (c.y<=4)) | (c.z == 4)
        self.assertTrue(a.tightenUp() == (c.x >= 1 ) & (c.x < 2) & (c.y >3) & (c.y<4))
        self.assertTrue(a.tightenDown() == (c.z > 0) & (c.x > 1 ) & (c.x < 2) & (c.y >3) & (c.y<=4))
        self.assertTrue(a.relaxDown() == ((c.x >= 1 ) & (c.x < 2) & (c.y >= 3) & (c.y<=4) | (c.z == 4)))
#        self.assertTrue(a.relaxUp() == ((c.x >= 1 ) & (c.x <= 2) & (c.y >3) & (c.y<=4) | (c.z == 4))) # TODO add test here
        self.assertTrue(a.relaxAll() == (c.x >= 1 ) & (c.x <= 2) & (c.y >= 3) & (c.y<=4) | (c.z == 4))
    def test_invert(self):
        c = self.c        
        assert(~(c.x>=1) == (c.x<1))
        assert(~~(c.x>=1) == (c.x>=1))
        assert( ~((c.x>=1) & (c.y <= 4)) == ((c.x< 1) | (c.y > 4)))
        assert(~~((c.x>=1) & (c.y <= 4)) == ((c.x>=1) & (c.y <= 4)))
    def test_empty(self):
        c = self.c        
        assert( ((c.x >=1) | c.getEmptyFederation()) == (c.x >=1))
        assert( ((c.x >=1) & c.getEmptyFederation()) != (c.x >=1))
        assert( ((c.x >=1) & c.getEmptyFederation()) == c.getEmptyFederation())
    def test_fed_clockaccess(self):
        c = self.c
        f = c.getZeroFederation()
        self.assertTrue( (f.x == 1) == (f.x >= 1) & (f.x <= 1))
        self.assertFalse( (f.x == 1) == (f.x >= 1) & (f.x < 1))
        self.assertTrue( (f.x != 1) == ((f.x > 1) | (f.x < 1)))
        self.assertFalse( (f.x != 1) == ((f.x > 1) | (f.x <= 1)))
        self.assertTrue( (f.x == 1) & (f.y == 1)  == (f.y == 1) & (f.x == 1))
        self.assertTrue( (f.x == 1) | (f.y == 1)  == (f.y == 1) | (f.x == 1))
        self.assertFalse( (f.x == 1) | (f.y == 1)  != (f.y == 1) | (f.x == 1))
        self.assertFalse( (f.x == 1) & (f.y == 1)  != (f.y == 1) & (f.x == 1))
        self.assertTrue( (f.x == 1) & (f.y == 1)  != (f.y == 1) | (f.x == 1))
        self.assertTrue( (f.x == 1) & ((f.y == 1) | (f.z ==1))  == (f.x == 1) & (f.y == 1) |(f.x == 1) & (f.z ==1) )
        self.assertFalse( (f.x == 1) & ((f.y == 1) | (f.z ==1))  == (f.x == 1) & (f.y == 1) |(f.x == 1) )
        self.assertTrue( (f.x - f.y <= 1) == (f.y - f.x >= -1))
        self.assertFalse( (f.x - f.y <= 1) == (f.y - f.x > -1))
        self.assertTrue( ((f.x - f.y == 1) & (f.x == 1) ) == ((f.x == 1) & (f.y == 0)) )
        self.assertTrue( (f.x - f.y != 1)  == ((f.x - f.y > 1) | (f.x - f.y < 1)) )    
    def test_clock_name(self):
        c = self.c        
        self.assertTrue(c.hasClockByName('x'))
        self.assertFalse(c.hasClockByName('w'))
        self.assertTrue(str(c.x) == 'c.x')    
    def test_depend(self):
        c = self.c    
        (c.x > 1).depends(c.x)
        (c.x > 2).depends(c.x)
        (c.x > 3).depends(c.x)
        self.assertTrue((c.x > 1).depends(c.x))
        self.assertFalse((c.x > 1).depends(c.y))
        self.assertFalse(((c.x > 1)|(c.x <=1)).reduce().depends(c.x))
        self.assertTrue(((c.x > 2)|(c.x <=1)).reduce().depends(c.x))
        self.assertTrue(((c.x > 1) & (c.y > 1)).reduce().depends(c.y))
        self.assertTrue(((c.x > 1) & (c.y > 1)).reduce().depends(c.x))
        self.assertTrue(((c.x > 1) | (c.y > 1)).reduce().depends(c.y))
        self.assertTrue(((c.x > 1) | (c.y > 1)).reduce().depends(c.x))

    #def test_pointer_fun(self):
    #    c = self.c
    #    f = c.getZeroFederation()
    #    a = str(f._fed)
    #    print a
    #    #import pdb; pdb.set_trace()
    #    address = int(a.split('at 0x')[1][:-3], 16)
    #    print address

    #    f2 = udbm.udbm_int.fed_t_pointer_to_Federation(address)

    #    self.assertEqual(f, f2)

    def test_updateIncrement(self):
        c = self.c        
        a = (c.y == 5)
        b = a & (c.x - c.y == 0)

        self.assertEqual(b.updateIncrement(c.x, 1), (c.x == 6) & (c.x-c.y == 1) & (c.y == 5))

        self.assertEqual(b, (c.x == 5) & (c.x-c.y == 0) & (c.y == 5))

        b.updateIncrementInPlace(c.x, 1)
        self.assertEqual(b, (c.x == 6) & (c.x-c.y == 1) & (c.y == 5))


if __name__ == '__main__':
    unittest.main()
