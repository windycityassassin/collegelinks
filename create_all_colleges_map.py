"""
Create an interactive map with all colleges
"""
from collegelinks.visualization import FilteredCollegeMap

def create_all_colleges_map():
    """Create a map with all colleges"""
    print("\nCreating map with all colleges...")
    
    # Create map
    college_map = FilteredCollegeMap()
    
    # Add colleges without any filters
    college_map.add_colleges()
    
    # Save map
    output_file = "all_colleges_interactive_map.html"
    college_map.save(output_file)
    print(f"Map created: {output_file}")
    return output_file

if __name__ == "__main__":
    create_all_colleges_map()
