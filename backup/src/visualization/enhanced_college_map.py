"""
Generate an enhanced interactive map of colleges with search functionality
"""
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from pathlib import Path
import json

def create_enhanced_map(df):
    """Create an enhanced interactive map with modern popups and search functionality"""
    
    # Create a base map centered on India
    m = folium.Map(
        location=[20.5937, 78.9629],
        zoom_start=5,
        tiles='OpenStreetMap'
    )
    
    # Create marker cluster
    marker_cluster = MarkerCluster(
        name="College Clusters",
        overlay=True,
        control=True,
        options={
            'spiderfyOnMaxZoom': True,
            'showCoverageOnHover': True,
            'zoomToBoundsOnClick': True
        }
    ).add_to(m)

    # Create a dictionary of college data for search and filtering
    college_data = []
    
    # Extract unique values for filters
    states = sorted([str(state) for state in df['state'].unique() if pd.notna(state)])
    institution_types = sorted([str(t) for t in df['institution_type'].unique() if pd.notna(t)])
    
    print(f"Found {len(states)} states and {len(institution_types)} institution types")
    print("States:", states[:5], "...")  # Print first 5 states
    print("Types:", institution_types[:5], "...")  # Print first 5 types
    
    # Add markers for each college
    for idx, row in df.iterrows():
        try:
            lat = float(row['latitude'])
            lon = float(row['longitude'])
            
            if pd.isna(lat) or pd.isna(lon):
                continue
                
            # Get college type and set color
            college_type = str(row['institution_type']).lower()
            color = 'red' if 'central' in college_type else 'blue'
            
            # Store college data for search and filtering
            college_data.append({
                'name': str(row['name']),
                'lat': lat,
                'lng': lon,
                'type': str(row['institution_type']),
                'state': str(row['state']),
                'status': str(row.get('status', ''))
            })
            
            # Create popup content
            popup_content = f"""
            <div style="min-width: 200px; font-family: Arial, sans-serif;">
                <h4 style="margin: 0; padding: 10px; background: {'#e74c3c' if 'central' in college_type else '#3498db'}; color: white;">
                    {row['name']}
                </h4>
                <div style="padding: 10px;">
                    <p><strong>Type:</strong> {row['institution_type']}</p>
                    <p><strong>State:</strong> {row['state']}</p>
                    <p><strong>Status:</strong> {row.get('status', 'N/A')}</p>
                </div>
            </div>
            """
            
            # Create marker
            marker = folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=row['name'],
                icon=folium.Icon(color=color)
            )
            marker.add_to(marker_cluster)
            
        except (ValueError, TypeError) as e:
            print(f"Error processing row {idx}: {e}")
            continue

    # Create filter panel HTML
    filter_html = f"""
    <div id="filter-panel" style="position: fixed; top: 20px; right: 20px; background: white; 
         padding: 15px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); z-index: 1000; 
         max-width: 300px; max-height: 80vh; overflow-y: auto;">
        <h3 style="margin-top: 0;">Filters</h3>
        
        <!-- State Filter -->
        <div class="filter-section">
            <label>State:</label>
            <select id="state-filter" style="width: 100%; padding: 5px; margin: 5px 0;">
                <option value="">All States</option>
                {''.join(f'<option value="{state}">{state}</option>' for state in states)}
            </select>
        </div>

        <!-- Institution Type Filter -->
        <div class="filter-section">
            <label>Institution Type:</label>
            <select id="type-filter" style="width: 100%; padding: 5px; margin: 5px 0;">
                <option value="">All Types</option>
                {''.join(f'<option value="{t}">{t}</option>' for t in institution_types)}
            </select>
        </div>

        <!-- Status Filter -->
        <div class="filter-section">
            <label>Status:</label>
            <div id="status-filter" style="margin: 5px 0;">
                <label><input type="checkbox" value="2(f)"> 2(f)</label>
                <label><input type="checkbox" value="2(f) & 12(B)"> 2(f) & 12(B)</label>
            </div>
        </div>

        <button id="apply-filters" style="width: 100%; padding: 8px; margin-top: 10px; 
                background: #3498db; color: white; border: none; border-radius: 4px; 
                cursor: pointer;">Apply Filters</button>
    </div>
    """

    # Add filter JavaScript
    filter_js = f"""
    <script>
    // College data and map variables
    var collegeData = {json.dumps(college_data, default=str)};
    var map = null;
    var markers = [];
    
    // Wait for map to be ready
    function initMap() {{
        var mapDiv = document.getElementById('map');
        if (mapDiv && mapDiv._leaflet_id) {{
            map = mapDiv._leaflet_map;
            if (map) {{
                // Add click handler to apply button
                var applyButton = document.getElementById('apply-filters');
                if (applyButton) {{
                    applyButton.addEventListener('click', applyFilters);
                }}
                return;
            }}
        }}
        setTimeout(initMap, 100);
    }}
    
    // Apply filters to markers
    function applyFilters() {{
        if (!map) return;
        
        var state = document.getElementById('state-filter').value;
        var type = document.getElementById('type-filter').value;
        var statuses = Array.from(document.querySelectorAll('#status-filter input:checked')).map(cb => cb.value);
        
        // Clear existing markers
        markers.forEach(marker => map.removeLayer(marker));
        markers = [];
        
        // Filter colleges
        var filteredColleges = collegeData.filter(college => {{
            if (state && college.state !== state) return false;
            if (type && college.type !== type) return false;
            if (statuses.length > 0 && !statuses.includes(college.status)) return false;
            return true;
        }});
        
        // Add filtered markers
        filteredColleges.forEach(college => {{
            var color = college.type.toLowerCase().includes('central') ? 'red' : 'blue';
            
            var marker = L.marker([college.lat, college.lng], {{
                title: college.name
            }});
            
            var popupContent = `
                <div style="min-width: 200px; font-family: Arial, sans-serif;">
                    <h4 style="margin: 0; padding: 10px; background: ${{color === 'red' ? '#e74c3c' : '#3498db'}}; color: white;">
                        ${{college.name}}
                    </h4>
                    <div style="padding: 10px;">
                        <p><strong>Type:</strong> ${{college.type}}</p>
                        <p><strong>State:</strong> ${{college.state}}</p>
                        <p><strong>Status:</strong> ${{college.status || 'N/A'}}</p>
                    </div>
                </div>
            `;
            
            marker.bindPopup(popupContent);
            marker.addTo(map);
            markers.push(marker);
        }});
    }}
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', initMap);
    </script>
    """
    
    # Add filter panel and JavaScript to map
    m.get_root().html.add_child(folium.Element(filter_html))
    m.get_root().script.add_child(folium.Element(filter_js))
    
    return m

def main():
    """Main function to create and save the map"""
    # Read the geocoded colleges data
    project_dir = Path(__file__).resolve().parents[2]
    data_file = project_dir / 'data' / 'processed' / 'geocoded_colleges.csv'
    output_dir = project_dir / 'docs'
    output_dir.mkdir(exist_ok=True)
    
    print("Reading data from:", data_file)
    df = pd.read_csv(data_file)
    print(f"Total colleges in dataset: {len(df)}")
    print(f"Colleges with valid coordinates: {len(df.dropna(subset=['latitude', 'longitude']))}")
    
    # Create and save the map
    m = create_enhanced_map(df)
    
    # Save to docs directory for GitHub Pages
    docs_output = output_dir / 'enhanced_college_map.html'
    m.save(str(docs_output))
    print(f"\nMap saved to: {docs_output}")
    
    # Also save to project root for easy access
    root_output = project_dir / 'college_map.html'
    m.save(str(root_output))
    print(f"Map saved to: {root_output}")
    
    print(f"\nTotal colleges on map: {len(df.dropna(subset=['latitude', 'longitude']))}")
    print("\nTry opening the map in Chrome or Firefox if Safari has issues loading it.")

if __name__ == "__main__":
    main()
