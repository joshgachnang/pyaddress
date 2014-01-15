import unittest
from address import AddressParser
import os

cwd = os.path.dirname(os.path.dirname((os.path.realpath(__file__))))

class AddressParserTest(unittest.TestCase):
    ap = None

    def setUp(self):
        self.ap = AddressParser()
    
    def test_load_suffixes(self):
        self.assertEqual(self.ap.suffixes["ALLEY"], "ALY")
    
    def test_load_cities(self):
        self.assertTrue("wisconsin rapids" in self.ap.cities)
    
    def test_load_states(self):
        self.assertEqual(self.ap.states["Wisconsin"], "WI")
    
    def test_load_zips(self):
        self.ap.load_zips(os.path.join(cwd, "zipcodes.csv"))
        last = self.ap.zips["99950"]
        self.assertEqual(last["zip"], "99950")
        self.assertEqual(last["city"], "Ketchikan")
        self.assertEqual(last["state"], "AK")
        self.assertEqual(last["lat"], "55.875767")
        self.assertEqual(last["lng"], "-131.46633")
        self.assertEqual(last["timezone"], "-9")
        self.assertEqual(last["dst"], True)
    
if __name__ == '__main__':
    unittest.main()
