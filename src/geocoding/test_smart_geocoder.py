import unittest
from unittest.mock import Mock, patch
import json
from pathlib import Path
from datetime import datetime, timedelta
from src.geocoding.smart_geocoder import SmartGeocoder
import pandas as pd

class TestSmartGeocoder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create test data directory
        cls.test_data_dir = Path(__file__).parent / 'test_data'
        cls.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test cache directory
        cls.test_cache_dir = cls.test_data_dir / 'cache'
        cls.test_cache_dir.mkdir(exist_ok=True)
        
        # Create mock district centroids
        cls.district_centroids_file = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'district_centroids.csv'
        if not cls.district_centroids_file.exists():
            with open(cls.district_centroids_file, 'w') as f:
                f.write("district,state,latitude,longitude\n")
                f.write("South Delhi,Delhi,28.5562,77.1000\n")
                f.write("Chennai,Tamil Nadu,13.0827,80.2707\n")
                f.write("Mumbai,Maharashtra,19.0760,72.8777\n")

    @patch('googlemaps.Client')
    def setUp(self, mock_google):
        """Set up test fixtures before each test method."""
        # Mock Google Maps client
        mock_google_client = Mock()
        mock_google.return_value = mock_google_client
        
        # Initialize geocoder with mocked client
        self.geocoder = SmartGeocoder(
            google_api_key="test_key",
            cache_dir=str(self.test_cache_dir)
        )

    @patch('googlemaps.Client')
    @patch('geopy.geocoders.Nominatim')
    def test_cache_operations(self, mock_nominatim, mock_google):
        """Test caching functionality"""
        test_address = "Test University, Delhi"
        test_result = {
            'latitude': 28.6139,
            'longitude': 77.2090,
            'confidence': 0.8,
            'source': 'google',
            'address_components': {},
            'validation_score': 0.9
        }
        
        # Cache result
        self.geocoder._cache_result(test_address, test_result)
        
        # Verify cache file exists
        self.assertTrue(self.geocoder.cache_file.exists())
        
        # Get cached result
        cached = self.geocoder._get_cached_result(test_address)
        self.assertIsNotNone(cached)
        self.assertEqual(cached['latitude'], test_result['latitude'])
        self.assertEqual(cached['longitude'], test_result['longitude'])

    @patch('googlemaps.Client')
    def test_google_geocoding(self, mock_google):
        """Test Google Maps geocoding"""
        test_address = "Test University, Delhi"
        
        # Setup Google Maps mock with proper response
        google_response = [{
            'geometry': {
                'location': {'lat': 28.6139, 'lng': 77.2090},
                'location_type': 'ROOFTOP'
            },
            'address_components': [
                {
                    'long_name': '110020',
                    'types': ['postal_code']
                },
                {
                    'long_name': 'South Delhi',
                    'types': ['administrative_area_level_2']
                }
            ],
            'formatted_address': 'Test Address'
        }]
        mock_google.return_value.geocode = Mock(return_value=google_response)
        
        # Re-initialize geocoder with mocked client
        self.geocoder = SmartGeocoder(
            google_api_key="test_key",
            cache_dir=str(self.test_cache_dir)
        )
        
        # Mock confidence calculation
        self.geocoder._calculate_google_confidence = Mock(return_value=0.95)
        
        result = self.geocoder._geocode_google(test_address)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['source'], 'google')
        self.assertEqual(result['latitude'], 28.6139)
        self.assertEqual(result['longitude'], 77.2090)
        self.assertTrue(result['confidence'] > 0.7)

    @patch('googlemaps.Client')
    def test_nominatim_geocoding(self, mock_google):
        """Test Nominatim geocoding"""
        # Disable Google Maps for this test
        self.geocoder.google_maps = None
        
        # Mock Nominatim response
        mock_location = Mock()
        mock_location.latitude = 28.6139
        mock_location.longitude = 77.2090
        mock_location.raw = {
            'address': {
                'postcode': '110020',
                'state': 'Delhi',
                'city': 'New Delhi'
            }
        }
        mock_location.address = "Test Address"
        self.geocoder.nominatim.geocode = Mock(return_value=mock_location)
        
        result = self.geocoder._geocode_nominatim("Test University, Delhi")
        self.assertIsNotNone(result)
        self.assertEqual(result['latitude'], 28.6139)
        self.assertEqual(result['longitude'], 77.2090)
        self.assertTrue(result['confidence'] > 0.6)

    def test_validation(self):
        """Test result validation"""
        # Valid result within India
        valid_result = {
            'latitude': 28.6139,
            'longitude': 77.2090,
            'confidence': 0.8
        }
        valid_metadata = {
            'components': {
                'district': 'South Delhi',
                'state': 'Delhi'
            }
        }
        self.assertTrue(
            self.geocoder._validate_result(valid_result, valid_metadata)
        )
        
        # Invalid result outside India
        invalid_result = {
            'latitude': 40.7128,
            'longitude': -74.0060,
            'confidence': 0.8
        }
        self.assertFalse(
            self.geocoder._validate_result(invalid_result, valid_metadata)
        )

    def test_address_variations(self):
        """Test address variation generation"""
        address = "Test University Campus, Near Metro, South Delhi, Delhi"
        metadata = {
            'components': {
                'landmarks': [
                    {'type': 'educational', 'name': 'University Campus'},
                    {'type': 'transport', 'name': 'Metro'}
                ],
                'district': 'South Delhi',
                'state': 'Delhi',
                'pin': '110020'
            }
        }
        
        variations = self.geocoder._generate_address_variations(address, metadata)
        self.assertTrue(len(variations) > 0)
        # Should have variation without landmarks
        self.assertTrue(any('South Delhi, Delhi, 110020' in v for v in variations))

    @patch('googlemaps.Client')
    @patch('src.data_processing.address_processor.AddressProcessor')
    @patch('geopy.geocoders.Nominatim')
    def test_full_geocoding_flow(self, mock_nominatim, mock_address_processor, mock_google):
        """Test complete geocoding process"""
        # Create a new geocoder instance with mocked dependencies
        mock_google_client = Mock()
        mock_google.return_value = mock_google_client
        
        self.geocoder = SmartGeocoder(
            google_api_key="test_key",
            cache_dir=str(self.test_cache_dir)
        )
        
        # Set up the mocked Google Maps client
        google_response = [{
            'geometry': {
                'location': {'lat': 28.5449, 'lng': 77.1926},
                'location_type': 'ROOFTOP'
            },
            'address_components': [
                {'long_name': 'IIT Delhi', 'types': ['establishment']},
                {'long_name': 'South Delhi', 'types': ['administrative_area_level_2']},
                {'long_name': '110020', 'types': ['postal_code']}
            ],
            'formatted_address': 'IIT Delhi, Hauz Khas'
        }]
        mock_google_client.geocode.return_value = google_response
        self.geocoder.google_maps = mock_google_client
        
        # Mock address processor
        mock_processor = Mock()
        mock_address_processor.return_value = mock_processor
        mock_processor.process_address.return_value = (
            "IIT Delhi, Hauz Khas",
            {'components': {'district': 'South Delhi', 'state': 'Delhi', 'pin': '110020'}}
        )
        
        # Mock validation and confidence methods
        self.geocoder._validate_result = Mock(return_value=True)
        self.geocoder._calculate_validation_score = Mock(return_value=0.9)
        self.geocoder._calculate_google_confidence = Mock(return_value=0.95)
        
        # Perform geocoding
        result = self.geocoder.geocode("IIT Delhi")
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertEqual(result['source'], 'google')
        self.assertEqual(result['latitude'], 28.5449)
        self.assertEqual(result['longitude'], 77.1926)
        self.assertTrue(result['confidence'] > 0.7)
        self.assertTrue(result['validation_score'] > 0.8)

if __name__ == '__main__':
    unittest.main(verbosity=2)
