# Meant to parse out address lines, minus city,state,zip into a usable dict for address matching
# Ignores periods and commas, because no one cares.

import re
import csv
import os
import dstk
import sys

# Keep lowercase, no periods
# Requires numbers first, then option dash plus numbers.
street_num_regex = r'^(\d+)([-/]?)(\d*)$'

apartment_regex_number = r'(#?)(\d*)(\w*)'
cwd = os.path.dirname(os.path.realpath(__file__))


# Procedure: Go through backwards. First check for apartment number, then
# street suffix, street name, street prefix, then building. For each sub,
# check if that spot is already filled in the dict.
class Address(object):
  
    # address components
    primary_number = None             # House or building number
    street_name = None 
    street_predirection = None        # Directional that appears before street_name
    street_postdirection = None       # Directional that appears after street_name
    street_suffix = None              # eg Avenue, Street, Road, Drive
    secondary_number = None           # secondary_designator of suite number, if any
    secondary_designator = None       # Location within a complex/building (ste, apt, etc.)
    extra_secondary_designator = None # captures subsequent designators eg room in suite 300 room 7
    pmb_designator = None             # Private Mail box
    pmb_number = None                 
    city = None                       # Accepted or proper name
    state = None
    zip = None                        # 5 digit zip code
    plus4 = None                      # the 4 digit add on code
    
    # Only set for dstk
    lat = None
    lng = None
    last_matched = None
    unmatched = False
    # Only used for debug
    line_number = -1
    # Confidence value from DSTK. 0 - 1, -1 for not set.
    confidence = -1

    # Cache the zip lookup db.
    zips = None

    def __init__(self, address, parser, line_number=-1, logger=None, dstk_pre_parse=None):
        """
        @dstk_pre_parse: a single value from a dstk multiple street2coordinates return. @address would be the key then.
        """
        self.parser = parser
        self.line_number = line_number
        self.original = self._clean(address)
        self.logger = logger
        if address is None:
            return
        address = self.preprocess_address(address)
        if parser.backend == "dstk":
            # if self.logger: self.logger.debug("Preparsed: {0}".format(dstk_pre_parse))
            self.dstk_parse(address, parser, pre_parsed_address=dstk_pre_parse)
        elif parser.backend == "default":
            self.parse_address(address)
        else:
            raise ValueError("Parser gave invalid backend, must be either 'default' or 'dstk'.")

        if self.primary_number is None or self.primary_number <= 0:
            raise InvalidAddressException("Addresses must have house numbers.")
        elif self.street_name is None or self.street_name == "":
            raise InvalidAddressException("Addresses must have streets.")
            # if self.primary_number is None or self.street_name is None or self.street_suffix is None:
            # raise ValueError("Street addresses require house_number, street, and street_suffix")

    def parse_address(self, address):
        # print "YOU ARE PARSING AN ADDRESS"
        # Save the original string

        # Get rid of periods and commas, split by spaces, reverse.
        # Periods should not exist, remove them. Commas separate tokens. It's possible we can use commas for better guessing.
        address = address.strip().replace('.', '')
        # We'll use this for guessing.
        self.comma_separated_address = address.split(',')
        address = address.replace(',', '')

        # First, do some preprocessing
        # address = self.preprocess_address(address)

        # Try all our address regexes. USPS says parse from the back.
        address = reversed(address.split())
        # Save unmatched to process after the rest is processed.
        unmatched = []
        # Use for contextual data
        for token in address:
        #            print token, self
            # Check zip code first
            if self.check_zip(token):
                continue
            if self.check_state(token):
                continue
            if self.check_city(token):
                continue
            if self.check_street_suffix(token):
                continue
            if self.check_house_number(token):
                continue
            if self.check_street_prefix(token):
                continue
            if self.check_street(token):
                continue
                # if self.check_building(token):
            #     continue
            if self.guess_unmatched(token):
                continue
            unmatched.append(token)

        # Post processing

        for token in unmatched:
        #            print "Unmatched token: ", token
            if self.check_apartment_number(token):
                continue
                # print "Unmatched token: ", token
            #            print "Original address: ", self.original
            self.unmatched = True

    def preprocess_address(self, address):
        """
        Takes a basic address and attempts to clean it up, extract reasonably assured bits that may throw off the
        rest of the parsing, and return the cleaned address.
        """
        # Run some basic cleaning
        address = address.replace("# ", "#")
        address = address.replace(" & ", "&")
        # Clear the address of things like 'X units', which shouldn't be in an address anyway. We won't save this for now.
        if re.search(r"-?-?\w+ units", address, re.IGNORECASE):
            address = re.sub(r"-?-?\w+ units", "", address, flags=re.IGNORECASE)
            # Sometimes buildings are put in parantheses.
        # building_match = re.search(r"\(.*\)", address, re.IGNORECASE)
        # if building_match:
        #     self.building = self._clean(building_match.group().replace('(', '').replace(')', ''))
        #     address = re.sub(r"\(.*\)", "", address, flags=re.IGNORECASE)
        # Now let's get the apartment stuff out of the way. Using only sure match regexes, delete apartment parts from
        # the address. This prevents things like "Unit" being the street name.
        apartment_regexes = [r'#\w+ & \w+', '#\w+ rm \w+', "#\w+-\w", r'apt #{0,1}\w+', r'apartment #{0,1}\w+', r'#\w+',
                             r'# \w+', r'rm \w+', r'unit #?\w+', r'units #?\w+', r'- #{0,1}\w+', r'no\s?\d+\w*',
                             r'style\s\w{1,2}', r'townhouse style\s\w{1,2}']
        for regex in apartment_regexes:
            apartment_match = re.search(regex, address, re.IGNORECASE)
            if apartment_match:
            #                print "Matched regex: ", regex, apartment_match.group()
                self.secondary_designator = self._clean(apartment_match.group())
                address = re.sub(regex, "", address, flags=re.IGNORECASE)
            # Now check for things like ",  ," which throw off dstk
        address = re.sub(r"\,\s*\,", ",", address)
        return address

    def check_zip(self, token):
        """
        Returns true if token is matches a zip code (5 numbers or 9 numbers). Zip code must be the last token in an
        address (minus anything removed during preprocessing such as --2 units.
        """
        if self.zip is None:
            # print "last matched", self.last_matched
            if self.last_matched is not None:
                return False
                # print "zip check", len(token) == 5, re.match(r"\d{5}", token)
            if re.match(r"\d{5}(-?\d{0,4})?", token):
                self.zip = self._clean(token)
                return True

        return False

    def check_state(self, token):
        """
        Check if state is in either the keys or values of our states list. Must come before the suffix.
        """
        # print "zip", self.zip
        if len(token) == 2 and self.state is None:
            if token.capitalize() in self.parser.states.keys():
                self.state = self._clean(self.parser.states[token.capitalize()])
                return True
            elif token.upper() in self.parser.states.values():
                self.state = self._clean(token.upper())
                return True
        if self.state is None and self.street_suffix is None and len(self.comma_separated_address) > 1:
            if token.capitalize() in self.parser.states.keys():
                self.state = self._clean(self.parser.states[token.capitalize()])
                return True
            elif token.upper() in self.parser.states.values():
                self.state = self._clean(token.upper())
                return True
        return False

    def check_city(self, token):
        """
        Check if there is a known city from our city list. Must come before the suffix.
        """
        shortened_cities = {'saint': 'st.'}
        if self.city is None and self.state is not None and self.street_suffix is None:
            if token.lower() in self.parser.cities:
                self.city = self._clean(token.capitalize())
                return True
            return False
            # Check that we're in the correct location, and that we have at least one comma in the address
        if self.city is None and self.secondary_designator is None and self.street_suffix is None and len(
                self.comma_separated_address) > 1:
            if token.lower() in self.parser.cities:
                self.city = self._clean(token.capitalize())
                return True
            return False
        # Multi word cities
        if self.city is not None and self.street_suffix is None and self.street_name is None:
            #print "Checking for multi part city", token.lower(), token.lower() in shortened_cities.keys()
            if token.lower() + ' ' + self.city in self.parser.cities:
                self.city = self._clean((token.lower() + ' ' + self.city).capitalize())
                return True
            if token.lower() in shortened_cities.keys():
                token = shortened_cities[token.lower()]
                #print "Checking for shorted multi part city", token.lower() + ' ' + self.city
                if token.lower() + ' ' + self.city.lower() in self.parser.cities:
                    self.city = self._clean(token.capitalize() + ' ' + self.city.capitalize())
                    return True

    def check_apartment_number(self, token):
        """
        Finds apartment, unit, #, etc, regardless of spot in string. This needs to come after everything else has been ruled out,
        because it has a lot of false positives.
        """
        apartment_regexes = [r'#\w+ & \w+', '#\w+ rm \w+', "#\w+-\w", r'apt #{0,1}\w+', r'apartment #{0,1}\w+', r'#\w+',
                             r'# \w+', r'rm \w+', r'unit #?\w+', r'units #?\w+', r'- #{0,1}\w+', r'no\s?\d+\w*',
                             r'style\s\w{1,2}', r'\d{1,4}/\d{1,4}', r'\d{1,4}', r'\w{1,2}']
        for regex in apartment_regexes:
            if re.match(regex, token.lower()):
                self.secondary_designator = self._clean(token)
                return True
            #        if self.secondary_designator is None and re.match(apartment_regex_number, token.lower()):
            ##            print "Apt regex"
            #            self.secondary_designator = token
            #            return True
            ## If we come on apt or apartment and already have an apartment number, add apt or apartment to the front
        if self.secondary_designator and token.lower() in ['apt', 'apartment']:
        #            print "Apt in a_n"
            self.secondary_designator = self._clean(token + ' ' + self.secondary_designator)
            return True

        if not self.street_suffix and not self.street_name and not self.secondary_designator:
        #            print "Searching for unmatched term: ", token, token.lower(),
            if re.match(r'\d?\w?', token.lower()):
                self.secondary_designator = self._clean(token)
                return True
        return False

    def check_street_suffix(self, token):
        """
        Attempts to match a street suffix. If found, it will return the abbreviation, with the first letter capitalized
        and a period after it. E.g. "St." or "Ave."
        """
        # Suffix must come before street
        # print "Suffix check", token, "suffix", self.street_suffix, "street", self.street_name
        if self.street_suffix is None and self.street_name is None:
            # print "upper", token.upper()
            if token.upper() in self.parser.suffixes.keys():
                suffix = self.parser.suffixes[token.upper()]
                self.street_suffix = self._clean(suffix.capitalize() + '.')
                return True
            elif token.upper() in self.parser.suffixes.values():
                self.street_suffix = self._clean(token.capitalize() + '.')
                return True
        return False

    def check_street(self, token):
        """
        Let's assume a street comes before a prefix and after a suffix. This isn't always the case, but we'll deal
        with that in our guessing game. Also, two word street names...well...

        This check must come after the checks for house_number and street_prefix to help us deal with multi word streets.
        """
        # First check for single word streets between a prefix and a suffix
        if self.street_name is None and self.street_suffix is not None and self.street_predirection is None and self.primary_number is None:
            self.street_name = self._clean(token.capitalize())
            return True
        # Now check for multiple word streets. This check must come after the check for street_prefix and house_number for this reason.
        elif self.street_name is not None and self.street_suffix is not None and self.street_predirection is None and self.primary_number is None:
            self.street_name = self._clean(token.capitalize() + ' ' + self.street_name)
            return True
        if not self.street_suffix and not self.street_name and token.lower() in self.parser.streets:
            self.street_name = self._clean(token)
            return True
        return False

    def check_street_prefix(self, token):
        """
        Finds street prefixes, such as N. or Northwest, before a street name. Standardizes to 1 or two letters, followed
        by a period.
        """
        if self.street_name and not self.street_predirection and token.lower().replace('.', '') in self.parser.prefixes.keys():
            self.street_predirection = self._clean(self.parser.prefixes[token.lower().replace('.', '')])
            return True
        return False

    def check_house_number(self, token):
        """
        Attempts to find a house number, generally the first thing in an address. If anything is in front of it,
        we assume it is a building name.
        """
        if self.street_name and self.primary_number is None and re.match(street_num_regex, token.lower()):
            if '/' in token:
                token = token.split('/')[0]
            if '-' in token:
                token = token.split('-')[0]
            self.primary_number = self._clean(str(token))
            return True
        return False

    def check_building(self, token):
        """
        Building name check. If we have leftover and everything else is set, probably building names.
        Allows for multi word building names.
        """
        if self.street_name and self.primary_number:
            if not self.building:
                self.building = self._clean(token)
            else:
                self.building = self._clean(token + ' ' + self.building)
            return True
        return False

    def guess_unmatched(self, token):
        """
        When we find something that doesn't match, we can make an educated guess and log it as such.
        """
        # Check if this is probably an apartment:
        if token.lower() in ['apt', 'apartment']:
            return False
            # Stray dashes are likely useless
        if token.strip() == '-':
            return True
            # Almost definitely not a street if it is one or two characters long.
        if len(token) <= 2:
            return False
            # Let's check for a suffix-less street.
        if self.street_suffix is None and self.street_name is None and self.street_predirection is None and self.primary_number is None:
            # Streets will just be letters
            if re.match(r"[A-Za-z]", token):
                if self.line_number >= 0:
                    pass
                #                    print "{0}: Guessing suffix-less street: ".format(self.line_number), token
                else:
                #                    print "Guessing suffix-less street: ", token
                    pass
                self.street_name = self._clean(token.capitalize())
                return True
        return False

    def full_address(self):
        """
        Print the address in a human readable format
        """
        addr = ""
        # if self.building:
        #     addr = addr + "(" + self.building + ") "
        if self.primary_number:
            addr = addr + self.primary_number
        if self.street_predirection:
            addr = addr + " " + self.street_predirection
        if self.street_name:
            addr = addr + " " + self.street_name
        if self.street_suffix:
            addr = addr + " " + self.street_suffix
        if self.secondary_designator:
            addr = addr + " " + self.secondary_designator
        if self.city:
            addr = addr + ", " + self.city
        if self.state:
            addr = addr + ", " + self.state
        if self.zip:
            addr = addr + " " + self.zip
        return addr

    def zip_info(self, zip):
        """
        Given a zip, find the info from zipcode.csv, which is cached in self.parser. Only uses the first
        5 digits of the zip. Returns either a dict with the zip info (zip, city, state, lat, lng, timezone,
        dst) or None if not found in the file.
        """
        try:
            return self.parser.zips[zip[0:5]]
        except KeyError:
            return None

    def __repr__(self):
        return unicode(self)

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        address_dict = {
            "house_number": self.primary_number,
            "street_prefix": self.street_predirection,
            "street": self.street_name,
            "street_suffix": self.street_suffix,
            "apartment": self.secondary_designator,
            # "building": self.building,
            "city": self.city,
            "state": self.state,
            "zip": self.zip
        }
        # print "Address Dict", address_dict
        return u"Address - House number: {house_number} Prefix: {street_prefix} Street: {street} Suffix: {street_suffix}" \
               u" Apartment: {apartment} City,State,Zip: {city}, {state} {zip}".format(**address_dict)

    def dstk_parse(self, address, parser, pre_parsed_address=None):
        """
        Given an address string, use DSTK to parse the address and then coerce it to a normal Address object.
        pre_parsed_address for multi parsed string. Gives the value part for single dstk return value. If
        pre_parsed_address is None, parse it via dstk on its own.
        """
        if pre_parsed_address:
            dstk_address = pre_parsed_address
        else:
            if self.logger: self.logger.debug("Asking DSTK for address parse {0}".format(address.encode("ascii", "ignore")))
            dstk_address = parser.dstk.street2coordinates(address)
            # if self.logger: self.logger.debug("dstk return: {0}".format(dstk_address))
        if 'confidence' not in dstk_address:
            raise InvalidAddressException("Could not deal with DSTK return: {0}".format(dstk_address))
        if dstk_address['street_address'] == "":
            raise InvalidAddressException("Empty street address in DSTK return: {0}".format(dstk_address))
        if dstk_address['street_number']  is None or dstk_address['street_name'] is None:
            raise InvalidAddressException("House number or street name was Non in DSTK return: {0}".format(dstk_address))
        if dstk_address['confidence'] < parser.required_confidence:
            raise DSTKConfidenceTooLowException("Required confidence: {0}. Got confidence: {1}. Address: {2}. Return: {3}.".format(parser.required_confidence, dstk_address['confidence'], address.encode("ascii", "ignore"), dstk_address))
        self.confidence = dstk_address['confidence']
        if 'street_address' in dstk_address:
            intersections = self._get_dstk_intersections(address, dstk_address['street_address'])
        if self.logger: self.logger.debug("Confidence: {0}.".format(dstk_address['confidence']))
        if self.logger: self.logger.debug("Address: {0}.".format(address))
        if self.logger: self.logger.debug("Return: {0}.".format(dstk_address))
        # if self.logger: self.logger.debug("")

        addr = dstk_address
        if addr is None:
            raise InvalidAddressException("DSTK could not parse address: {0}".format(self.original))
        if "street_number" in addr:
            if addr["street_number"] not in address:
                raise InvalidAddressException("DSTK returned a house number not in the original address: {0}".format(addr))
            self.primary_number = addr["street_number"]
        else:
            raise InvalidAddressException("(dstk) Addresses must have house numbers: {0}".format(addr))

        if "locality" in addr:
            self.city = addr["locality"]
            # DSTK shouldn't be returning unknown cities
            if addr["locality"] not in address:
                raise InvalidAddressException("DSTK returned a city not in the address. City: {0}, Address: {1}.".format(self.city, address))
        if "region" in addr:
            self.state = addr["region"]
            # if "fips_county" in addr:
            # self.zip = addr["fips_county"]
        if "latitude" in addr:
            self.lat = addr["latitude"]
        if "longitude" in addr:
            self.lng = addr["longitude"]
            # Try and find the apartment
        # First remove the street_address (this doesn't include apartment)
        if "street_address" in addr:
            apartment = address.replace(addr["street_address"], '')
        # Make sure the city doesn't somehow come before the street in the original string.

            # try:
            #     end_pos = re.search("(" + addr["locality"] + ")", apartment).start(1) - 1
            #     # self.secondary_designator = apartment[:end_pos]
            # except Exception:
            #     pass
            # self.secondary_designator = None
        # Now that we have an address, try to parse out street suffix, prefix, and street
        if self.secondary_designator:
            street_addr = addr["street_address"].replace(self.secondary_designator, '')
        else:
            street_addr = addr["street_address"]

        # We should be left with only prefix, street, suffix. Go for suffix first.
        split_addr = street_addr.split()
        if len(split_addr) == 0:
            if self.logger: self.logger.debug("Could not split street_address: {0}".format(addr))
            raise InvalidAddressException("Could not split street_address: {0}".format(addr))
        # Get rid of house_number
        if split_addr[0] == self.primary_number:
            split_addr = split_addr[1:]
        if self.logger: self.logger.debug("Checking {0} for suffixes".format(split_addr[-1].upper()))
        if split_addr[-1].upper() in parser.suffixes.keys() or split_addr[-1].upper() in parser.suffixes.values():
            self.street_suffix = split_addr[-1]
            split_addr = split_addr[:-1]
        if self.logger: self.logger.debug("Checking {0} for prefixes".format(split_addr[0].lower()))
        if split_addr[0].lower() in parser.prefixes.keys() or split_addr[0].upper() in parser.prefixes.values() or \
                                split_addr[0].upper() + '.' in parser.prefixes.values():
            if split_addr[0][-1] == '.':
                self.street_predirection = split_addr[0].upper()
            else:
                self.street_predirection = split_addr[0].upper() + '.'
            if self.logger: self.logger.debug("Saving prefix: {0}".format(self.street_predirection))
            split_addr = split_addr[1:]
        if self.logger: self.logger.debug("Saving street: {0}".format(split_addr))
        self.street_name = " ".join(split_addr)
        # DSTK shouldn't be guessing cities that come before streets.
        match = re.search(self.street_name, address)
        if match is None:
            raise InvalidAddressException("DSTK picked a street not in the original address. Street: {0}. Address: {1}.".format(self.street_name, address))
        street_position = match
        match = re.search(self.city, address)
        if match is None:
            raise InvalidAddressException("DSTK picked a city not in the original address. City: {0}. Address: {1}.".format(self.city, address))
        city_position = match
        if city_position.start(0) < street_position.end(0):
            raise InvalidAddressException("DSTK picked a street that comes after the city. Street: {0}. City: {1}. Address: {2}.".format(self.street_name, self.city, address))
        if self.logger: self.logger.debug("Successful DSTK address: {0}, house: {1}, street: {2}\n".format(self.original, self.primary_number, self.street_name))

    def _get_dstk_intersections(self, address, dstk_address):
        """
        Find the unique tokens in the original address and the returned address.
        """
        # Normalize both addresses
        normalized_address = self._normalize(address)
        normalized_dstk_address = self._normalize(dstk_address)
        address_uniques = set(normalized_address) - set(normalized_dstk_address)
        dstk_address_uniques = set(normalized_dstk_address) - set(normalized_address)
        if self.logger: self.logger.debug("Address Uniques {0}".format(address_uniques))
        if self.logger: self.logger.debug("DSTK Address Uniques {0}".format(dstk_address_uniques))
        return (len(address_uniques), len(dstk_address_uniques))

    def _normalize(self, address):
        """
        Normalize prefixes, suffixes and other to make matching original to returned easier.
        """
        normalized_address = []
        if self.logger: self.logger.debug("Normalizing Address: {0}".format(address))
        for token in address.split():
            if token.upper() in self.parser.suffixes.keys():
                normalized_address.append(self.parser.suffixes[token.upper()].lower())
            elif token.upper() in self.parser.suffixes.values():
                normalized_address.append(token.lower())
            elif token.upper().replace('.', '') in self.parser.suffixes.values():
                normalized_address.append(token.lower().replace('.', ''))
            elif token.lower() in self.parser.prefixes.keys():
                normalized_address.append(self.parser.prefixes[token.lower()].lower())
            elif token.upper() in self.parser.prefixes.values():
                normalized_address.append(token.lower()[:-1])
            elif token.upper() + '.' in self.parser.prefixes.values():
                normalized_address.append(token.lower())
            else:
                normalized_address.append(token.lower())
        return normalized_address

    def _clean(self, item):
        if item is None:
            return None
        else:
            return item.encode("utf-8", "replace")

def create_cities_csv(filename="places2k.txt", output="cities.csv"):
    """
    Takes the places2k.txt from USPS and creates a simple file of all cities.
    """
    with open(filename, 'r') as city_file:
        with open(output, 'w') as out:
            for line in city_file:
                # Drop Puerto Rico (just looking for the 50 states)
                if line[0:2] == "PR":
                    continue
                    # Per census.gov, characters 9-72 are the name of the city or place. Cut ,off the last part, which is city, town, etc.
                #                    print " ".join(line[9:72].split()[:-1])
                out.write(" ".join(line[9:72].split()[:-1]) + '\n')


class InvalidAddressException(Exception):
    pass

class DSTKConfidenceTooLowException(Exception):
    pass

