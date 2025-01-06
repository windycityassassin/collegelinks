"""
Script to collect and validate training data for the geocoding model
"""
import sys
import os
from pathlib import Path
import pandas as pd
import logging
from typing import List, Dict
import csv
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import time
import random

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.geocoding.smart_geocoder import SmartGeocoder
from src.data_processing.address_processor import AddressProcessor
from src.ml.geocoding_validator import MLGeocodeValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_ugc_universities() -> List[Dict]:
    """Scrape university data from UGC website"""
    base_url = "https://www.ugc.ac.in/oldpdf/Consolidated_CENTRAL_STATE_PRIVATE_DEEMED_March2023.pdf"
    
    # Note: This is a placeholder. The actual implementation would:
    # 1. Download and parse the PDF
    # 2. Extract university names and addresses
    # 3. Clean and structure the data
    
    logger.info("Scraping UGC university data...")
    return []

def scrape_aicte_colleges() -> List[Dict]:
    """Scrape college data from AICTE website"""
    base_url = "https://facilities.aicte-india.org/dashboard/pages/angulardashboard.php#!/approved"
    
    # Note: This is a placeholder. The actual implementation would:
    # 1. Use Selenium to navigate the dynamic website
    # 2. Extract college information
    # 3. Clean and structure the data
    
    logger.info("Scraping AICTE college data...")
    return []

def load_manual_verification_data() -> List[Dict]:
    """Load manually verified institution data"""
    verified_file = project_root / 'data' / 'verified' / 'verified_institutions.csv'
    
    if not verified_file.exists():
        logger.warning("No verified institutions file found")
        return []
    
    verified_data = []
    with open(verified_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            verified_data.append({
                'name': row['name'],
                'address': row['address'],
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'verified': True
            })
    
    return verified_data

def generate_negative_examples(institutions: List[Dict]) -> List[Dict]:
    """Generate negative examples for training"""
    negative_examples = []
    
    for inst in institutions:
        # Example 1: Wrong PIN code
        wrong_pin = inst.copy()
        wrong_pin['address'] = wrong_pin['address'].replace(
            wrong_pin['address'][-6:],
            str(int(wrong_pin['address'][-6:]) + 1000).zfill(6)
        )
        wrong_pin['verified'] = False
        negative_examples.append(wrong_pin)
        
        # Example 2: Wrong city/state
        wrong_location = inst.copy()
        wrong_location['address'] = wrong_location['address'].replace(
            wrong_location['address'].split(',')[-2],
            'Wrong City'
        )
        wrong_location['verified'] = False
        negative_examples.append(wrong_location)
        
        # Example 3: Incomplete address
        incomplete = inst.copy()
        incomplete['address'] = ', '.join(incomplete['address'].split(',')[:-2])
        incomplete['verified'] = False
        negative_examples.append(incomplete)
    
    return negative_examples

def validate_and_save_data(
    institutions: List[Dict],
    geocoder: SmartGeocoder,
    address_processor: AddressProcessor,
    output_file: Path
):
    """Validate and save training data"""
    validated_data = []
    
    for inst in tqdm(institutions, desc="Validating institutions"):
        try:
            # Process address
            processed_address, metadata = address_processor.process_address(inst['address'])
            
            # Get geocoding result
            result = geocoder.geocode(processed_address)
            
            if result and result.get('confidence_score', 0) > 0.8:
                validated_data.append({
                    'name': inst['name'],
                    'address': inst['address'],
                    'processed_address': processed_address,
                    'latitude': result['latitude'],
                    'longitude': result['longitude'],
                    'confidence_score': result['confidence_score'],
                    'metadata': metadata,
                    'verified': inst.get('verified', False)
                })
            
            # Rate limiting
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            logger.error(f"Error processing {inst['name']}: {e}")
            continue
    
    # Save to CSV
    df = pd.DataFrame(validated_data)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved {len(validated_data)} validated institutions to {output_file}")

def main():
    """Main data collection script"""
    # Initialize components
    geocoder = SmartGeocoder(
        google_api_key=os.getenv('GOOGLE_MAPS_API_KEY'),
        cache_dir=str(project_root / 'data' / 'cache')
    )
    address_processor = AddressProcessor()
    
    # Create output directory
    output_dir = project_root / 'data' / 'training'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect data from different sources
    institutions = []
    
    # 1. Load manually verified data
    verified = load_manual_verification_data()
    institutions.extend(verified)
    logger.info(f"Loaded {len(verified)} manually verified institutions")
    
    # 2. Scrape UGC universities (when implemented)
    # ugc_unis = scrape_ugc_universities()
    # institutions.extend(ugc_unis)
    # logger.info(f"Scraped {len(ugc_unis)} UGC universities")
    
    # 3. Scrape AICTE colleges (when implemented)
    # aicte_colleges = scrape_aicte_colleges()
    # institutions.extend(aicte_colleges)
    # logger.info(f"Scraped {len(aicte_colleges)} AICTE colleges")
    
    # 4. Generate negative examples
    negatives = generate_negative_examples(verified)
    institutions.extend(negatives)
    logger.info(f"Generated {len(negatives)} negative examples")
    
    # Validate and save data
    output_file = output_dir / 'training_data.csv'
    validate_and_save_data(
        institutions,
        geocoder,
        address_processor,
        output_file
    )

if __name__ == '__main__':
    main()
