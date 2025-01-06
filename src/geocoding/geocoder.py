import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple, List
import time
import json
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import logging
from pathlib import Path
import os
from dotenv import load_dotenv

class CollegeGeocoder:
    def __init__(self, google_api_key: Optional[str] = None):
        """Initialize the geocoder with API keys and configurations"""
        self.google_api_key = google_api_key
        self.nominatim = Nominatim(user_agent="collegelinks_geocoder")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('geocoding.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # India boundaries for validation
        self.INDIA_BOUNDS = {
            'min_lat': 6.5546079,
            'max_lat': 35.6745457,
            'min_lon': 68.1113787,
            'max_lon': 97.395561
        }
        
        # Rate limiting parameters
        self.google_delay = 0.1  # 100ms between requests
        self.nominatim_delay = 1.0  # 1s between requests
        self.last_google_call = 0
        self.last_nominatim_call = 0

    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """Check if coordinates are within India's boundaries"""
        return (self.INDIA_BOUNDS['min_lat'] <= lat <= self.INDIA_BOUNDS['max_lat'] and
                self.INDIA_BOUNDS['min_lon'] <= lon <= self.INDIA_BOUNDS['max_lon'])

    def geocode_google(self, address: str) -> Optional[Dict]:
        """Geocode using Google Maps API"""
        if not self.google_api_key:
            return None
            
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_google_call
        if time_since_last < self.google_delay:
            time.sleep(self.google_delay - time_since_last)
        
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": address,
                "key": self.google_api_key,
                "region": "in"  # Bias results to India
            }
            
            response = requests.get(url, params=params)
            self.last_google_call = time.time()
            
            if response.status_code == 200:
                result = response.json()
                if result["status"] == "OK":
                    location = result["results"][0]["geometry"]["location"]
                    confidence = self._calculate_google_confidence(result["results"][0])
                    return {
                        "lat": location["lat"],
                        "lon": location["lng"],
                        "confidence": confidence,
                        "source": "google"
                    }
            return None
        except Exception as e:
            self.logger.error(f"Google geocoding error for {address}: {str(e)}")
            return None

    def geocode_nominatim(self, address: str) -> Optional[Dict]:
        """Geocode using Nominatim/OpenStreetMap"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_nominatim_call
        if time_since_last < self.nominatim_delay:
            time.sleep(self.nominatim_delay - time_since_last)
            
        try:
            location = self.nominatim.geocode(
                address,
                country_codes="in",
                timeout=10
            )
            self.last_nominatim_call = time.time()
            
            if location:
                return {
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "confidence": self._calculate_nominatim_confidence(location),
                    "source": "nominatim"
                }
            return None
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            self.logger.error(f"Nominatim geocoding error for {address}: {str(e)}")
            return None

    def _calculate_google_confidence(self, result: Dict) -> float:
        """Calculate confidence score for Google geocoding result"""
        confidence = 0.0
        
        # Check location type
        location_type = result.get("geometry", {}).get("location_type", "")
        if location_type == "ROOFTOP":
            confidence = 1.0
        elif location_type == "RANGE_INTERPOLATED":
            confidence = 0.9
        elif location_type == "GEOMETRIC_CENTER":
            confidence = 0.8
        elif location_type == "APPROXIMATE":
            confidence = 0.6
            
        # Adjust based on result types
        types = result.get("types", [])
        if "street_address" in types:
            confidence = min(1.0, confidence + 0.1)
        elif "route" in types:
            confidence = min(1.0, confidence + 0.05)
            
        return confidence

    def _calculate_nominatim_confidence(self, location) -> float:
        """Calculate confidence score for Nominatim result"""
        confidence = 0.7  # Base confidence for Nominatim
        
        # Adjust based on address type
        if hasattr(location, "raw"):
            place_type = location.raw.get("type", "")
            if place_type in ["university", "college"]:
                confidence += 0.2
            elif place_type in ["education", "school"]:
                confidence += 0.1
                
        return min(1.0, confidence)

    def geocode_address(self, address: str, state: str) -> Optional[Dict]:
        """Geocode an address using available services"""
        # Prepare full address with state
        full_address = f"{address}, {state}, India"
        
        # Try Google Maps first
        result = self.geocode_google(full_address)
        if result and self.validate_coordinates(result["lat"], result["lon"]):
            return result
            
        # Fallback to Nominatim
        result = self.geocode_nominatim(full_address)
        if result and self.validate_coordinates(result["lat"], result["lon"]):
            return result
            
        return None

    def process_batch(self, df: pd.DataFrame, start_idx: int, batch_size: int) -> pd.DataFrame:
        """Process a batch of addresses"""
        end_idx = min(start_idx + batch_size, len(df))
        batch = df.iloc[start_idx:end_idx].copy()
        
        for idx, row in batch.iterrows():
            self.logger.info(f"Processing {idx + 1}/{end_idx} - {row['name']}")
            
            result = self.geocode_address(row['address'], row['state'])
            if result:
                batch.at[idx, 'latitude'] = result['lat']
                batch.at[idx, 'longitude'] = result['lon']
                batch.at[idx, 'geocoding_confidence'] = result['confidence']
                batch.at[idx, 'geocoding_source'] = result['source']
            else:
                self.logger.warning(f"Failed to geocode: {row['name']} - {row['address']}")
                
        return batch

    def geocode_colleges(self, input_file: str, batch_size: int = 50):
        """Main function to geocode college addresses"""
        # Check if input file exists
        if not Path(input_file).exists():
            self.logger.error(f"Input file not found: {input_file}")
            return
            
        try:
            # Read input data
            df = pd.read_csv(input_file)
            self.logger.info(f"Loaded {len(df)} records from {input_file}")
            
            # Sort by geocoding priority
            df = df.sort_values('geocoding_priority')
            
            # Initialize output columns
            df['latitude'] = None
            df['longitude'] = None
            df['geocoding_confidence'] = None
            df['geocoding_source'] = None
            
            # Process in batches
            for start_idx in range(0, len(df), batch_size):
                batch_df = self.process_batch(df, start_idx, batch_size)
                
                # Update main dataframe
                df.iloc[start_idx:start_idx + len(batch_df)] = batch_df
                
                # Save intermediate results
                df.to_csv('docs/geocoded_colleges.csv', index=False)
                self.logger.info(f"Processed and saved batch: {start_idx + 1} to {start_idx + len(batch_df)}")
            
            # Generate final report
            self._generate_geocoding_report(df)
            
        except Exception as e:
            self.logger.error(f"Error processing file: {str(e)}")

    def _generate_geocoding_report(self, df: pd.DataFrame):
        """Generate report of geocoding results"""
        report = {
            'total_records': len(df),
            'geocoded_records': df['latitude'].notna().sum(),
            'failed_records': df['latitude'].isna().sum(),
            'source_distribution': df['geocoding_source'].value_counts().to_dict(),
            'confidence_stats': {
                'mean': float(df['geocoding_confidence'].mean()),
                'median': float(df['geocoding_confidence'].median()),
                'min': float(df['geocoding_confidence'].min()),
                'max': float(df['geocoding_confidence'].max())
            }
        }
        
        # Save report
        with open('docs/geocoding_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Log summary
        self.logger.info("\nGeocoding Report:")
        self.logger.info("-" * 50)
        self.logger.info(f"Total records: {report['total_records']}")
        self.logger.info(f"Successfully geocoded: {report['geocoded_records']}")
        self.logger.info(f"Failed to geocode: {report['failed_records']}")
        self.logger.info("\nSource Distribution:")
        for source, count in report['source_distribution'].items():
            self.logger.info(f"{source}: {count} records")
        self.logger.info("\nConfidence Statistics:")
        for stat, value in report['confidence_stats'].items():
            self.logger.info(f"{stat}: {value:.2f}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Initialize geocoder with Google Maps API key from environment
    geocoder = CollegeGeocoder(google_api_key=os.getenv('GOOGLE_GEOCODING_API_KEY'))
    
    # Start geocoding
    input_file = "docs/enhanced_colleges.csv"
    geocoder.geocode_colleges(input_file)
