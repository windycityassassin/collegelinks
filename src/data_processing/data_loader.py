"""
Data loader for processing UGC college data
"""
import logging
import os
import pandas as pd
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from data_processing.indian_address_parser import IndianAddressParser
from schemas.college_profile import CollegeProfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CollegeDataLoader:
    """Loads and processes UGC college data and supporting datasets"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize data loader with data directory path"""
        self.data_dir = Path(data_dir)
        self.raw_dir = os.path.join(data_dir, "raw")
        self.interim_dir = os.path.join(data_dir, "interim")
        self.processed_dir = os.path.join(data_dir, "processed")
        self.address_parser = IndianAddressParser(data_dir)
        
        # Initialize geocoder
        self.geolocator = Nominatim(user_agent="collegelinks")
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1)
        
        # Create directories if they don't exist
        for dir_path in [self.raw_dir, self.interim_dir, self.processed_dir]:
            os.makedirs(dir_path, exist_ok=True)
            
        # Load supporting datasets
        self._load_reference_data()
    
    def _load_reference_data(self):
        """Load supporting datasets like districts and PIN codes"""
        # Load districts
        districts_path = os.path.join(self.raw_dir, "india_districts.csv")
        if os.path.exists(districts_path):
            districts_df = pd.read_csv(districts_path)
            self.districts_set = set(districts_df['district'].str.upper())
            logger.info(f"Loaded {len(self.districts_set)} districts")
        else:
            self.districts_set = set()
            logger.warning("Districts file not found")
            
        # Load PIN codes
        pin_codes_path = os.path.join(self.raw_dir, "india_pin_codes.csv")
        if os.path.exists(pin_codes_path):
            pin_codes_df = pd.read_csv(pin_codes_path)
            self.pin_codes_set = set(pin_codes_df['pincode'].astype(str))
            logger.info(f"Loaded {len(self.pin_codes_set)} PIN codes")
        else:
            self.pin_codes_set = set()
            logger.warning("PIN codes file not found")
    
    def load_colleges(self) -> pd.DataFrame:
        """Load and combine college datasets"""
        datasets = {
            'colleges': "Colleges.csv",
            'central_universities': "Central Uni.csv",
            'state_universities': "State Uni.csv",
            'private_universities': "Private Uni.csv",
            'deemed_universities': "Deemed to be Uni.csv"
        }
        
        combined_df = pd.DataFrame()
        
        for name, filename in datasets.items():
            path = os.path.join(self.raw_dir, filename)
            if os.path.exists(path):
                df = pd.read_csv(path)
                df['source'] = name
                combined_df = pd.concat([combined_df, df], ignore_index=True)
                logger.info(f"Loaded {len(df)} records from {filename}")
            else:
                logger.warning(f"File not found: {filename}")
        
        logger.info(f"Total records loaded: {len(combined_df)}")
        return combined_df
    
    def _process_address(self, row: pd.Series) -> Dict[str, Any]:
        """Process and validate address information"""
        # Extract address components
        address = str(row.get('College address', ''))
        state = str(row.get('State', ''))
        
        # Parse address using specialized Indian address parser
        components = self.address_parser.parse_address(address, state)
        
        # Calculate completeness score
        score = components['confidence']
        if components['pin_code']:
            score += 0.3
        if components['district']:
            score += 0.3
        if components['street'] and components['locality']:
            score += 0.4
            
        return {
            'address': components['raw'],
            'street': components['street'],
            'locality': components['locality'],
            'landmark': components['landmark'],
            'district': components['district'],
            'state': components['state'] or state,
            'pin_code': components['pin_code'],
            'completeness_score': min(1.0, score)  # Cap at 1.0
        }
    
    def _geocode_address(self, row: pd.Series) -> Dict[str, Any]:
        """Geocode address to get latitude and longitude"""
        # Construct address string
        address_parts = []
        if row['street']:
            address_parts.append(row['street'])
        if row['locality']:
            address_parts.append(row['locality'])
        if row['final_district']:
            address_parts.append(row['final_district'])
        if row['State']:
            address_parts.append(row['State'])
        address_parts.append('India')
        
        address = ", ".join(filter(None, address_parts))
        
        try:
            location = self.geocode(address)
            if location:
                return {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'geocoded_address': location.address
                }
        except Exception as e:
            logger.warning(f"Geocoding failed for {address}: {str(e)}")
        
        return {
            'latitude': None,
            'longitude': None,
            'geocoded_address': None
        }

    def _create_college_profile(self, row: pd.Series) -> Dict[str, Any]:
        """Create college profile from row data"""
        # Extract address components
        address_info = self._process_address(row)
        
        # Helper function to safely convert to int
        def safe_int_convert(value, default=0):
            try:
                if pd.isna(value) or value == '':
                    return default
                return int(value)
            except (ValueError, TypeError):
                return default
        
        # Create base profile
        profile = {
            "id": re.sub(r'[^a-zA-Z0-9_]', '_', str(row.get('Name of the college', ''))).upper(),
            "name": str(row.get('Name of the college', '')),
            "type": str(row.get('type', 'Unknown')),
            "established": safe_int_convert(row.get('Year of Estb.')),
            "address": address_info['address'],
            "city": address_info.get('locality', ''),
            "state": address_info.get('state', ''),
            "accreditation": {
                "naac_grade": row.get('naac_grade', None),
                "nirf_rank": safe_int_convert(row.get('nirf_rank'), None)
            },
            "contact": {
                "website": str(row.get('website', 'https://example.com')),
                "email": str(row.get('email', 'info@example.com')),
                "phone": str(row.get('phone', '000-000-0000'))
            },
            "courses": {},
            "facilities": {
                "library": {
                    "name": "Main Library",
                    "books": 50000,
                    "digital_resources": True,
                    "study_spaces": True
                },
                "hostel": {
                    "boys": True,
                    "girls": True,
                    "total_capacity": 1000
                },
                "sports": ["Cricket", "Football", "Basketball"],
                "labs": ["Computer Lab", "Physics Lab", "Chemistry Lab"]
            },
            "admissions": {
                "entrance_exams": ["JEE", "NEET"],
                "admission_process": "Online Application",
                "important_dates": {
                    "application_start": "2024-01-01",
                    "application_end": "2024-06-30",
                    "academic_year_start": "2024-07-01"
                }
            }
        }
        
        # Add courses
        if 'courses' in row and isinstance(row['courses'], str):
            courses = []
            for course in row['courses'].split(','):
                course = course.strip()
                if course:
                    courses.append({
                        "name": course,
                        "duration": "4 years",
                        "seats": 60,
                        "fee_per_semester": 50000
                    })
            profile["courses"]["B.Tech"] = courses
        
        return profile

    def process_college_data(self) -> None:
        """Process and clean college data"""
        # Load data
        df = self.load_colleges()
        
        # Basic cleaning
        df = df.fillna("")
        
        # Process colleges
        logger.info("Processing colleges...")
        colleges = []
        for _, row in df.iterrows():
            try:
                college = self._create_college_profile(row)
                colleges.append(college)
            except Exception as e:
                logger.warning(f"Failed to process college {row.get('Name of the college', 'Unknown')}: {str(e)}")
        
        # Save processed data
        output_path = os.path.join(self.processed_dir, "college_profiles.json")
        with open(output_path, 'w') as f:
            json.dump({"colleges": colleges}, f, indent=2)
        logger.info(f"Saved {len(colleges)} college profiles to {output_path}")
        
        # Print statistics
        total = len(colleges)
        logger.info(f"\nData Processing Statistics:")
        logger.info(f"Total colleges processed: {total}")

def main():
    """Main function to process all data"""
    loader = CollegeDataLoader()
    loader.process_college_data()

if __name__ == "__main__":
    main()
