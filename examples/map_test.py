"""
Test script for college map visualization with real data.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.search import SearchFilters
from src.visualization import create_filtered_map

def test_engineering_colleges():
    """Create a map of top engineering colleges"""
    filters = SearchFilters(
        courses=["B.Tech Computer Science and Engineering", "B.Tech Electrical Engineering"],
        naac_grades=["A++", "A+"],
        required_facilities=["Computer Science Lab", "Electronics Lab"],
        institution_types=["Central"]
    )
    
    return create_filtered_map(
        filters=filters,
        output_file="engineering_colleges.html"
    )

def test_delhi_colleges():
    """Create a map of colleges in Delhi"""
    filters = SearchFilters(
        naac_grades=["A++", "A+", "A"],
        institution_types=["Central", "State"]
    )
    
    return create_filtered_map(
        filters=filters,
        output_file="delhi_colleges.html"
    )

def test_top_colleges():
    """Create a map of top-ranked colleges"""
    filters = SearchFilters(
        naac_grades=["A++"],
        max_nirf_rank=20
    )
    
    return create_filtered_map(
        filters=filters,
        output_file="top_colleges.html"
    )

def main():
    """Run all test cases"""
    print("\nCreating maps for different scenarios...")
    
    print("\n1. Top Engineering Colleges")
    eng_map = test_engineering_colleges()
    print(f"Created map: {eng_map}")
    
    print("\n2. Delhi Colleges")
    delhi_map = test_delhi_colleges()
    print(f"Created map: {delhi_map}")
    
    print("\n3. Top Ranked Colleges")
    top_map = test_top_colleges()
    print(f"Created map: {top_map}")
    
    print("\nAll maps created successfully!")

if __name__ == "__main__":
    main()
