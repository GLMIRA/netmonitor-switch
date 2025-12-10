import unittest
from src.snmp.client import SNMPClient
from src.snmp.parser import SNMPParser

class TestSNMPClient(unittest.TestCase):
    def setUp(self):
        self.client = SNMPClient('localhost', 'public')
        self.parser = SNMPParser()

    def test_snmp_get(self):
        response = self.client.get('1.3.6.1.2.1.1.1.0')
        self.assertIsNotNone(response)

    def test_snmp_walk(self):
        response = self.client.walk('1.3.6.1.2.1.1')
        self.assertIsInstance(response, list)

    def test_parse_snmp_response(self):
        raw_response = b'\x30\x0e\x02\x01\x00\x02\x01\x00\x30\x0c\x06\x0b\x2b\x06\x01\x02\x01\x01\x01\x00\x05\x00'
        parsed_data = self.parser.parse(raw_response)
        self.assertIn('sysDescr', parsed_data)

if __name__ == '__main__':
    unittest.main()