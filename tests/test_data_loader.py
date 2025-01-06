"""
Tests for the college data loader functionality
"""
import os
import pytest
import pandas as pd
import json
from pathlib import Path
from collegelinks.data_loader import CollegeDataLoader

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary test data directory with sample data"""
    # Create directory structure
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    # Create sample colleges CSV
    colleges_df = pd.DataFrame({
        'Name of the college': ['Test College', 'Empty Data College', 'Invalid Year College'],
        'Year of Estb.': ['2000', '', 'invalid'],
        'College address': ['123 Test St, Delhi', '456 Sample Rd, Mumbai', '789 Demo Ave, Chennai'],
        'State': ['Delhi', 'Maharashtra', 'Tamil Nadu'],
        'type': ['Central', 'State', 'Private'],
        'nirf_rank': ['1', '', 'invalid'],
        'naac_grade': ['A++', '', 'B'],
        'website': ['test.edu', '', 'invalid.edu'],
        'email': ['test@test.edu', '', 'invalid@test.edu'],
        'phone': ['1234567890', '', '9876543210']
    })
    colleges_df.to_csv(raw_dir / "Colleges.csv", index=False)
    
    # Create sample PIN codes CSV
    pin_codes_df = pd.DataFrame({
        'pincode': ['110001', '400001', '600001'],
        'district': ['Delhi', 'Mumbai', 'Chennai'],
        'state': ['Delhi', 'Maharashtra', 'Tamil Nadu']
    })
    pin_codes_df.to_csv(raw_dir / "india_pin_codes.csv", index=False)
    
    # Create sample districts CSV
    districts_df = pd.DataFrame({
        'district': ['Delhi', 'Mumbai', 'Chennai'],
        'state': ['Delhi', 'Maharashtra', 'Tamil Nadu']
    })
    districts_df.to_csv(raw_dir / "india_districts.csv", index=False)
    
    return tmp_path

def test_data_loader_initialization(test_data_dir):
    """Test data loader initialization"""
    loader = CollegeDataLoader(str(test_data_dir))
    assert loader.data_dir == Path(test_data_dir)
    assert os.path.exists(loader.raw_dir)
    assert os.path.exists(loader.interim_dir)
    assert os.path.exists(loader.processed_dir)

def test_load_colleges(test_data_dir):
    """Test loading college data"""
    loader = CollegeDataLoader(str(test_data_dir))
    df = loader.load_colleges()
    assert len(df) == 3
    assert 'Name of the college' in df.columns
    assert 'source' in df.columns

def test_process_address(test_data_dir):
    """Test address processing"""
    loader = CollegeDataLoader(str(test_data_dir))
    df = loader.load_colleges()
    row = df.iloc[0]
    
    address_info = loader._process_address(row)
    assert isinstance(address_info, dict)
    assert 'address' in address_info
    assert 'state' in address_info
    assert address_info['state'] == 'Delhi'

def test_create_college_profile(test_data_dir):
    """Test college profile creation with different data scenarios"""
    loader = CollegeDataLoader(str(test_data_dir))
    df = loader.load_colleges()
    
    # Test normal data
    normal_profile = loader._create_college_profile(df.iloc[0])
    assert normal_profile['name'] == 'Test College'
    assert normal_profile['established'] == 2000
    assert normal_profile['accreditation']['nirf_rank'] == 1
    
    # Test empty data
    empty_profile = loader._create_college_profile(df.iloc[1])
    assert empty_profile['established'] == 0  # Default value
    assert empty_profile['accreditation']['nirf_rank'] is None  # Default value
    
    # Test invalid data
    invalid_profile = loader._create_college_profile(df.iloc[2])
    assert invalid_profile['established'] == 0  # Default for invalid
    assert invalid_profile['accreditation']['nirf_rank'] is None  # Default for invalid

def test_full_processing(test_data_dir):
    """Test end-to-end data processing"""
    loader = CollegeDataLoader(str(test_data_dir))
    loader.process_college_data()
    
    output_file = os.path.join(loader.processed_dir, "college_profiles.json")
    assert os.path.exists(output_file)

def test_filter_colleges():
    """Test college filtering functionality"""
    # Create test data
    test_colleges = {
        "colleges": [
            {
                "id": "TEST_COLLEGE_1",
                "name": "Test Engineering College",
                "state": "Maharashtra",
                "city": "Mumbai",
                "courses": {
                    "B.Tech": [
                        {
                            "name": "Computer Science",
                            "fee_per_semester": 50000
                        }
                    ]
                },
                "accreditation": {
                    "naac_grade": "A",
                    "nirf_rank": 50
                },
                "facilities": {
                    "sports": ["Cricket", "Football"],
                    "labs": ["Computer Lab", "Physics Lab"],
                    "hostel": {"boys": True, "girls": True},
                    "library": {"books": 100000}
                }
            },
            {
                "id": "TEST_COLLEGE_2",
                "name": "Test Medical College",
                "state": "Karnataka",
                "city": "Bangalore",
                "courses": {
                    "MBBS": [
                        {
                            "name": "Medicine",
                            "fee_per_semester": 100000
                        }
                    ]
                },
                "accreditation": {
                    "naac_grade": "B",
                    "nirf_rank": 100
                },
                "facilities": {
                    "sports": ["Cricket"],
                    "labs": ["Biology Lab"],
                    "hostel": {"boys": False, "girls": True},
                    "library": {"books": 50000}
                }
            }
        ]
    }
    
    # Write test data to file
    test_data_dir = "tests/data"
    os.makedirs(os.path.join(test_data_dir, "processed"), exist_ok=True)
    with open(os.path.join(test_data_dir, "processed", "college_profiles.json"), "w") as f:
        json.dump(test_colleges, f)
    
    # Initialize data loader with test data
    loader = CollegeDataLoader(test_data_dir)
    
    # Test location filter
    assert len(loader.filter_colleges({"state": "Maharashtra"})) == 1
    assert len(loader.filter_colleges({"city": "Bangalore"})) == 1
    
    # Test course filter
    assert len(loader.filter_colleges({"course": "Computer"})) == 1
    assert len(loader.filter_colleges({"course": "Medicine"})) == 1
    
    # Test fees filter
    assert len(loader.filter_colleges({"max_fee": 75000})) == 1
    assert len(loader.filter_colleges({"max_fee": 150000})) == 2
    
    # Test rankings filter
    assert len(loader.filter_colleges({"min_nirf_rank": 75})) == 1
    assert len(loader.filter_colleges({"naac_grade": "A"})) == 1
    
    # Test infrastructure filters
    assert len(loader.filter_colleges({"facilities": ["Cricket"]})) == 2
    assert len(loader.filter_colleges({"facilities": ["Football"]})) == 1
    assert len(loader.filter_colleges({"hostel_required": True})) == 2
    assert len(loader.filter_colleges({"min_library_books": 75000})) == 1
    
    # Test multiple filters
    filters = {
        "state": "Maharashtra",
        "course": "Computer",
        "max_fee": 75000,
        "facilities": ["Cricket"]
    }
    assert len(loader.filter_colleges(filters)) == 1

if __name__ == '__main__':
    pytest.main([__file__])
