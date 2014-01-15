import unittest
from address import Address, AddressParser
import os

class AddressTest(unittest.TestCase):
    parser = None

    def setUp(self):
        self.parser = AddressParser()
    
    def test_basic_full_address(self):
        addr = Address("2 N. Park Street, Madison, WI 53703", self.parser)
        self.assertEqual(addr.house_number, "2")
        self.assertEqual(addr.street_prefix, "N.")
        self.assertEqual(addr.street, "Park")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, "Madison")
        self.assertEqual(addr.state, "WI")
        self.assertEqual(addr.zip, "53703")
        self.assertEqual(addr.apartment, None)
    
    def test_multi_address(self):
        addr = Address("416/418 N. Carroll St.", self.parser)
        self.assertEqual(addr.house_number, "416")
        self.assertEqual(addr.street_prefix, "N.")
        self.assertEqual(addr.street, "Carroll")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, None)
        self.assertEqual(addr.state, None)
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.apartment, None)
    
    def test_no_suffix(self):
        addr = Address("230 Lakelawn", self.parser)
        self.assertEqual(addr.house_number, "230")
        self.assertEqual(addr.street_prefix, None)
        self.assertEqual(addr.street, "Lakelawn")
        self.assertEqual(addr.street_suffix, None)
        self.assertEqual(addr.city, None)
        self.assertEqual(addr.state, None)
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.apartment, None)
    
    def test_streets_named_after_states(self):
        addr = Address("504 W. Washington Ave.", self.parser)
        self.assertEqual(addr.house_number, "504")
        self.assertEqual(addr.street_prefix, "W.")
        self.assertEqual(addr.street, "Washington")
        self.assertEqual(addr.street_suffix, "Ave.")
        self.assertEqual(addr.city, None)
        self.assertEqual(addr.state, None)
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.apartment, None)
    
    def test_hash_apartment(self):
        addr = Address("407 West Doty St. #2", self.parser)
        self.assertEqual(addr.house_number, "407")
        self.assertEqual(addr.street_prefix, "W.")
        self.assertEqual(addr.street, "Doty")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, None)
        self.assertEqual(addr.state, None)
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.apartment, "#2")
    
    def test_stray_dash_apartment(self):
        addr = Address("407 West Doty St. - #2", self.parser)
        self.assertEqual(addr.house_number, "407")
        self.assertEqual(addr.street_prefix, "W.")
        self.assertEqual(addr.street, "Doty")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, None)
        self.assertEqual(addr.state, None)
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.apartment, "#2")
    
    def test_9_digit_zip(self):
        addr = Address("2 N. Park Street, Madison, WI 53703-0000", self.parser)
        self.assertEqual(addr.house_number, "2")
        self.assertEqual(addr.street_prefix, "N.")
        self.assertEqual(addr.street, "Park")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, "Madison")
        self.assertEqual(addr.state, "WI")
        self.assertEqual(addr.zip, "53703-0000")
        self.assertEqual(addr.apartment, None)
    
    def test_9_digit_zip_no_dash(self):
        addr = Address("2 N. Park Street, Madison, WI 537030000", self.parser)
        self.assertEqual(addr.house_number, "2")
        self.assertEqual(addr.street_prefix, "N.")
        self.assertEqual(addr.street, "Park")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, "Madison")
        self.assertEqual(addr.state, "WI")
        self.assertEqual(addr.zip, "537030000")
        self.assertEqual(addr.apartment, None)
    
    def test_suffixless_street_with_city(self):
        addr = Address("431 West Johnson, Madison, WI", self.parser)
        self.assertEqual(addr.house_number, "431")
        self.assertEqual(addr.street_prefix, "W.")
        self.assertEqual(addr.street, "Johnson")
        self.assertEqual(addr.street_suffix, None)
        self.assertEqual(addr.city, "Madison")
        self.assertEqual(addr.state, "WI")
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.apartment, None)
    
    def test_multi_word_city(self):
        addr = Address('351 King St. #400, San Francisco, CA, 94158', self.parser)
        self.assertEqual('351', addr.house_number)
        self.assertEqual('San Francisco', addr.city)
        self.assertEqual('#400', addr.apartment)
    
    def test_street_postdirection(self):
        addr = Address('12006 120th Pl NE, Kirkland, WA', self.parser)
        self.assertEqual('NE', addr.post_direction)
    
if __name__ == '__main__':
    unittest.main()
