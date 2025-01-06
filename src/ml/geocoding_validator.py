"""
Machine Learning based geocoding validator for Indian educational institutions
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from typing import Dict, List, Optional, Tuple
import joblib
from pathlib import Path
import logging
from fuzzywuzzy import fuzz

class MLGeocodeValidator:
    def __init__(self, model_dir: Optional[str] = None):
        """Initialize ML-based geocoding validator"""
        self.logger = logging.getLogger(__name__)
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent.parent.parent / 'models'
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize models and encoders
        self.classifier = None
        self.label_encoder = LabelEncoder()
        self.feature_names = [
            'has_pin_code', 'pin_match_score',
            'district_match_score', 'state_match_score',
            'has_edu_keywords', 'address_length',
            'component_count', 'location_type_score',
            'place_type_score', 'coordinate_precision'
        ]
        
        # Load model if exists
        self._load_model()

    def _load_model(self):
        """Load trained model and encoders"""
        model_path = self.model_dir / 'geocoding_validator.joblib'
        if model_path.exists():
            try:
                model_data = joblib.load(model_path)
                self.classifier = model_data['classifier']
                self.label_encoder = model_data['label_encoder']
                self.logger.info("Loaded existing model")
            except Exception as e:
                self.logger.error(f"Error loading model: {e}")
                self.classifier = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )

    def _save_model(self):
        """Save trained model and encoders"""
        model_path = self.model_dir / 'geocoding_validator.joblib'
        model_data = {
            'classifier': self.classifier,
            'label_encoder': self.label_encoder
        }
        joblib.dump(model_data, model_path)
        self.logger.info("Saved model")

    def extract_features(self, geocode_result: Dict, address_metadata: Dict) -> np.ndarray:
        """Extract features from geocoding result"""
        features = []
        
        # PIN code features
        pin_code = None
        for component in geocode_result.get('address_components', []):
            if 'postal_code' in component.get('types', []):
                pin_code = component['long_name']
                break
        
        features.append(1 if pin_code else 0)  # has_pin_code
        features.append(
            fuzz.ratio(pin_code or '', address_metadata.get('components', {}).get('pin', '')) / 100
        )  # pin_match_score
        
        # District and state matching
        district_match = 0
        state_match = 0
        for component in geocode_result.get('address_components', []):
            if 'administrative_area_level_2' in component.get('types', []):
                district_match = fuzz.ratio(
                    component['long_name'].lower(),
                    address_metadata.get('components', {}).get('district', '').lower()
                ) / 100
            if 'administrative_area_level_1' in component.get('types', []):
                state_match = fuzz.ratio(
                    component['long_name'].lower(),
                    address_metadata.get('components', {}).get('state', '').lower()
                ) / 100
        
        features.append(district_match)  # district_match_score
        features.append(state_match)  # state_match_score
        
        # Educational keywords
        edu_keywords = {
            'university', 'college', 'institute', 'school',
            'vishwavidyalaya', 'mahavidyalaya', 'vidyalaya',
            'polytechnic', 'academy', 'education'
        }
        has_edu = 0
        address = geocode_result.get('formatted_address', '').lower()
        if any(keyword in address for keyword in edu_keywords):
            has_edu = 1
        features.append(has_edu)  # has_edu_keywords
        
        # Address complexity
        features.append(len(address) / 1000)  # address_length (normalized)
        features.append(
            len(geocode_result.get('address_components', [])) / 10
        )  # component_count (normalized)
        
        # Location type score
        location_type_scores = {
            'ROOFTOP': 1.0,
            'RANGE_INTERPOLATED': 0.8,
            'GEOMETRIC_CENTER': 0.6,
            'APPROXIMATE': 0.4
        }
        features.append(
            location_type_scores.get(
                geocode_result.get('geometry', {}).get('location_type', ''),
                0.0
            )
        )  # location_type_score
        
        # Place type score
        place_type_scores = {
            'establishment': 0.5,
            'point_of_interest': 0.3,
            'school': 0.8,
            'university': 1.0
        }
        max_type_score = 0.0
        for type_ in geocode_result.get('types', []):
            if type_ in place_type_scores:
                max_type_score = max(max_type_score, place_type_scores[type_])
        features.append(max_type_score)  # place_type_score
        
        # Coordinate precision
        viewport = geocode_result.get('geometry', {}).get('viewport', {})
        if viewport:
            ne = viewport.get('northeast', {})
            sw = viewport.get('southwest', {})
            if ne and sw:
                lat_precision = abs(ne.get('lat', 0) - sw.get('lat', 0))
                lng_precision = abs(ne.get('lng', 0) - sw.get('lng', 0))
                precision_score = 1.0 - min(1.0, (lat_precision + lng_precision) / 2)
            else:
                precision_score = 0.5
        else:
            precision_score = 0.0
        features.append(precision_score)  # coordinate_precision
        
        return np.array(features).reshape(1, -1)

    def train(self, training_data: List[Tuple[Dict, Dict, bool]]):
        """
        Train the validator model
        
        Args:
            training_data: List of (geocode_result, address_metadata, is_valid) tuples
        """
        if not training_data:
            self.logger.warning("No training data provided")
            return
        
        # Extract features and labels
        X = []
        y = []
        
        for result, metadata, is_valid in training_data:
            try:
                features = self.extract_features(result, metadata)
                X.append(features[0])  # Flatten the 2D array
                y.append(is_valid)
            except Exception as e:
                self.logger.error(f"Error extracting features: {e}")
                continue
        
        if not X:
            self.logger.error("No valid features extracted from training data")
            return
        
        X = np.array(X)
        y = np.array(y)
        
        # Initialize and train classifier
        if self.classifier is None:
            self.classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        
        try:
            self.classifier.fit(X, y)
            self._save_model()
            self.logger.info(f"Model trained on {len(X)} samples")
        except Exception as e:
            self.logger.error(f"Error training model: {e}")

    def validate(self, geocode_result: Dict, address_metadata: Dict) -> Tuple[bool, float]:
        """
        Validate geocoding result using ML model
        
        Returns:
            Tuple of (is_valid, confidence_score)
        """
        if self.classifier is None:
            self.logger.warning("No trained model available")
            return True, 0.5
        
        try:
            features = self.extract_features(geocode_result, address_metadata)
            probabilities = self.classifier.predict_proba(features)
            is_valid = probabilities[0][1] >= 0.5  # Probability of valid class
            confidence = probabilities[0][1]
            
            return is_valid, confidence
        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
            return True, 0.5  # Default to accepting result with low confidence
