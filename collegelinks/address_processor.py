import re
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import logging
import csv
from indic_transliteration import sanscript
from indic_transliteration.sanscript import SchemeMap, SCHEMES, transliterate

class AddressProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.district_data = self._load_district_data()
        self.educational_keywords = {
            'university', 'college', 'institute', 'school', 'vishwavidyalaya',
            'mahavidyalaya', 'vidyapeeth', 'polytechnic', 'iit', 'nit', 'iiit',
            'engineering', 'medical', 'technological', 'technology', 'sciences',
            'vidyalaya', 'gurukul', 'academy', 'campus'
        }
        
        # Common Indian address patterns
        self.address_patterns = [
            r'(?P<institution>.*?),?\s*(?P<area>.*?),?\s*(?P<city>.*?),?\s*(?P<state>.*?)\s*(?P<pin>\d{6})?',
            r'(?P<institution>.*?),?\s*(?P<area>.*?),?\s*(?P<state>.*?)\s*-?\s*(?P<pin>\d{6})?',
            r'(?P<institution>.*?),?\s*(?P<landmark>near.*?),?\s*(?P<area>.*?),?\s*(?P<city>.*?)',
            r'(?P<institution>.*?),?\s*(?P<road>.*?road),?\s*(?P<area>.*?),?\s*(?P<city>.*?)'
        ]
        
        # Load state mapping
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
            'OD': 'Odisha',
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

    def _load_district_data(self):
        """Load and cache district data"""
        districts_file = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'india_districts.csv'
        if not districts_file.exists():
            raise FileNotFoundError(f"Districts data file not found: {districts_file}")
            
        districts = {}
        with open(districts_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                state = row['state'].strip()
                district = row['district'].strip()
                if state not in districts:
                    districts[state] = set()
                districts[state].add(district.lower())
        return districts

    def _extract_pin_code(self, text):
        """Extract PIN code from text"""
        pin_match = re.search(r'\b(\d{6})\b', text)
        return pin_match.group(1) if pin_match else None

    def _extract_state(self, text):
        """Extract state from text using state mapping"""
        # Try exact match first
        for full_name in self.state_mapping.values():
            if full_name.lower() in text.lower():
                return full_name
                
        # Try abbreviations
        for abbr, full_name in self.state_mapping.items():
            if f" {abbr} " in f" {text} ":
                return full_name
        
        return None

    def _extract_district(self, text, state=None):
        """Extract district from text"""
        if not state or state not in self.district_data:
            return None
            
        text_lower = text.lower()
        for district in self.district_data[state]:
            if district in text_lower:
                return district.title()
        return None

    def _extract_educational_keywords(self, text):
        """Extract educational keywords from text"""
        found_keywords = []
        text_lower = text.lower()
        for keyword in self.educational_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        return found_keywords

    def process_address(self, address):
        """Process an Indian educational institution address"""
        metadata = {
            'components': {},
            'confidence_factors': {}
        }
        
        # Clean the address
        address = re.sub(r'\s+', ' ', address).strip()
        
        # Extract PIN code
        pin_code = self._extract_pin_code(address)
        if pin_code:
            metadata['components']['pin'] = pin_code
            metadata['confidence_factors']['has_pin'] = True
        
        # Extract state
        state = self._extract_state(address)
        if state:
            metadata['components']['state'] = state
            metadata['confidence_factors']['has_state'] = True
            
            # Extract district if state is known
            district = self._extract_district(address, state)
            if district:
                metadata['components']['district'] = district
                metadata['confidence_factors']['has_district'] = True
        
        # Extract educational keywords
        edu_keywords = self._extract_educational_keywords(address)
        metadata['confidence_factors']['educational_keywords'] = edu_keywords
        metadata['confidence_factors']['is_educational'] = len(edu_keywords) > 0
        
        # Try different address patterns
        best_match = None
        max_components = 0
        
        for pattern in self.address_patterns:
            match = re.match(pattern, address, re.IGNORECASE)
            if match:
                components = {k: v.strip() for k, v in match.groupdict().items() if v}
                if len(components) > max_components:
                    best_match = components
                    max_components = len(components)
        
        if best_match:
            metadata['components'].update(best_match)
        
        # Calculate confidence score
        confidence_score = 0.0
        if metadata['confidence_factors'].get('has_pin'):
            confidence_score += 0.3
        if metadata['confidence_factors'].get('has_state'):
            confidence_score += 0.3
        if metadata['confidence_factors'].get('has_district'):
            confidence_score += 0.2
        if metadata['confidence_factors'].get('is_educational'):
            confidence_score += 0.2
            
        metadata['confidence_score'] = min(1.0, confidence_score)
        
        return address, metadata
