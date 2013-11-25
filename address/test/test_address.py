import unittest
from ..address import Address, AddressParser
import os


class AddressTest(unittest.TestCase):
    parser = None

    def setUp(self):
        self.parser = AddressParser()

    def test_basic_full_address(self):
        addr = Address("2 N. Park Street, Madison, WI 53703", self.parser)
        self.assertTrue(addr.house_number == "2")
        self.assertTrue(addr.street_prefix == "N.")
        self.assertTrue(addr.street == "Park")
        self.assertTrue(addr.street_suffix == "St.")
        self.assertTrue(addr.city == "Madison")
        self.assertTrue(addr.state == "WI")
        self.assertTrue(addr.zip == "53703")
        self.assertTrue(addr.apartment == None)
        # self.assertTrue(addr.building == None)

    def test_multi_address(self):
        addr = Address("416/418 N. Carroll St.", self.parser)
        self.assertTrue(addr.house_number == "416")
        self.assertTrue(addr.street_prefix == "N.")
        self.assertTrue(addr.street == "Carroll")
        self.assertTrue(addr.street_suffix == "St.")
        self.assertTrue(addr.city == None)
        self.assertTrue(addr.state == None)
        self.assertTrue(addr.zip == None)
        self.assertTrue(addr.apartment == None)
        # self.assertTrue(addr.building == None)

    def test_no_suffix(self):
        addr = Address("230 Lakelawn", self.parser)
        self.assertTrue(addr.house_number == "230")
        self.assertTrue(addr.street_prefix == None)
        self.assertTrue(addr.street == "Lakelawn")
        self.assertTrue(addr.street_suffix == None)
        self.assertTrue(addr.city == None)
        self.assertTrue(addr.state == None)
        self.assertTrue(addr.zip == None)
        self.assertTrue(addr.apartment == None)
        # self.assertTrue(addr.building == None)

#     def test_building_in_front(self):
#         addr = Address("Roundhouse Apartments 626 Langdon", self.parser)
# #        print addr
#         self.assertTrue(addr.house_number == "626")
#         self.assertTrue(addr.street_prefix == None)
#         self.assertTrue(addr.street == "Langdon")
#         self.assertTrue(addr.street_suffix == None)
#         self.assertTrue(addr.city == None)
#         self.assertTrue(addr.state == None)
#         self.assertTrue(addr.zip == None)
#         self.assertTrue(addr.apartment == None)
#         # self.assertTrue(addr.building == "Roundhouse Apartments")

    def test_streets_named_after_states(self):
        addr = Address("504 W. Washington Ave.", self.parser)
        self.assertTrue(addr.house_number == "504")
        self.assertTrue(addr.street_prefix == "W.")
        self.assertTrue(addr.street == "Washington")
        self.assertTrue(addr.street_suffix == "Ave.")
        self.assertTrue(addr.city == None)
        self.assertTrue(addr.state == None)
        self.assertTrue(addr.zip == None)
        self.assertTrue(addr.apartment == None)
        # self.assertTrue(addr.building == None)

    def test_hash_apartment(self):
        addr = Address("407 West Doty St. #2", self.parser)
        self.assertTrue(addr.house_number == "407")
        self.assertTrue(addr.street_prefix == "W.")
        self.assertTrue(addr.street == "Doty")
        self.assertTrue(addr.street_suffix == "St.")
        self.assertTrue(addr.city == None)
        self.assertTrue(addr.state == None)
        self.assertTrue(addr.zip == None)
        self.assertTrue(addr.apartment == "#2")
        # self.assertTrue(addr.building == None)

    def test_stray_dash_apartment(self):
        addr = Address("407 West Doty St. - #2", self.parser)
        self.assertTrue(addr.house_number == "407")
        self.assertTrue(addr.street_prefix == "W.")
        self.assertTrue(addr.street == "Doty")
        self.assertTrue(addr.street_suffix == "St.")
        self.assertTrue(addr.city == None)
        self.assertTrue(addr.state == None)
        self.assertTrue(addr.zip == None)
        self.assertTrue(addr.apartment == "#2")
        # self.assertTrue(addr.building == None)

    def test_9_digit_zip(self):
        addr = Address("2 N. Park Street, Madison, WI 53703-0000", self.parser)
        self.assertTrue(addr.house_number == "2")
        self.assertTrue(addr.street_prefix == "N.")
        self.assertTrue(addr.street == "Park")
        self.assertTrue(addr.street_suffix == "St.")
        self.assertTrue(addr.city == "Madison")
        self.assertTrue(addr.state == "WI")
        self.assertTrue(addr.zip == "53703-0000")
        self.assertTrue(addr.apartment == None)

    def test_9_digit_zip_no_dash(self):
        addr = Address("2 N. Park Street, Madison, WI 537030000", self.parser)
        self.assertTrue(addr.house_number == "2")
        self.assertTrue(addr.street_prefix == "N.")
        self.assertTrue(addr.street == "Park")
        self.assertTrue(addr.street_suffix == "St.")
        self.assertTrue(addr.city == "Madison")
        self.assertTrue(addr.state == "WI")
        self.assertTrue(addr.zip == "537030000")
        self.assertTrue(addr.apartment == None)

    def test_suffixless_street_with_city(self):
        addr = Address("431 West Johnson, Madison, WI", self.parser)
        self.assertTrue(addr.house_number == "431")
        self.assertTrue(addr.street_prefix == "W.")
        self.assertTrue(addr.street == "Johnson")
        self.assertTrue(addr.street_suffix == None)
        self.assertTrue(addr.city == "Madison")
        self.assertTrue(addr.state == "WI")
        self.assertTrue(addr.zip == None)
        self.assertTrue(addr.apartment == None)
        # self.assertTrue(addr.building == None)
    
    def test_multi_word_city(self):
        addr = Address('351 King St. #400, San Francisco, CA, 94158', self.parser)
        self.assertEqual('351', addr.house_number)
        self.assertEqual('San Francisco', addr.city)
        self.assertEqual('#400', addr.apartment)
    
    def test_street_postdirection(self):
        addr = Address('12006 120th Pl NE, Kirkland, WA', self.parser)
        self.assertEqual('NE', addr.post_direction)
    



    # Not yet passing.
    #def test_5_digit_house_number(self):
    #    addr = Address('51691 North Scottsdale Road', self.parser)
    #    self.assertTrue(addr.house_number == "51691")
    #    self.assertTrue(addr.street_prefix == "N.")
    #    self.assertTrue(addr.street == "Scottsdale")
    #    self.assertTrue(addr.street_suffix == "Rd.")
    #    self.assertTrue(addr.city == None)
    #    self.assertTrue(addr.state == None)
    #    self.assertTrue(addr.zip == None)
    #    self.assertTrue(addr.apartment == None)


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
        self.ap.load_zips("address/zipcode.csv")
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
