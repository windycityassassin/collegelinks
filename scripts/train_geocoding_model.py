"""
Script to train the ML geocoding validator with sample data
"""
import sys
import os
from pathlib import Path
import pandas as pd
import logging
from typing import List, Dict, Tuple

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.ml.geocoding_validator import MLGeocodeValidator
from src.geocoding.smart_geocoder import SmartGeocoder
from src.data_processing.address_processor import AddressProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_sample_data() -> pd.DataFrame:
    """Load sample data with known correct geocoding results"""
    # This would typically load from a verified dataset
    # For now, we'll create a small sample
    return pd.DataFrame([
        {
            'name': 'Indian Institute of Technology Delhi',
            'address': 'IIT Delhi, Hauz Khas, New Delhi, Delhi 110016',
            'district': 'South Delhi',
            'state': 'Delhi',
            'pin': '110016',
            'correct_lat': 28.5449756,
            'correct_lon': 77.1926225
        },
        {
            'name': 'University of Delhi',
            'address': 'University of Delhi, North Campus, Delhi 110007',
            'district': 'North Delhi',
            'state': 'Delhi',
            'pin': '110007',
            'correct_lat': 28.6883816,
            'correct_lon': 77.2041368
        },
        {
            'name': 'Anna University',
            'address': 'Anna University, Guindy, Chennai, Tamil Nadu 600025',
            'district': 'Chennai',
            'state': 'Tamil Nadu',
            'pin': '600025',
            'correct_lat': 13.0122,
            'correct_lon': 80.2356
        }
        # Add more verified institutions here
    ])

def generate_training_data(
    geocoder: SmartGeocoder,
    address_processor: AddressProcessor,
    sample_data: pd.DataFrame
) -> List[Tuple[Dict, Dict, bool]]:
    """Generate training data from sample institutions"""
    training_data = []
    
    for _, row in sample_data.iterrows():
        # Process address
        processed_address, metadata = address_processor.process_address(row['address'])
        metadata['components'].update({
            'district': row['district'],
            'state': row['state'],
            'pin': row['pin']
        })
        
        # Get geocoding result
        try:
            result = geocoder._geocode_google(processed_address)
            if result:
                # Check if result is within 1km of known correct location
                from geopy.distance import geodesic
                distance = geodesic(
                    (result['latitude'], result['longitude']),
                    (row['correct_lat'], row['correct_lon'])
                ).kilometers
                
                # Add to training data
                training_data.append((
                    result,
                    metadata,
                    distance <= 1.0  # Consider valid if within 1km
                ))
                
                logger.info(f"Processed {row['name']}: {'Valid' if distance <= 1.0 else 'Invalid'}")
            
            # Also try some intentionally wrong addresses for negative examples
            wrong_address = f"{row['name']}, Wrong City, Wrong State"
            wrong_result = geocoder._geocode_google(wrong_address)
            if wrong_result:
                training_data.append((
                    wrong_result,
                    metadata,
                    False  # This should be invalid
                ))
        except Exception as e:
            logger.error(f"Error processing {row['name']}: {e}")
            continue
    
    return training_data

def main():
    """Main training script"""
    # Initialize components
    geocoder = SmartGeocoder(
        google_api_key=os.getenv('GOOGLE_MAPS_API_KEY'),
        cache_dir=str(project_root / 'data' / 'cache')
    )
    address_processor = AddressProcessor()
    ml_validator = MLGeocodeValidator(
        model_dir=str(project_root / 'models')
    )
    
    # Load and process sample data
    logger.info("Loading sample data...")
    sample_data = load_sample_data()
    
    # Generate training data
    logger.info("Generating training data...")
    training_data = generate_training_data(
        geocoder,
        address_processor,
        sample_data
    )
    
    # Train the model
    logger.info(f"Training model with {len(training_data)} samples...")
    ml_validator.train(training_data)
    
    logger.info("Training complete!")

if __name__ == '__main__':
    main()
