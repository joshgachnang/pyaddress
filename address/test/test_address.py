import unittest
from address import Address
from address_parser import AddressParser
import os

class AddressTest(unittest.TestCase):
    parser = None

    def setUp(self):
        self.parser = AddressParser()
    
    def test_basic_full_address(self):
        addr = Address("2 N. Park Street, Madison, WI 53703", self.parser)
        self.assertEqual(addr.primary_number, "2")
        self.assertEqual(addr.street_predirection, "N.")
        self.assertEqual(addr.street_name, "Park")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, "Madison")
        self.assertEqual(addr.state, "WI")
        self.assertEqual(addr.zip, "53703")
        self.assertEqual(addr.secondary_designator, None)
    
    def test_multi_address(self):
        addr = Address("416/418 N. Carroll St.", self.parser)
        self.assertEqual(addr.primary_number, "416")
        self.assertEqual(addr.street_predirection, "N.")
        self.assertEqual(addr.street_name, "Carroll")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, None)
        self.assertEqual(addr.state, None)
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.secondary_designator, None)
    
    def test_no_suffix(self):
        addr = Address("230 Lakelawn", self.parser)
        self.assertEqual(addr.primary_number, "230")
        self.assertEqual(addr.street_predirection, None)
        self.assertEqual(addr.street_name, "Lakelawn")
        self.assertEqual(addr.street_suffix, None)
        self.assertEqual(addr.city, None)
        self.assertEqual(addr.state, None)
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.secondary_designator, None)
    
    def test_streets_named_after_states(self):
        addr = Address("504 W. Washington Ave.", self.parser)
        self.assertEqual(addr.primary_number, "504")
        self.assertEqual(addr.street_predirection, "W.")
        self.assertEqual(addr.street_name, "Washington")
        self.assertEqual(addr.street_suffix, "Ave.")
        self.assertEqual(addr.city, None)
        self.assertEqual(addr.state, None)
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.secondary_designator, None)
    
    def test_hash_apartment(self):
        addr = Address("407 West Doty St. #2", self.parser)
        self.assertEqual(addr.primary_number, "407")
        self.assertEqual(addr.street_predirection, "W.")
        self.assertEqual(addr.street_name, "Doty")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, None)
        self.assertEqual(addr.state, None)
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.secondary_designator, "#2")
    
    def test_stray_dash_apartment(self):
        addr = Address("407 West Doty St. - #2", self.parser)
        self.assertEqual(addr.primary_number, "407")
        self.assertEqual(addr.street_predirection, "W.")
        self.assertEqual(addr.street_name, "Doty")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, None)
        self.assertEqual(addr.state, None)
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.secondary_designator, "#2")
    
    def test_9_digit_zip(self):
        addr = Address("2 N. Park Street, Madison, WI 53703-0000", self.parser)
        self.assertEqual(addr.primary_number, "2")
        self.assertEqual(addr.street_predirection, "N.")
        self.assertEqual(addr.street_name, "Park")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, "Madison")
        self.assertEqual(addr.state, "WI")
        self.assertEqual(addr.zip, "53703-0000")
        self.assertEqual(addr.secondary_designator, None)
    
    def test_9_digit_zip_no_dash(self):
        addr = Address("2 N. Park Street, Madison, WI 537030000", self.parser)
        self.assertEqual(addr.primary_number, "2")
        self.assertEqual(addr.street_predirection, "N.")
        self.assertEqual(addr.street_name, "Park")
        self.assertEqual(addr.street_suffix, "St.")
        self.assertEqual(addr.city, "Madison")
        self.assertEqual(addr.state, "WI")
        self.assertEqual(addr.zip, "537030000")
        self.assertEqual(addr.secondary_designator, None)
    
    def test_suffixless_street_with_city(self):
        addr = Address("431 West Johnson, Madison, WI", self.parser)
        self.assertEqual(addr.primary_number, "431")
        self.assertEqual(addr.street_predirection, "W.")
        self.assertEqual(addr.street_name, "Johnson")
        self.assertEqual(addr.street_suffix, None)
        self.assertEqual(addr.city, "Madison")
        self.assertEqual(addr.state, "WI")
        self.assertEqual(addr.zip, None)
        self.assertEqual(addr.secondary_designator, None)
    
    def test_multi_word_city(self):
        addr = Address('351 King St. #400, San Francisco, CA, 94158', self.parser)
        self.assertEqual('351', addr.primary_number)
        self.assertEqual('San Francisco', addr.city)
        self.assertEqual('#400', addr.secondary_designator)
    
    def test_street_postdirection(self):
        addr = Address('12006 120th Pl NE, Kirkland, WA', self.parser)
        self.assertEqual('NE', addr.post_direction)
    
if __name__ == '__main__':
    unittest.main()
