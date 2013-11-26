import unittest
from address import AddressParser
import os

cwd = os.path.dirname(os.path.dirname((os.path.realpath(__file__))))


class AddressParserTest(unittest.TestCase):
    ap = None

    def setUp(self):
        self.ap = AddressParser()

    def test_load_suffixes(self):
        self.assertTrue(self.ap.suffixes["ALLEY"] == "ALY")

    def test_load_cities(self):
        self.assertTrue("wisconsin rapids" in self.ap.cities)

    def test_load_states(self):
        self.assertTrue(self.ap.states["Wisconsin"] == "WI")

    def test_load_zips(self):
        self.ap.load_zips(os.path.join(cwd, "zipcodes.csv"))
        #print self.ap._zip_info
        last = self.ap.zips["99950"]
        self.assertTrue(last["zip"] == "99950")
        self.assertTrue(last["city"] == "Ketchikan")
        self.assertTrue(last["state"] == "AK")
        self.assertTrue(last["lat"] == "55.875767")
        self.assertTrue(last["lng"] == "-131.46633")
        self.assertTrue(last["timezone"] == "-9")
        self.assertTrue(last["dst"] == True)
    # Not using preloaded streets any more.
#    def test_load_streets(self):
#        self.assertTrue("mifflin" in self.ap.streets)

if __name__ == '__main__':
    unittest.main()
