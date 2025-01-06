import os
import json
import time
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from geopy.distance import geodesic
import googlemaps
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from fuzzywuzzy import fuzz
from ..data_processing.address_processor import AddressProcessor
from src.ml.geocoding_validator import MLGeocodeValidator

class SmartGeocoder:
    def __init__(self, google_api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """Initialize the smart geocoder with multiple services and caching"""
        self.google_api_key = google_api_key
        self.google_maps = googlemaps.Client(key=google_api_key) if google_api_key else None
        self.nominatim = Nominatim(user_agent="collegelinks_smart_geocoder")
        self.address_processor = AddressProcessor()
        self.ml_validator = MLGeocodeValidator()
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
        # Cache setup
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent.parent.parent / 'data' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / 'geocoding_cache.json'
        self.load_cache()
        
        # India boundaries for validation
        self.INDIA_BOUNDS = {
            'min_lat': 6.5546079,
            'max_lat': 35.6745457,
            'min_lon': 68.1113787,
            'max_lon': 97.395561
        }
        
        # Rate limiting
        self.google_delay = 0.1
        self.nominatim_delay = 1.0
        self.last_google_call = 0
        self.last_nominatim_call = 0
        
        # Load district centroids for validation
        self.district_data = self._load_district_data()

    def _load_district_data(self) -> pd.DataFrame:
        """Load district centroid data for validation"""
        data_dir = Path(__file__).parent.parent.parent / 'data' / 'raw'
        try:
            return pd.read_csv(data_dir / 'district_centroids.csv')
        except FileNotFoundError:
            self.logger.warning("District centroids file not found. Some validations will be skipped.")
            return pd.DataFrame()

    def load_cache(self):
        """Load geocoding cache from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            else:
                self.cache = {}
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}")
            self.cache = {}

    def save_cache(self):
        """Save geocoding cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")

    def _get_cache_key(self, address: str) -> str:
        """Generate cache key for an address"""
        return hashlib.md5(address.lower().encode()).hexdigest()

    def _cache_result(self, address: str, result: Dict):
        """Cache geocoding result"""
        key = self._get_cache_key(address)
        result['timestamp'] = datetime.now().isoformat()
        self.cache[key] = result
        self.save_cache()

    def _get_cached_result(self, address: str) -> Optional[Dict]:
        """Get cached result if available and not expired"""
        key = self._get_cache_key(address)
        if key in self.cache:
            result = self.cache[key]
            timestamp = datetime.fromisoformat(result['timestamp'])
            # Cache expires after 30 days
            if datetime.now() - timestamp < timedelta(days=30):
                return result
        return None

    def geocode(self, address: str, retry_count: int = 3) -> Dict:
        """
        Smart geocoding with multiple services and validation
        Returns: {
            'latitude': float,
            'longitude': float,
            'confidence': float,
            'source': str,
            'address_components': Dict,
            'validation_score': float
        }
        """
        # Check cache first
        cached = self._get_cached_result(address)
        if cached:
            return cached

        # Process address
        processed_address, address_metadata = self.address_processor.process_address(address)
        
        # Try Google Maps first
        if self.google_api_key:
            try:
                result = self._geocode_google(processed_address)
                if result and self._validate_result(result, address_metadata):
                    result['validation_score'] = self._calculate_validation_score(
                        result, address_metadata
                    )
                    self._cache_result(address, result)
                    return result
            except Exception as e:
                self.logger.error(f"Google geocoding error: {e}")

        # Fallback to Nominatim
        try:
            result = self._geocode_nominatim(processed_address)
            if result and self._validate_result(result, address_metadata):
                result['validation_score'] = self._calculate_validation_score(
                    result, address_metadata
                )
                self._cache_result(address, result)
                return result
        except Exception as e:
            self.logger.error(f"Nominatim geocoding error: {e}")

        # If both fail, retry with variations
        if retry_count > 0:
            variations = self._generate_address_variations(processed_address, address_metadata)
            for variant in variations:
                try:
                    result = self.geocode(variant, retry_count - 1)
                    if result:
                        return result
                except Exception:
                    continue

        return {
            'latitude': None,
            'longitude': None,
            'confidence': 0.0,
            'source': 'none',
            'address_components': {},
            'validation_score': 0.0,
            'error': 'Geocoding failed for all attempts'
        }

    def _geocode_google(self, address: str) -> Optional[Dict]:
        """Geocode using Google Maps API"""
        if not self.google_api_key:
            return None

        # Rate limiting
        elapsed = time.time() - self.last_google_call
        if elapsed < self.google_delay:
            time.sleep(self.google_delay - elapsed)
        
        try:
            result = self.google_maps.geocode(address)
            self.last_google_call = time.time()
            
            if not result:
                return None
            
            location = result[0]['geometry']['location']
            return {
                'latitude': location['lat'],
                'longitude': location['lng'],
                'confidence': self._calculate_google_confidence(result[0]),
                'source': 'google',
                'address_components': result[0].get('address_components', {}),
                'formatted_address': result[0].get('formatted_address', '')
            }
        except Exception as e:
            self.logger.error(f"Google geocoding error: {e}")
            return None

    def _geocode_nominatim(self, address: str) -> Optional[Dict]:
        """Geocode using Nominatim"""
        # Rate limiting
        elapsed = time.time() - self.last_nominatim_call
        if elapsed < self.nominatim_delay:
            time.sleep(self.nominatim_delay - elapsed)
        
        try:
            result = self.nominatim.geocode(
                address,
                country_codes='in',
                timeout=10
            )
            self.last_nominatim_call = time.time()
            
            if not result:
                return None
            
            return {
                'latitude': result.latitude,
                'longitude': result.longitude,
                'confidence': self._calculate_nominatim_confidence(result),
                'source': 'nominatim',
                'address_components': result.raw.get('address', {}),
                'formatted_address': result.address
            }
        except Exception as e:
            self.logger.error(f"Nominatim geocoding error: {e}")
            return None

    def _validate_result(self, result: Dict, address_metadata: Dict) -> bool:
        """Validate geocoding result"""
        if not result:
            return False
            
        lat = result.get('latitude')
        lon = result.get('longitude')
        
        if lat is None or lon is None:
            return False
            
        # Basic bounds check
        if not self._is_within_india_bounds(lat, lon):
            return False
            
        # ML-based validation
        is_valid, confidence = self.ml_validator.validate(result, address_metadata)
        if not is_valid:
            return False
            
        # If ML validation passes, perform additional checks
        if result['source'] == 'google':
            if result.get('confidence', 0) < 0.6:
                return False
        else:  # Nominatim
            if result.get('confidence', 0) < 0.7:  # Higher threshold for Nominatim
                return False
        
        return True

    def _calculate_validation_score(self, result: Dict, address_metadata: Dict) -> float:
        """Calculate validation score based on multiple factors"""
        score = 0.0
        weights = {
            'district_match': 0.3,
            'state_match': 0.2,
            'pin_match': 0.15,
            'education_keywords': 0.15,
            'bounds_check': 0.2
        }
        
        # Check district match
        if 'district' in address_metadata.get('components', {}):
            result_district = self._extract_district(result)
            if result_district and result_district.lower() == address_metadata['components']['district'].lower():
                score += weights['district_match']
        
        # Check state match
        if 'state' in address_metadata.get('components', {}):
            result_state = self._extract_state(result)
            if result_state and result_state.lower() == address_metadata['components']['state'].lower():
                score += weights['state_match']
        
        # Check PIN code match
        if 'pin' in address_metadata.get('components', {}):
            result_pin = self._extract_pin(result)
            if result_pin and result_pin == address_metadata['components']['pin']:
                score += weights['pin_match']
        
        # Check for educational keywords
        if self._has_education_keywords(result):
            score += weights['education_keywords']
        
        # Check if coordinates are within India bounds
        if self._is_within_india_bounds(result['latitude'], result['longitude']):
            score += weights['bounds_check']
        
        return score

    def _extract_district(self, result: Dict) -> Optional[str]:
        """Extract district from geocoding result"""
        for component in result.get('address_components', []):
            if 'administrative_area_level_2' in component.get('types', []):
                return component['long_name']
        return None

    def _extract_state(self, result: Dict) -> Optional[str]:
        """Extract state from geocoding result"""
        for component in result.get('address_components', []):
            if 'administrative_area_level_1' in component.get('types', []):
                return component['long_name']
        return None

    def _extract_pin(self, result: Dict) -> Optional[str]:
        """Extract PIN code from geocoding result"""
        for component in result.get('address_components', []):
            if 'postal_code' in component.get('types', []):
                return component['long_name']
        return None

    def _has_education_keywords(self, result: Dict) -> bool:
        """Check if result contains educational institution keywords"""
        keywords = {
            'university', 'college', 'institute', 'school', 'campus',
            'vishwavidyalaya', 'mahavidyalaya', 'vidyalaya', 'shikshan',
            'polytechnic', 'academy', 'education'
        }
        
        address = result.get('formatted_address', '').lower()
        types = [t.lower() for t in result.get('types', [])]
        
        # Check in address
        if any(keyword in address for keyword in keywords):
            return True
            
        # Check in place types
        if 'university' in types or 'school' in types:
            return True
            
        # Check in address components
        for component in result.get('address_components', []):
            if any(keyword in component.get('long_name', '').lower() for keyword in keywords):
                return True
        
        return False

    def _is_within_india_bounds(self, lat: float, lon: float) -> bool:
        """Check if coordinates are within India's boundaries"""
        return (self.INDIA_BOUNDS['min_lat'] <= lat <= self.INDIA_BOUNDS['max_lat'] and
                self.INDIA_BOUNDS['min_lon'] <= lon <= self.INDIA_BOUNDS['max_lon'])

    def _calculate_google_confidence(self, result: Dict) -> float:
        """Calculate confidence score for Google result"""
        score = 0.7  # Base score
        
        # Location type boost
        location_type = result.get('geometry', {}).get('location_type', '')
        if location_type == 'ROOFTOP':
            score += 0.2
        elif location_type == 'RANGE_INTERPOLATED':
            score += 0.1
        
        # Address component completeness
        components = result.get('address_components', [])
        if any(c['types'] == ['postal_code'] for c in components):
            score += 0.1
        if any(c['types'] == ['administrative_area_level_2'] for c in components):
            score += 0.1
        
        return min(1.0, score)

    def _calculate_nominatim_confidence(self, result) -> float:
        """Calculate confidence score for Nominatim result"""
        score = 0.6  # Base score (lower than Google)
        
        # Check address completeness
        address = result.raw.get('address', {})
        if 'postcode' in address:
            score += 0.1
        if 'state' in address:
            score += 0.1
        if 'city' in address or 'town' in address:
            score += 0.1
        
        # Check type of location
        if 'amenity' in result.raw:
            score += 0.1
        
        return min(1.0, score)

    def _generate_address_variations(self, address: str, metadata: Dict) -> List[str]:
        """Generate address variations for retry attempts"""
        variations = []
        components = metadata['components']
        
        # Remove landmarks
        if components.get('landmarks'):
            parts = []
            if components.get('district'):
                parts.append(components['district'])
            if components.get('state'):
                parts.append(components['state'])
            if components.get('pin'):
                parts.append(components['pin'])
            variations.append(', '.join(parts))
        
        # Add state if missing
        if not components.get('state') and components.get('district'):
            district_row = self.district_data[
                self.district_data['district'] == components['district']
            ]
            if not district_row.empty:
                state = district_row.iloc[0]['state']
                variations.append(f"{address}, {state}")
        
        return variations
