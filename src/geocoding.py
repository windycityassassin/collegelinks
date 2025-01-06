"""
Geocoding module for processing university and college locations.
"""
import os
import json
import time
import pandas as pd
from typing import Dict, Optional, List
from dataclasses import dataclass
import requests
from dotenv import load_dotenv

@dataclass
class Location:
    """Class to store location data."""
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence: float = 0.0
    source: str = ''
    error: str = ''

class Geocoder:
    """A class to geocode locations using Google Geocoding API."""
    
    def __init__(self):
        """Initialize the geocoder."""
        # Load environment variables
        load_dotenv()
        
        # Get API key
        self.api_key = os.getenv('GOOGLE_GEOCODING_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_GEOCODING_API_KEY not found in environment")
        
        # Initialize cache
        self.cache_file = os.path.join('data', 'processed', 'geocoding_cache.json')
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load geocoding cache from file."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save geocoding cache to file."""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def geocode(self, name: str, address: str, state: str) -> Location:
        """
        Geocode a location using Google Geocoding API.
        
        Args:
            name: Name of the institution
            address: Address of the institution
            state: State where the institution is located
            
        Returns:
            Location object with geocoding results
        """
        # Check cache first
        cache_key = f"{name}|{address}|{state}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return Location(
                name=name,
                address=address,
                latitude=cached.get('latitude'),
                longitude=cached.get('longitude'),
                confidence=cached.get('confidence', 0.0),
                source=cached.get('source', ''),
                error=cached.get('error', '')
            )
        
        try:
            # Construct search query
            search_query = f"{name}, {state}, India"
            geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
            
            # Make API request
            params = {
                'address': search_query,
                'key': self.api_key.strip()
            }
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': '*/*'
            }
            
            response = requests.get(geocoding_url, params=params, headers=headers)
            result = response.json()
            
            if result.get('status') == 'OK' and result.get('results'):
                place = result['results'][0]
                location = place['geometry']['location']
                
                # Calculate confidence based on types
                types = place.get('types', [])
                confidence = 0.5
                if 'university' in types:
                    confidence = 0.9
                elif 'school' in types or 'establishment' in types:
                    confidence = 0.7
                
                # Create location object
                loc = Location(
                    name=name,
                    address=place['formatted_address'],
                    latitude=location['lat'],
                    longitude=location['lng'],
                    confidence=confidence,
                    source='Google Geocoding API'
                )
            else:
                error_msg = result.get('error_message', result.get('status', 'Unknown error'))
                loc = Location(
                    name=name,
                    address=address,
                    error=f"Geocoding failed: {error_msg}"
                )
            
            # Cache the result
            self.cache[cache_key] = {
                'latitude': loc.latitude,
                'longitude': loc.longitude,
                'confidence': loc.confidence,
                'source': loc.source,
                'error': loc.error
            }
            self._save_cache()
            
            # Respect API rate limits
            time.sleep(0.1)  # Max 10 requests per second
            
            return loc
            
        except Exception as e:
            return Location(
                name=name,
                address=address,
                error=f"Error: {str(e)}"
            )

def process_universities(input_file: str, output_file: str) -> List[Location]:
    """
    Process universities from a CSV file and geocode their locations.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        
    Returns:
        List of Location objects with geocoding results
    """
    # Read input CSV
    df = pd.read_csv(input_file)
    
    # Initialize geocoder
    geocoder = Geocoder()
    
    results = []
    total = len(df)
    
    print(f"\nProcessing {total} institutions from {input_file}")
    
    for idx, row in df.iterrows():
        name = row['Name of the University']
        state = row['State']
        address = row.get('Address', '')  # Some files might not have address
        
        print(f"\nProcessing {idx + 1}/{total}: {name}")
        result = geocoder.geocode(name, address, state)
        results.append(result)
        
        # Show progress
        if (idx + 1) % 10 == 0:
            print(f"Processed {idx + 1}/{total} institutions")
    
    # Convert results to DataFrame
    results_df = pd.DataFrame([
        {
            'name': r.name,
            'address': r.address,
            'latitude': r.latitude,
            'longitude': r.longitude,
            'confidence': r.confidence,
            'source': r.source,
            'error': r.error
        }
        for r in results
    ])
    
    # Save to CSV
    results_df.to_csv(output_file, index=False)
    print(f"\nResults saved to {output_file}")
    
    return results

if __name__ == '__main__':
    # Example usage
    input_file = os.path.join('docs', 'Central Uni.csv')
    output_file = os.path.join('data', 'processed', 'central_universities_geocoded.csv')
    process_universities(input_file, output_file)
