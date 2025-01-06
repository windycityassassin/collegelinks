"""
Specialized parser for Indian addresses with high accuracy validation
"""
import logging
import re
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndianAddressParser:
    """Parser specialized for Indian addresses with high accuracy validation"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize parser with reference data"""
        self.data_dir = Path(data_dir)
        self._load_reference_data()
        
    def _load_reference_data(self):
        """Load or download reference data"""
        # Create directories
        self.ref_dir = self.data_dir / "reference"
        self.ref_dir.mkdir(exist_ok=True)
        
        # Load or download PIN codes
        self.pin_codes = self._load_pin_codes()
        
        # Load or download districts
        self.districts = self._load_districts()
        
        # Load or download states
        self.states = self._load_states()
        
        logger.info(f"Loaded {len(self.pin_codes)} PIN codes, {len(self.districts)} districts")
        
    def _load_pin_codes(self) -> Dict[str, Dict]:
        """Load complete database of Indian PIN codes"""
        pin_file = self.ref_dir / "pin_codes.json"
        
        if not pin_file.exists():
            # TODO: Download from India Post API or other source
            # For now, use existing data
            pin_codes = {}
            pin_df = pd.read_csv(self.data_dir / "raw" / "india_pin_codes.csv")
            for _, row in pin_df.iterrows():
                pin_codes[str(row['pincode'])] = {
                    'district': row['district'],
                    'state': row['state']
                }
            
            # Save for future use
            with open(pin_file, 'w') as f:
                json.dump(pin_codes, f)
        else:
            with open(pin_file) as f:
                pin_codes = json.load(f)
                
        return pin_codes
    
    def _load_districts(self) -> Dict[str, List[str]]:
        """Load complete database of Indian districts"""
        district_file = self.ref_dir / "districts.json"
        
        if not district_file.exists():
            # TODO: Download from official source
            # For now, use existing data
            districts = {}
            district_df = pd.read_csv(self.data_dir / "raw" / "india_districts.csv")
            for _, row in district_df.iterrows():
                state = row['state']
                if state not in districts:
                    districts[state] = []
                districts[state].append(row['district'])
            
            # Save for future use
            with open(district_file, 'w') as f:
                json.dump(districts, f)
        else:
            with open(district_file) as f:
                districts = json.load(f)
                
        return districts
    
    def _load_states(self) -> Dict[str, Dict]:
        """Load Indian states and their variations"""
        return {
            'ANDHRA PRADESH': {'ap', 'andhra', 'andhrapradesh'},
            'ARUNACHAL PRADESH': {'arunachal'},
            'ASSAM': {'as'},
            'BIHAR': {'br'},
            'CHHATTISGARH': {'cg', 'chattisgarh'},
            'GOA': {'ga'},
            'GUJARAT': {'gj'},
            'HARYANA': {'hr'},
            'HIMACHAL PRADESH': {'hp'},
            'JHARKHAND': {'jh'},
            'KARNATAKA': {'ka'},
            'KERALA': {'kl'},
            'MADHYA PRADESH': {'mp'},
            'MAHARASHTRA': {'mh'},
            'MANIPUR': {'mn'},
            'MEGHALAYA': {'ml'},
            'MIZORAM': {'mz'},
            'NAGALAND': {'nl'},
            'ODISHA': {'od', 'orissa'},
            'PUNJAB': {'pb'},
            'RAJASTHAN': {'rj'},
            'SIKKIM': {'sk'},
            'TAMIL NADU': {'tn', 'tamilnadu'},
            'TELANGANA': {'ts', 'tg'},
            'TRIPURA': {'tr'},
            'UTTAR PRADESH': {'up'},
            'UTTARAKHAND': {'uk', 'uttaranchal'},
            'WEST BENGAL': {'wb'},
            'DELHI': {'dl', 'new delhi'},
            'PUDUCHERRY': {'py', 'pondicherry'},
        }
    
    def parse_address(self, address: str, state: str = None) -> Dict[str, str]:
        """Parse Indian address with high accuracy"""
        if not isinstance(address, str):
            return {}
            
        components = {
            'street': '',
            'locality': '',
            'landmark': '',
            'pin_code': '',
            'district': '',
            'state': state or '',
            'confidence': 0.0,
            'raw': address
        }
        
        # Clean address
        address = self._clean_address(address)
        
        # Extract PIN code
        pin_code = self._extract_pin_code(address)
        if pin_code:
            components['pin_code'] = pin_code
            components['confidence'] += 0.3
            
            # Get district and state from PIN code
            if pin_code in self.pin_codes:
                pin_data = self.pin_codes[pin_code]
                if not components['district']:
                    components['district'] = pin_data['district']
                if not components['state']:
                    components['state'] = pin_data['state']
                components['confidence'] += 0.2
        
        # Extract district
        district = self._extract_district(address, components['state'])
        if district:
            components['district'] = district
            components['confidence'] += 0.3
        
        # Parse address parts
        parts = self._split_address(address)
        
        # Extract street and locality
        if parts:
            components['street'] = parts[0]
            if len(parts) > 1:
                components['locality'] = parts[1]
            
            components['confidence'] += 0.2
        
        return components
    
    def _clean_address(self, address: str) -> str:
        """Clean and standardize address string"""
        # Remove extra whitespace
        address = ' '.join(address.split())
        
        # Standardize separators
        address = re.sub(r'\s*[,\-]\s*', ', ', address)
        
        return address
    
    def _extract_pin_code(self, address: str) -> Optional[str]:
        """Extract and validate 6-digit PIN code"""
        # Look for 6-digit numbers
        pin_matches = re.findall(r'\b(\d{6})\b', address)
        
        # Validate against known PIN codes
        for pin in pin_matches:
            if pin in self.pin_codes:
                return pin
                
        return None
    
    def _extract_district(self, address: str, state: str = None) -> Optional[str]:
        """Extract and validate district name"""
        # Clean and split address
        parts = [p.strip().upper() for p in re.split(r'[,\-]', address)]
        
        # If state is provided, look in that state's districts
        if state and state.upper() in self.districts:
            state_districts = self.districts[state.upper()]
            for part in parts:
                if part in state_districts:
                    return part
        
        # Look in all districts
        for state_districts in self.districts.values():
            for part in parts:
                if part in state_districts:
                    return part
        
        return None
    
    def _split_address(self, address: str) -> List[str]:
        """Split address into meaningful parts"""
        # Remove PIN code
        address = re.sub(r'\b\d{6}\b', '', address)
        
        # Split by common delimiters
        parts = [p.strip() for p in re.split(r'[,\-]', address)]
        
        # Remove empty parts
        parts = [p for p in parts if p]
        
        return parts

def main():
    """Test the address parser"""
    parser = IndianAddressParser()
    
    # Test addresses
    test_addresses = [
        "123 MG Road, Bangalore - 560001, Karnataka",
        "Sector 15, Gurgaon, Haryana - 122001",
        "Near City Mall, Pune 411001, Maharashtra"
    ]
    
    for addr in test_addresses:
        result = parser.parse_address(addr)
        print(f"\nAddress: {addr}")
        print("Parsed components:")
        for k, v in result.items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
