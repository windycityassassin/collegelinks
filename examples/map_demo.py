"""
Demo script for college map visualization.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.search import SearchFilters
from src.visualization import create_filtered_map

def main():
    """Create sample maps with different filters"""
    
    # Create a map with all colleges
    print("Creating map with all colleges...")
    create_filtered_map(output_path="all_colleges_map.html")
    
    # Create a map with filtered colleges
    print("\nCreating filtered map...")
    filters = SearchFilters(
        state="Maharashtra",
        city="Mumbai",
        institution_types=["Private"],
        required_facilities=["hostel", "library", "wifi"],
        min_naac_score=3.0,
        max_tuition_fee=500000
    )
    create_filtered_map(
        filters=filters,
        output_path="filtered_colleges_map.html"
    )
    
    print("\nMaps have been created!")
    print("- View all colleges: all_colleges_map.html")
    print("- View filtered colleges: filtered_colleges_map.html")

if __name__ == "__main__":
    main()
