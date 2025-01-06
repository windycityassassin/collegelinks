import unittest
from address_processor import AddressProcessor

class TestAddressProcessor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = AddressProcessor()

    def test_basic_clean(self):
        """Test basic address cleaning"""
        test_cases = [
            (
                "IIT   Delhi,  Hauz  Khas,    New Delhi",
                "IIT Delhi, Hauz Khas, New Delhi"
            ),
            (
                "Anna univ; Chennai|TN",
                "Anna University, Chennai, TN"
            )
        ]
        
        for input_addr, expected in test_cases:
            cleaned = self.processor._basic_clean(input_addr)
            self.assertEqual(cleaned, expected)

    def test_pin_validation(self):
        """Test PIN code validation"""
        valid_pins = ['110001', '400001', '500032']
        invalid_pins = ['999999', '123456', '000000']
        
        for pin in valid_pins:
            self.assertTrue(self.processor._validate_pin(pin))
        
        for pin in invalid_pins:
            self.assertFalse(self.processor._validate_pin(pin))

    def test_district_validation(self):
        """Test district validation"""
        valid_cases = [
            ('Mumbai', 'Maharashtra'),
            ('Chennai', 'Tamil Nadu'),
            ('Bengaluru', 'Karnataka')
        ]
        
        invalid_cases = [
            ('Mumbai', 'Tamil Nadu'),
            ('Invalid', 'Karnataka'),
            ('Chennai', 'Invalid')
        ]
        
        for district, state in valid_cases:
            self.assertTrue(
                self.processor._validate_district(district, state)
            )
        
        for district, state in invalid_cases:
            self.assertFalse(
                self.processor._validate_district(district, state)
            )

    def test_full_address_processing(self):
        """Test complete address processing"""
        test_addresses = [
            {
                'input': 'IIT Delhi, Hauz Khas, South Delhi, Delhi 110020',
                'expected_components': {
                    'pin': '110020',
                    'state': 'Delhi',
                    'district': 'South Delhi'
                }
            },
            {
                'input': 'Anna University, Chennai, Tamil Nadu 600001',
                'expected_components': {
                    'pin': '600001',
                    'state': 'Tamil Nadu',
                    'district': 'Chennai'
                }
            }
        ]
        
        for test_case in test_addresses:
            processed, metadata = self.processor.process_address(
                test_case['input']
            )
            
            # Check components
            components = metadata['components']
            for key, value in test_case['expected_components'].items():
                self.assertEqual(components.get(key), value)
            
            # Check confidence
            self.assertGreater(metadata['confidence'], 0.5)
            
            # Check processed address is not empty
            self.assertTrue(len(processed) > 0)

    def test_landmark_extraction(self):
        """Test landmark extraction"""
        address = "IIT Delhi, University Campus, Near Metro Station, Delhi"
        _, metadata = self.processor.process_address(address)
        
        landmarks = metadata['components'].get('landmarks', [])
        landmark_types = {l['type'] for l in landmarks}
        
        self.assertIn('educational', landmark_types)
        self.assertIn('transport', landmark_types)

    def test_abbreviation_expansion(self):
        """Test abbreviation expansion"""
        test_cases = [
            (
                "dept of tech, univ campus",
                "dept of Technology, University campus"
            ),
            (
                "engg coll rd",
                "Engineering College Road"
            )
        ]
        
        for input_addr, expected in test_cases:
            expanded = self.processor._expand_abbreviations(input_addr)
            self.assertEqual(expanded, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
