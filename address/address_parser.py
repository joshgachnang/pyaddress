#from address import Address
import dstk
import os

cwd = os.path.dirname(os.path.realpath(__file__))


class AddressParser(object):
    """
    AddressParser will be use to create Address objects. It contains a list of preseeded cities, states, prefixes,
    suffixes, and street names that will help the Address object correctly parse the given string. It is loaded
    with defaults that work in the average case, but can be adjusted for specific cases.
    """
    suffixes = {}
    # Lower case list of cities, used as a hint
    cities = []
    # Lower case list of streets, used as a hint
    streets = []
    prefixes = {
        "n": "N.", "e": "E.", "s": "S.", "w": "W.", "ne": "NE.", "nw": "NW.", 'se': "SE.", 'sw': "SW.", 'north': "N.",
        'east': "E.", 'south': "S.",
        'west': "W.", 'northeast': "NE.", 'northwest': "NW.", 'southeast': "SE.", 'southwest': "SW."}
    states = {
        'Mississippi': 'MS', 'Oklahoma': 'OK', 'Delaware': 'DE', 'Minnesota': 'MN', 'Illinois': 'IL', 'Arkansas': 'AR',
        'New Mexico': 'NM', 'Indiana': 'IN', 'Maryland': 'MD', 'Louisiana': 'LA', 'Idaho': 'ID', 'Wyoming': 'WY',
        'Tennessee': 'TN', 'Arizona': 'AZ', 'Iowa': 'IA', 'Michigan': 'MI', 'Kansas': 'KS', 'Utah': 'UT',
        'Virginia': 'VA', 'Oregon': 'OR', 'Connecticut': 'CT', 'Montana': 'MT', 'California': 'CA',
        'Massachusetts': 'MA', 'West Virginia': 'WV', 'South Carolina': 'SC', 'New Hampshire': 'NH',
        'Wisconsin': 'WI', 'Vermont': 'VT', 'Georgia': 'GA', 'North Dakota': 'ND', 'Pennsylvania': 'PA',
        'Florida': 'FL', 'Alaska': 'AK', 'Kentucky': 'KY', 'Hawaii': 'HI', 'Nebraska': 'NE', 'Missouri': 'MO',
        'Ohio': 'OH', 'Alabama': 'AL', 'New York': 'NY', 'South Dakota': 'SD', 'Colorado': 'CO', 'New Jersey': 'NJ',
        'Washington': 'WA', 'North Carolina': 'NC', 'District of Columbia': 'DC', 'Texas': 'TX', 'Nevada': 'NV',
        'Maine': 'ME', 'Rhode Island': 'RI'}
    zips = None

    def __init__(self, suffixes=None, cities=None, streets=None, zips=None, logger=None, backend="default"):
        """
        suffixes, cities and streets provide a chance to use different lists than the provided lists.
        suffixes is probably good for most users, unless you have some suffixes not recognized by USPS.
        cities is a very expansive list that may lead to false positives in some cases. If you only have a few cities
        you know will show up, provide your own list for better accuracy. If you are doing addresses across the US,
        the provided list is probably better.
        streets can be used to limit the list of possible streets the address are on. It comes blank by default and
        uses positional clues instead. If you are instead just doing a couple cities, a list of all possible streets
        will decrease incorrect street names.
        Valid backends include "default" and "dstk". If backend is dstk, it requires a dstk_api_base. Example of
        dstk_api_base would be 'http://example.com'.
        """
        self.logger = logger
        self.backend = backend
        if suffixes:
            self.suffixes = suffixes
        else:
            self.load_suffixes(os.path.join(cwd, "suffixes.csv"))
        if cities:
            self.cities = cities
        else:
            self.load_cities(os.path.join(cwd, "cities.csv"))
        if streets:
            self.streets = streets
        else:
            self.load_streets(os.path.join(cwd, "streets.csv"))
        if zips:
            self.zips = zips
        else:
            self.load_zips(os.path.join(cwd, "zipcodes.csv"))

    def parse_address(self, address, line_number=-1):
        """
        Return an Address object from the given address. Passes itself to the Address constructor to use all the custom
        loaded suffixes, cities, etc.
        """
        return Address(address, self, line_number, self.logger)

    def load_suffixes(self, filename):
        """
        Build the suffix dictionary. The keys will be possible long versions, and the values will be the
        accepted abbreviations. Everything should be stored using the value version, and you can search all
        by using building a set of self.suffixes.keys() and self.suffixes.values().
        """
        with open(filename, 'r') as f:
            for line in f:
                # Make sure we have key and value
                if len(line.split(',')) != 2:
                    continue
                    # Strip off newlines.
                self.suffixes[line.strip().split(',')[0]] = line.strip().split(',')[1]

    def load_cities(self, filename):
        """
        Load up all cities in lowercase for easier matching. The file should have one city per line, with no extra
        characters. This isn't strictly required, but will vastly increase the accuracy.
        """
        with open(filename, 'r') as f:
            for line in f:
                self.cities.append(line.strip().lower())

    def load_streets(self, filename):
        """
        Load up all streets in lowercase for easier matching. The file should have one street per line, with no extra
        characters. This isn't strictly required, but will vastly increase the accuracy.
        """
        with open(filename, 'r') as f:
            for line in f:
                self.streets.append(line.strip().lower())

    def load_zips(self, filename):
        """
        Caches the zip file into memory. Erases previously cached data.
        """
        self.zips = {}
        with open(filename, 'r') as zipfile:
            for line in zipfile.readlines():
                if line.strip() == "":
                    continue
                line = line.replace('"', '').replace('\n', '')
                members = line.split(',')
                if members[0] in self.zips:
                    print "Duplicate zip info!", members[0]
                self.zips[members[0]] = {
                    "zip": members[0],
                    "city": members[1],
                    "state": members[2],
                    "lat": members[3],
                    "lng": members[4],
                    "timezone": members[5],
                    # Sets to True for dst==1, False for dst==0
                    "dst": members[6] == "1"
                }


