"""
Visualization functionality for college data
"""
from typing import Optional, List, Dict
import folium
from folium import plugins
from folium.plugins import MarkerCluster
from .data_loader import CollegeDataLoader

class FilteredCollegeMap:
    """Class to create and manage filtered college maps"""
    def __init__(self, data_dir: str = "data"):
        """Initialize map with data directory"""
        self.data_loader = CollegeDataLoader(data_dir)
        self.map = None
        
    def get_marker_color(self, college: dict) -> str:
        """Get marker color based on college type"""
        color_map = {
            "Central": "red",
            "State": "blue",
            "Private": "green",
            "Deemed": "orange"
        }
        return color_map.get(college.get('type', ''), "gray")
        
    def create_popup_content(self, college: dict) -> str:
        """Create HTML content for college popup"""
        content = f"""
            <div style='min-width: 300px'>
                <h4>{college['name']}</h4>
                <p><b>Type:</b> {college.get('type', 'N/A')}</p>
        """
        
        # Add location info
        location_parts = []
        if college.get('city'):
            location_parts.append(college['city'])
        if college.get('state'):
            location_parts.append(college['state'])
        location = ', '.join(location_parts) if location_parts else 'N/A'
        content += f"<p><b>Location:</b> {location}</p>"
        
        # Add full address if available
        if college.get('address'):
            content += f"<p><b>Address:</b> {college['address']}</p>"
            
        # Add university affiliation if available
        if college.get('university'):
            content += f"<p><b>Affiliated to:</b> {college['university']}</p>"
            
        content += "</div>"
        return content
        
    def create_map(self, colleges: List[dict]) -> None:
        """Create an interactive map with college markers"""
        # Create the map centered on India
        self.map = folium.Map(
            location=[20.5937, 78.9629],
            zoom_start=5,
            tiles='cartodbpositron',
            control_scale=True
        )

        # Add custom CSS for full-screen map
        custom_css = """
        <style>
            html, body {
                margin: 0;
                padding: 0;
                height: 100%;
                width: 100%;
            }
            .folium-map {
                height: 100vh;
                width: 100%;
                position: relative;
            }
        </style>
        """
        self.map.get_root().html.add_child(folium.Element(custom_css))

        # Create a marker cluster
        marker_cluster = MarkerCluster().add_to(self.map)
        
        # Create a feature group for searchable markers
        search_group = folium.FeatureGroup(name="Searchable Markers")
        self.map.add_child(search_group)

        # Add the colleges to the map
        for college in colleges:
            if not college.get('latitude') or not college.get('longitude'):
                continue

            # Create popup content
            popup_content = self.create_popup_content(college)
            
            # Add marker to cluster for display
            folium.Marker(
                location=[float(college['latitude']), float(college['longitude'])],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=college['name'],
                icon=folium.Icon(color=self.get_marker_color(college))
            ).add_to(marker_cluster)
            
            # Add a simple circle marker to the search group
            folium.CircleMarker(
                location=[float(college['latitude']), float(college['longitude'])],
                radius=0,
                popup=college['name'],
                fill=False,
                weight=0,
                tooltip=college['name']
            ).add_to(search_group)

        # Add the search control
        self.map.add_child(folium.plugins.Search(
            layer=search_group,
            search_label="tooltip",
            search_zoom=15,
            position='topleft',
            placeholder='Search colleges...',
            collapsed=False,
            search_initial=False
        ))

        # Add fullscreen control
        plugins.Fullscreen().add_to(self.map)

    def add_colleges(self, filters: Optional[dict] = None):
        """Add filtered colleges to the map"""
        colleges = self.data_loader.filter_colleges(filters) if filters else self.data_loader.load_colleges()
        print(f"Found {len(colleges)} colleges matching filters: {filters}")
        self.create_map(colleges)
            
    def save(self, output_file: str):
        """Save map to HTML file"""
        if not self.map:
            self.create_map([])
        self.map.save(output_file)

def create_filtered_map(
    data_dir: str = "data",
    filters: Optional[dict] = None,
    output_file: str = "college_map.html"
) -> str:
    """Create a filtered college map"""
    college_map = FilteredCollegeMap(data_dir)
    college_map.add_colleges(filters)
    college_map.save(output_file)
    return output_file
