import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import Optional, Dict, List
import json

class DataProcessor:
    def __init__(self):
        self.state_mapping = {
            'AP': 'Andhra Pradesh',
            'AR': 'Arunachal Pradesh',
            'AS': 'Assam',
            'BR': 'Bihar',
            'CG': 'Chhattisgarh',
            'GA': 'Goa',
            'GJ': 'Gujarat',
            'HR': 'Haryana',
            'HP': 'Himachal Pradesh',
            'JH': 'Jharkhand',
            'KA': 'Karnataka',
            'KL': 'Kerala',
            'MP': 'Madhya Pradesh',
            'MH': 'Maharashtra',
            'MN': 'Manipur',
            'ML': 'Meghalaya',
            'MZ': 'Mizoram',
            'NL': 'Nagaland',
            'OR': 'Odisha',
            'PB': 'Punjab',
            'RJ': 'Rajasthan',
            'SK': 'Sikkim',
            'TN': 'Tamil Nadu',
            'TS': 'Telangana',
            'TR': 'Tripura',
            'UK': 'Uttarakhand',
            'UP': 'Uttar Pradesh',
            'WB': 'West Bengal',
            'AN': 'Andaman and Nicobar Islands',
            'CH': 'Chandigarh',
            'DN': 'Dadra and Nagar Haveli',
            'DD': 'Daman and Diu',
            'DL': 'Delhi',
            'JK': 'Jammu and Kashmir',
            'LA': 'Ladakh',
            'LD': 'Lakshadweep',
            'PY': 'Puducherry'
        }
        
        # Load district mapping
        self.district_mapping = self._load_district_mapping()
        
        # Common address patterns to clean
        self.address_patterns = {
            r'\s+': ' ',  # Multiple spaces
            r',\s*,': ',',  # Multiple commas
            r'\.+': '.',  # Multiple periods
            r'\s+,': ',',  # Space before comma
            r',(?!\s)': ', ',  # No space after comma
            r'\bDist\.?\s*': 'District ',  # Standardize District
            r'\bP\.?O\.?\s*': 'Post Office ',  # Standardize P.O.
            r'\bP\.?B\.?\s*': 'Post Box ',  # Standardize P.B.
            r'\bTeh\.?\s*': 'Tehsil ',  # Standardize Tehsil
            r'\bTal\.?\s*': 'Taluka ',  # Standardize Taluka
            r'Pin\s*-?\s*': 'PIN: ',  # Standardize PIN
            r'\bVill\.?\s*': 'Village ',  # Standardize Village
        }
        
        # Load landmark data
        self.landmarks = self._load_landmarks()

    def _load_district_mapping(self) -> Dict[str, List[str]]:
        """Load district mapping for each state"""
        # This would ideally load from a JSON file, but for now returning a sample
        return {
            'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Thane', 'Nashik'],
            'Karnataka': ['Bangalore', 'Mysore', 'Hubli', 'Mangalore', 'Belgaum'],
            # Add more states and districts
        }

    def _load_landmarks(self) -> Dict[str, Dict[str, tuple]]:
        """Load landmark data with known coordinates"""
        # This would ideally load from a JSON file
        return {
            'Mumbai': {
                'Gateway of India': (18.9217, 72.8347),
                'CST Station': (18.9398, 72.8355),
            },
            'Delhi': {
                'India Gate': (28.6129, 77.2295),
                'Red Fort': (28.6562, 77.2410),
            },
            # Add more cities and landmarks
        }

    def extract_pin_code(self, text: str) -> Optional[str]:
        """Extract PIN code from text using various patterns"""
        if pd.isna(text):
            return None
            
        patterns = [
            r'(?P<pin>\d{6})',  # Standalone 6 digits
            r'Pin\s*-?\s*(?P<pin>\d{6})',  # Pin- format
            r'Pin\s*Code\s*:?\s*(?P<pin>\d{6})',  # Pin Code: format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(text))
            if match:
                return match.group('pin')
        return None

    def clean_postal_code(self, postal_code: Optional[str]) -> Optional[str]:
        """Clean and validate postal codes"""
        if pd.isna(postal_code):
            return None
        
        # Convert to string and remove non-digits
        postal_str = str(postal_code)
        postal_digits = re.sub(r'\D', '', postal_str)
        
        # Validate 6-digit format
        if len(postal_digits) == 6:
            return postal_digits
        elif len(postal_digits) > 6:
            return postal_digits[:6]
        else:
            return None

    def extract_district(self, address: str, state: str) -> Optional[str]:
        """Extract district from address"""
        if pd.isna(address) or pd.isna(state):
            return None
            
        # Try to find district explicitly mentioned
        district_pattern = r'(?:District|Dist\.?|Dt\.?)\s*[-:]?\s*([^,\.]+)'
        match = re.search(district_pattern, address, re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
        # Check against known districts for the state
        if state in self.district_mapping:
            for district in self.district_mapping[state]:
                if district.lower() in address.lower():
                    return district
                    
        return None

    def clean_address(self, row: pd.Series) -> str:
        """Clean and enhance addresses with improved logic"""
        address = row.get('address', '')
        district = row.get('District')
        state = row.get('state')
        
        if pd.isna(address):
            return None
            
        address = str(address).strip()
        
        # Apply all cleaning patterns
        for pattern, replacement in self.address_patterns.items():
            address = re.sub(pattern, replacement, address)
        
        # Extract and validate PIN code
        pin_code = self.extract_pin_code(address)
        if pin_code:
            # Remove PIN code from address if it exists
            address = re.sub(r'\b' + pin_code + r'\b', '', address)
            # Add PIN code in standard format at the end
            address = f"{address.strip()}, PIN: {pin_code}"
        
        # Add district if missing and available
        extracted_district = self.extract_district(address, state)
        if extracted_district and extracted_district.lower() not in address.lower():
            address = f"{address}, District {extracted_district}"
        elif district and str(district).strip() and str(district).strip().lower() not in address.lower():
            address = f"{address}, District {district}"
        
        # Add state if missing and available
        if state and str(state).strip() and str(state).strip().lower() not in address.lower():
            address = f"{address}, {state}"
        
        # Final cleanup
        address = re.sub(r'\s+', ' ', address)  # Remove multiple spaces
        address = re.sub(r',\s*,', ',', address)  # Remove consecutive commas
        address = re.sub(r'^\s*,\s*|\s*,\s*$', '', address)  # Remove leading/trailing commas
        
        return address.strip()

    def normalize_state_name(self, state: Optional[str]) -> Optional[str]:
        """Normalize state names with improved logic"""
        if pd.isna(state):
            return None
        
        state = str(state).strip().title()
        
        # Direct mapping for common variations
        state_variations = {
            'Delhi': 'Delhi',
            'New Delhi': 'Delhi',
            'Ncr': 'Delhi',
            'Tamilnadu': 'Tamil Nadu',
            'Tamilnadhu': 'Tamil Nadu',
            'Up': 'Uttar Pradesh',
            'Ap': 'Andhra Pradesh',
            'Mp': 'Madhya Pradesh',
            'Uk': 'Uttarakhand',
            'Maharashtra State': 'Maharashtra',
            'Maharastra': 'Maharashtra',
            'Orissa': 'Odisha',
            'Telegana': 'Telangana',
            'Telengana': 'Telangana',
            'Andhrapradesh': 'Andhra Pradesh',
            'Andra Pradesh': 'Andhra Pradesh',
            'Pondicherry': 'Puducherry',
            'Pondy': 'Puducherry',
            'Calcutta': 'West Bengal',
            'Kolkata': 'West Bengal',
            'Bombay': 'Maharashtra',
            'Madras': 'Tamil Nadu',
            'Bangalore': 'Karnataka',
            'Bengaluru': 'Karnataka',
        }
        
        # Check direct variations first
        if state in state_variations:
            return state_variations[state]
            
        # Check state codes
        if state.upper() in self.state_mapping:
            return self.state_mapping[state.upper()]
            
        return state

    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validate if coordinates are within India's bounding box"""
        INDIA_BOUNDS = {
            'min_lat': 6.5546079,
            'max_lat': 35.6745457,
            'min_lon': 68.1113787,
            'max_lon': 97.395561
        }
        
        return (INDIA_BOUNDS['min_lat'] <= lat <= INDIA_BOUNDS['max_lat'] and
                INDIA_BOUNDS['min_lon'] <= lon <= INDIA_BOUNDS['max_lon'])

    def process_data(self):
        """Process and clean the college data with enhanced validation"""
        input_file = 'docs/cleaned_colleges.csv'
        
        # Check if input file exists
        if not Path(input_file).exists():
            print(f"Error: Input file {input_file} not found")
            return
            
        # Read the cleaned data
        try:
            df = pd.read_csv(input_file)
        except Exception as e:
            print(f"Error reading input file: {e}")
            return
            
        # Verify required columns exist
        required_columns = ['address', 'postal_code', 'state']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            return
        
        print("Starting enhanced data processing...")
        
        # Clean postal codes
        print("Cleaning postal codes...")
        df['postal_code'] = df['postal_code'].apply(self.clean_postal_code)
        
        # Extract PIN codes from addresses where missing
        mask = df['postal_code'].isna()
        df.loc[mask, 'postal_code'] = df.loc[mask, 'address'].apply(self.extract_pin_code)
        
        # Clean addresses
        print("Enhancing addresses...")
        df['address'] = df.apply(self.clean_address, axis=1)
        
        # Normalize state names
        print("Normalizing state names...")
        df['state'] = df['state'].apply(self.normalize_state_name)
        
        # Add geolocation columns
        if 'latitude' not in df.columns:
            df['latitude'] = None
        if 'longitude' not in df.columns:
            df['longitude'] = None
        
        # Add data quality indicators
        df['address_quality'] = df.apply(self._calculate_address_quality, axis=1)
        df['geocoding_priority'] = df.apply(self._calculate_geocoding_priority, axis=1)
        
        # Save the enhanced data
        output_file = 'docs/enhanced_colleges.csv'
        df.to_csv(output_file, index=False)
        print(f"Enhanced data saved to {output_file}")
        
        # Generate quality report
        self._generate_quality_report(df)
        
        return df

    def _calculate_address_quality(self, row: pd.Series) -> int:
        """Calculate address quality score (0-100)"""
        score = 0
        
        # Basic completeness
        if not pd.isna(row['address']):
            score += 20
            
            # Check for key components
            if 'District' in str(row['address']):
                score += 20
            if str(row['state']) in str(row['address']):
                score += 20
            if self.extract_pin_code(str(row['address'])):
                score += 20
                
            # Length check
            if len(str(row['address'])) >= 30:
                score += 20
                
        return score

    def _calculate_geocoding_priority(self, row: pd.Series) -> int:
        """Calculate geocoding priority (1-5, 1 being highest)"""
        quality = row['address_quality']
        
        if quality >= 90:
            return 1
        elif quality >= 70:
            return 2
        elif quality >= 50:
            return 3
        elif quality >= 30:
            return 4
        else:
            return 5

    def _generate_quality_report(self, df: pd.DataFrame) -> None:
        """Generate detailed quality report"""
        report = {
            'total_records': int(len(df)),
            'complete_addresses': int(df['address'].notna().sum()),
            'complete_postal_codes': int(df['postal_code'].notna().sum()),
            'unique_states': int(df['state'].nunique()),
            'quality_distribution': {
                str(score): int(count) 
                for score, count in df['address_quality'].value_counts().items()
            },
            'priority_distribution': {
                str(priority): int(count)
                for priority, count in df['geocoding_priority'].value_counts().items()
            }
        }
        
        print("\nData Quality Report:")
        print("-" * 50)
        print(f"Total records: {report['total_records']}")
        print(f"Complete addresses: {report['complete_addresses']}")
        print(f"Complete postal codes: {report['complete_postal_codes']}")
        print(f"Unique states: {report['unique_states']}")
        print("\nAddress Quality Distribution:")
        for score, count in report['quality_distribution'].items():
            print(f"Score {score}: {count} records")
        print("\nGeocoding Priority Distribution:")
        for priority, count in report['priority_distribution'].items():
            print(f"Priority {priority}: {count} records")
        
        # Save report
        with open('docs/data_quality_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print("\nDetailed report saved to docs/data_quality_report.json")

if __name__ == "__main__":
    processor = DataProcessor()
    processor.process_data()
