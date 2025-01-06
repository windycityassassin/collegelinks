"""
Tests for college search functionality
"""
import pytest
from pathlib import Path
import json
from .college_search import CollegeSearchEngine, SearchFilters

@pytest.fixture
def sample_college_data():
    """Sample college data for testing"""
    return {
        "001": {
            "id": "001",
            "name": "Test Engineering College",
            "established_year": 1990,
            "institution_type": "Private",
            "approved_by": ["AICTE", "UGC"],
            "location": {
                "address": "Test Address",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
                "district": "Mumbai City"
            },
            "contact": {
                "website": "https://test.edu.in",
                "email": "info@test.edu.in",
                "phone": ["1234567890"]
            },
            "accreditation": {
                "naac_grade": "A++",
                "naac_score": 3.8,
                "nirf_rank": 50
            },
            "infrastructure": {
                "has_hostel": True,
                "library": True,
                "wifi_enabled": True,
                "sports_facilities": ["Cricket", "Football"],
                "auditorium": True,
                "cafeteria": True,
                "medical_facility": True
            },
            "courses": [
                {
                    "name": "B.Tech in Computer Science",
                    "degree": "B.Tech",
                    "duration_years": 4.0,
                    "department": "Computer Science",
                    "specialization": "Computer Science and Engineering",
                    "seats": 120,
                    "course_type": "UG"
                }
            ],
            "fee_structure": {
                "currency": "INR",
                "program_fees": {
                    "B.Tech": {
                        "tuition": 200000,
                        "hostel": 100000,
                        "other": 50000
                    }
                }
            }
        }
    }

@pytest.fixture
def search_engine(sample_college_data, tmp_path):
    """Create a search engine with sample data"""
    # Create necessary directories
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True)
    
    # Write sample data
    with open(processed_dir / "colleges.json", "w") as f:
        json.dump(sample_college_data, f)
    
    return CollegeSearchEngine(str(data_dir))

def test_location_filter(search_engine):
    """Test location-based filtering"""
    # Test state filter
    filters = SearchFilters(state="Maharashtra")
    results = search_engine.search(filters)
    assert len(results) == 1
    
    filters = SearchFilters(state="Karnataka")
    results = search_engine.search(filters)
    assert len(results) == 0
    
    # Test city filter
    filters = SearchFilters(city="Mumbai")
    results = search_engine.search(filters)
    assert len(results) == 1
    
    # Test district filter
    filters = SearchFilters(district="Mumbai City")
    results = search_engine.search(filters)
    assert len(results) == 1

def test_academic_filter(search_engine):
    """Test academic filtering"""
    # Test course filter
    filters = SearchFilters(courses=["B.Tech in Computer Science"])
    results = search_engine.search(filters)
    assert len(results) == 1
    
    # Test degree filter
    filters = SearchFilters(degrees=["B.Tech"])
    results = search_engine.search(filters)
    assert len(results) == 1
    
    # Test specialization filter
    filters = SearchFilters(specializations=["Computer Science and Engineering"])
    results = search_engine.search(filters)
    assert len(results) == 1

def test_fee_filter(search_engine):
    """Test fee-based filtering"""
    # Test min fee filter
    filters = SearchFilters(min_tuition_fee=100000)
    results = search_engine.search(filters)
    assert len(results) == 1
    
    filters = SearchFilters(min_tuition_fee=300000)
    results = search_engine.search(filters)
    assert len(results) == 0
    
    # Test max fee filter
    filters = SearchFilters(max_tuition_fee=250000)
    results = search_engine.search(filters)
    assert len(results) == 1

def test_ranking_filter(search_engine):
    """Test ranking-based filtering"""
    # Test NIRF rank filter
    filters = SearchFilters(min_nirf_rank=1, max_nirf_rank=100)
    results = search_engine.search(filters)
    assert len(results) == 1
    
    # Test NAAC grade filter
    filters = SearchFilters(naac_grades=["A++"])
    results = search_engine.search(filters)
    assert len(results) == 1
    
    # Test NAAC score filter
    filters = SearchFilters(min_naac_score=3.5)
    results = search_engine.search(filters)
    assert len(results) == 1

def test_infrastructure_filter(search_engine):
    """Test infrastructure-based filtering"""
    # Test hostel filter
    filters = SearchFilters(hostel_required=True)
    results = search_engine.search(filters)
    assert len(results) == 1
    
    # Test facilities filter
    filters = SearchFilters(required_facilities=["library", "wifi", "sports"])
    results = search_engine.search(filters)
    assert len(results) == 1

def test_type_filter(search_engine):
    """Test institution type filtering"""
    # Test institution type filter
    filters = SearchFilters(institution_types=["Private"])
    results = search_engine.search(filters)
    assert len(results) == 1
    
    # Test approvals filter
    filters = SearchFilters(approvals=["AICTE", "UGC"])
    results = search_engine.search(filters)
    assert len(results) == 1

def test_combined_filters(search_engine):
    """Test multiple filters together"""
    filters = SearchFilters(
        state="Maharashtra",
        city="Mumbai",
        courses=["B.Tech in Computer Science"],
        institution_types=["Private"],
        hostel_required=True,
        required_facilities=["library", "wifi"],
        min_naac_score=3.5
    )
    results = search_engine.search(filters)
    assert len(results) == 1

def test_get_unique_values(search_engine):
    """Test getting unique values for dropdowns"""
    unique_values = search_engine.get_unique_values()
    
    assert "Maharashtra" in unique_values["states"]
    assert "Mumbai" in unique_values["cities"]
    assert "Mumbai City" in unique_values["districts"]
    assert "B.Tech in Computer Science" in unique_values["courses"]
    assert "B.Tech" in unique_values["degrees"]
    assert "Computer Science and Engineering" in unique_values["specializations"]
    assert "Private" in unique_values["institution_types"]
    assert "AICTE" in unique_values["approvals"]
    assert "A++" in unique_values["naac_grades"]
