# -*-*- encoding: utf-8 -*-*-

import unittest

import gmaps
import gmaps_local
import location_formatting

def get_geocode(address):
    gmaps_data = gmaps_local.fetch_raw_cached(address=address)
    geocode = gmaps.parse_geocode(gmaps_data)
    return geocode

formatting_reg_data = {
    'Shibuya': 'Shibuya, Tokyo, Japan',
    u'渋谷': 'Shibuya, Tokyo, Japan',
    'Ginza': 'Ginza, Chuo, Tokyo, Japan',
    'Osaka': 'Osaka, Osaka Prefecture, Japan',
    'Nagoya': 'Nagoya, Aichi Prefecture, Japan',
    'Kowloon': 'Kowloon, Hong Kong',
    'Hong Kong Island': 'Hong Kong Island, Hong Kong',
    'Shanghai': 'Shanghai, China',
    'Sao Paulo, Brazil': u'S\xe3o Paulo, Brazil',
    'Taipei': 'Taipei, Taiwan',
    'Miami, FL': 'Miami, FL, United States',
    'Sydney': 'Sydney, NSW, Australia',
    'Paris': 'Paris, France',
    'London': 'London, United Kingdom',
    'Helsinki': 'Helsinki, Finland',
    'Bay Area': 'San Francisco Bay Area, CA, United States',
    'Brooklyn': 'Brooklyn, New York, NY, United States',
    'Williamsburg, Brooklyn': 'Williamsburg, Brooklyn, New York, NY, United States',
    'SOMA, SF, CA': 'South of Market, San Francisco, CA, United States',
    '6 5th Street, SF, CA': 'South of Market, San Francisco, CA, United States',
    'Irvine': 'Irvine, CA, United States',
    'New England': 'New England',
}


class TestLocationFormatting(unittest.TestCase):
    def runTest(self):
        for address, final_address in formatting_reg_data.iteritems():
            formatted_address = location_formatting.format_geocode(get_geocode(address))
            if formatted_address != final_address:
                print 'formatted address for %r is %r, should be %r' % (address, formatted_address, final_address)
                print gmaps_local.fetch_raw_cached(address=address)
                self.assertEqual(final_address, formatted_address)

grouping_lists = [
    (['Miami, FL', 'Soma, SF, CA', 'Williamsburg, Brooklyn'], ['Miami, FL', 'South of Market, San Francisco, CA', 'Brooklyn, New York, NY']),
    (['Brooklyn', 'Williamsburg, Brooklyn'], ['Brooklyn', 'Williamsburg, Brooklyn']),
    (['SOMA, SF, CA', '6 5th Street, SF, CA'], ['South of Market', 'South of Market']),
    (['Bay Area', '6 5th Street, SF, CA'], ['San Francisco Bay Area, CA', 'South of Market, San Francisco, CA']),
    (['Shibuya', 'Ginza'], ['Shibuya, Tokyo', 'Ginza, Chuo, Tokyo']),
    (['Shibuya', 'Ginza', 'Osaka'], ['Shibuya, Tokyo', 'Ginza, Chuo, Tokyo', 'Osaka, Osaka Prefecture']),
    (['Nagoya', 'Sydney'], ['Nagoya, Aichi Prefecture, Japan', 'Sydney, NSW, Australia']),
]

class TestMultiLocationFormatting(unittest.TestCase):
    def runTest(self):
        for addresses, reformatted_addresses in grouping_lists:
            geocodes = [get_geocode(address) for address in addresses]
            reformatted_parts = location_formatting.format_geocodes(geocodes)
            self.assertEqual(reformatted_parts, reformatted_addresses)


if __name__ == '__main__':
    TestLocationFormatting().runTest()
    TestMultiLocationFormatting().runTest()
