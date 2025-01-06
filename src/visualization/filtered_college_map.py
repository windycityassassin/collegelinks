"""
Map visualization for filtered college data.
"""
from typing import Optional, List
import folium
from folium import plugins, FeatureGroup
from ..search import CollegeSearchEngine, SearchFilters
from ..schemas import CollegeProfile

class FilteredCollegeMap:
    """Class to create and manage filtered college maps"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize map with data directory"""
        self.search_engine = CollegeSearchEngine(data_dir)
        self.map = None
        self.college_layer = None
        self.marker_cluster = None
    
    def create_base_map(self, center: List[float] = [20.5937, 78.9629], zoom: int = 5):
        """Create base map centered on India"""
        self.map = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles="cartodbpositron"
        )
        
        # Add fullscreen control
        self.map.add_child(plugins.Fullscreen())
        
        # Create feature group for colleges
        self.college_layer = FeatureGroup(name="Colleges")
        self.map.add_child(self.college_layer)
        
        # Add marker cluster
        self.marker_cluster = plugins.MarkerCluster().add_to(self.college_layer)
        
        # Add search control
        self.map.add_child(plugins.Search(
            layer=self.college_layer,
            search_label="tooltip",
            position="topleft"
        ))
    
    def get_marker_color(self, college: CollegeProfile) -> str:
        """Get marker color based on college type"""
        color_map = {
            "Central": "red",
            "State": "blue",
            "Private": "green",
            "Deemed": "orange"
        }
        return color_map.get(college.type, "gray")
    
    def create_popup_content(self, college: CollegeProfile) -> str:
        """Create HTML content for college popup"""
        content = f"""
        <div style='width:300px'>
            <h4>{college.name}</h4>
            <p><b>Type:</b> {college.type}</p>
            <p><b>Established:</b> {college.established}</p>
        """
        
        # Add NIRF and NAAC info
        if college.accreditation:
            content += "<p><b>Accreditation:</b><br>"
            if college.accreditation.nirf_rank:
                content += f"NIRF Rank: {college.accreditation.nirf_rank}<br>"
            if college.accreditation.naac_grade:
                content += f"NAAC Grade: {college.accreditation.naac_grade}"
            content += "</p>"
        
        # Add courses
        content += "<p><b>Programs:</b><ul>"
        for program_type, courses in college.courses.items():
            content += f"<li>{program_type.title()}:<ul>"
            for course in courses[:3]:  # Show first 3 courses
                content += f"<li>{course.name}</li>"
            if len(courses) > 3:
                content += f"<li>...and {len(courses)-3} more</li>"
            content += "</ul></li>"
        content += "</ul></p>"
        
        # Add facilities
        content += "<p><b>Facilities:</b><ul>"
        if college.facilities.library:
            content += f"<li>Library: {college.facilities.library.name}</li>"
        if college.facilities.hostel:
            hostel_info = []
            if college.facilities.hostel.boys:
                hostel_info.append("Boys")
            if college.facilities.hostel.girls:
                hostel_info.append("Girls")
            content += f"<li>Hostel: {', '.join(hostel_info)} (Capacity: {college.facilities.hostel.total_capacity})</li>"
        if college.facilities.sports:
            content += f"<li>Sports: {', '.join(college.facilities.sports[:3])}</li>"
        content += "</ul></p>"
        
        # Add contact info
        content += f"""
        <p><b>Contact:</b><br>
        Website: <a href='{college.contact.website}' target='_blank'>Visit Website</a><br>
        Email: {college.contact.email}<br>
        Phone: {college.contact.phone}
        </p>
        """
        
        # Add virtual tour if available
        if college.media and college.media.virtual_tour:
            content += f"<p><a href='{college.media.virtual_tour}' target='_blank'>Take Virtual Tour</a></p>"
        
        content += "</div>"
        return content
    
    def add_colleges(self, filters: Optional[SearchFilters] = None):
        """Add filtered colleges to the map"""
        if not self.map:
            self.create_base_map()
        
        colleges = self.search_engine.search(filters) if filters else list(self.search_engine.colleges.values())
        
        for college in colleges:
            # Skip if no location data
            if not college.latitude or not college.longitude:
                continue
                
            # Add marker
            folium.Marker(
                location=[college.latitude, college.longitude],
                popup=folium.Popup(self.create_popup_content(college), max_width=350),
                tooltip=college.name,
                icon=folium.Icon(color=self.get_marker_color(college), icon='info-sign')
            ).add_to(self.marker_cluster)
    
    def save(self, output_file: str):
        """Save map to HTML file"""
        if not self.map:
            raise ValueError("Map not created yet. Call add_colleges() first.")
        self.map.save(output_file)

def create_filtered_map(
    data_dir: str = "data",
    filters: Optional[SearchFilters] = None,
    output_file: str = "college_map.html"
) -> str:
    """
    Create a filtered college map
    
    Args:
        data_dir: Directory containing college data
        filters: Optional search filters
        output_file: Output HTML file path
        
    Returns:
        Path to generated HTML file
    """
    college_map = FilteredCollegeMap(data_dir)
    college_map.add_colleges(filters)
    college_map.save(output_file)
    return output_file