class DSTKAddressParser(AddressParser):
    def __init__(self, suffixes=None, cities=None, streets=None, zips=None, logger=None, backend="default",\
                 dstk_api_base=None, required_confidence=0.65):
        """
        suffixes, cities and streets provide a chance to use different lists than the provided lists.
        suffixes is probably good for most users, unless you have some suffixes not recognized by USPS.
        cities is a very expansive list that may lead to false positives in some cases. If you only have a few cities
        you know will show up, provide your own list for better accuracy. If you are doing addresses across the US,
        the provided list is probably better.
        streets can be used to limit the list of possible streets the address are on. It comes blank by default and
        uses positional clues instead. If you are instead just doing a couple cities, a list of all possible streets
        will decrease incorrect street names.
        Valid backends include "default" and "dstk". If backend is dstk, it requires a dstk_api_base. Example of
        dstk_api_base would be 'http://example.com'.
        """
        super(AddressParser, self).__init__(suffixes, cities, streets, zips, logger)
        self.dstk_api_base = dstk_api_base
        self.required_confidence = required_confidence
        if backend == "dstk":
            if dstk_api_base is None:
                raise ValueError("dstk_api_base is required for dstk backend.")
            self.dstk = dstk.DSTK({'apiBase': dstk_api_base})
        elif backend == "default":
            pass
        else:
            raise ValueError("backend must be either 'default' or 'dstk'.")

    def dstk_multi_address(self, address_list):
        if self.backend != "dstk":
            raise ValueError("Only allowed for DSTK backends.")
        if self.logger: self.logger.debug("Sending {0} possible addresses to DSTK".format(len(address_list)))
        multi_address = self.dstk.street2coordinates(address_list)
        if self.logger: self.logger.debug("Received {0} addresses from DSTK".format(len(multi_address)))
        # if self.logger: self.logger.debug("End street2coords")
        addresses = []
        # if self.logger: self.logger.debug("Multi Addresses: {0}".format(multi_address))
        for address, dstk_return in multi_address.items():
            if dstk_return is None:
                # if self.logger: self.logger.debug("DSTK None return for: {0}".format(address))
                continue
            addresses.append(Address(address, self, -1, self.logger, dstk_pre_parse=dstk_return))
            if self.logger: self.logger.debug("DSTK Address Appended: {0}".format(dstk_return))
        return addresses