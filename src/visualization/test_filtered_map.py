"""
Test the filtered college map visualization.
"""
import pytest
from pathlib import Path
from ..search import SearchFilters
from .filtered_college_map import create_filtered_map

def test_map_creation():
    """Test basic map creation without filters"""
    output_path = "test_map.html"
    
    # Create map
    map_file = create_filtered_map(output_path=output_path)
    
    # Check if file was created
    assert Path(map_file).exists()
    
    # Clean up
    Path(map_file).unlink()

def test_filtered_map():
    """Test map creation with filters"""
    output_path = "test_filtered_map.html"
    
    # Create filters
    filters = SearchFilters(
        state="Maharashtra",
        city="Mumbai",
        institution_types=["Private"],
        required_facilities=["hostel", "library"],
        min_naac_score=3.0
    )
    
    # Create map
    map_file = create_filtered_map(
        filters=filters,
        output_path=output_path
    )
    
    # Check if file was created
    assert Path(map_file).exists()
    
    # Clean up
    Path(map_file).unlink()

def test_invalid_data_dir():
    """Test handling of invalid data directory"""
    with pytest.raises(ValueError, match="Invalid data directory"):
        create_filtered_map(data_dir="nonexistent_dir")
