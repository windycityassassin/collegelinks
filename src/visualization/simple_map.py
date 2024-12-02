"""
Create a simple clustered map of colleges with search functionality and advanced filtering
"""
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import json

def create_simple_map():
    # Read the data
    df = pd.read_csv('/Users/apv/CascadeProjects/collegelinks_fresh/data/processed/geocoded_colleges.csv')
    
    # Clean and get unique values for filters
    df['state'] = df['state'].fillna('Unknown')
    df['institution_type'] = df['institution_type'].fillna('Unknown')
    
    # Convert postal code to integer format (removing .0)
    df['postal_code'] = df['postal_code'].fillna('Not Available')
    df.loc[df['postal_code'] != 'Not Available', 'postal_code'] = df.loc[df['postal_code'] != 'Not Available', 'postal_code'].astype(float).astype(int).astype(str)
    
    df['status'] = df['status'].fillna('Not Available')
    df['Affiliated To University'] = df['Affiliated To University'].fillna('')
    df['Year of Estb.'] = df['Year of Estb.'].fillna('')
    df['Teaching Upto'] = df['Teaching Upto'].fillna('')
    df['Govt or Non Govt'] = df['Govt or Non Govt'].fillna('')
    df['Aided or Unaided'] = df['Aided or Unaided'].fillna('')
    
    states = sorted(df['state'].unique().tolist())
    institution_types = sorted(df['institution_type'].unique().tolist())
    
    # Create a base map centered on India
    m = folium.Map(
        location=[20.5937, 78.9629],
        zoom_start=5,
        tiles='CartoDB positron'
    )
    
    # Create a marker cluster
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
    
    # Create a list to store college data for search
    college_data = []
    
    # Add markers for each college to the cluster
    for _, row in df.iterrows():
        try:
            lat = float(row['latitude'])
            lon = float(row['longitude'])
            
            if pd.isna(lat) or pd.isna(lon):
                continue
                
            # Create table rows for available data
            table_rows = []
            
            # Always show these fields
            table_rows.extend([
                f'''
                <tr>
                    <td style="padding: 5px; font-weight: bold;">Type:</td>
                    <td style="padding: 5px;">{row['institution_type']}</td>
                </tr>
                <tr style="background: #f9f9f9;">
                    <td style="padding: 5px; font-weight: bold;">State:</td>
                    <td style="padding: 5px;">{row['state']}</td>
                </tr>
                <tr>
                    <td style="padding: 5px; font-weight: bold;">Postal Code:</td>
                    <td style="padding: 5px;">{row['postal_code']}</td>
                </tr>
                <tr style="background: #f9f9f9;">
                    <td style="padding: 5px; font-weight: bold;">UGC Status:</td>
                    <td style="padding: 5px;">{row['status']}</td>
                </tr>'''
            ])
            
            # Optional fields - only add if they have values
            if row['Affiliated To University']:
                table_rows.append(f'''
                <tr>
                    <td style="padding: 5px; font-weight: bold;">Affiliated To:</td>
                    <td style="padding: 5px;">{row['Affiliated To University']}</td>
                </tr>''')
                
            if row['Year of Estb.']:
                table_rows.append(f'''
                <tr style="background: #f9f9f9;">
                    <td style="padding: 5px; font-weight: bold;">Established:</td>
                    <td style="padding: 5px;">{row['Year of Estb.']}</td>
                </tr>''')
                
            if row['Teaching Upto']:
                table_rows.append(f'''
                <tr>
                    <td style="padding: 5px; font-weight: bold;">Teaching Level:</td>
                    <td style="padding: 5px;">{row['Teaching Upto']}</td>
                </tr>''')
                
            if row['Govt or Non Govt']:
                table_rows.append(f'''
                <tr style="background: #f9f9f9;">
                    <td style="padding: 5px; font-weight: bold;">Category:</td>
                    <td style="padding: 5px;">{row['Govt or Non Govt']}</td>
                </tr>''')
                
            if row['Aided or Unaided']:
                table_rows.append(f'''
                <tr>
                    <td style="padding: 5px; font-weight: bold;">Funding:</td>
                    <td style="padding: 5px;">{row['Aided or Unaided']}</td>
                </tr>''')
            
            # Create popup content
            popup_content = f"""
            <div style="min-width: 300px; max-width: 400px; font-family: Arial, sans-serif;">
                <h4 style="margin: 0; padding: 10px; background: #2c3e50; color: white;">
                    {row['name']}
                </h4>
                <div style="padding: 10px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        {''.join(table_rows)}
                    </table>
                </div>
            </div>
            """
            
            # Store college data for search
            college_data.append({
                'name': row['name'],
                'lat': lat,
                'lng': lon,
                'type': row['institution_type'],
                'state': row['state'],
                'popup': popup_content
            })
            
            # Add marker to cluster
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=400),
                tooltip=row['name']
            ).add_to(marker_cluster)
            
        except (ValueError, TypeError) as e:
            continue

    # Add filter control
    filter_html = f"""
    <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
    
    <style>
    .filter-container {{
        position: absolute;
        top: 10px;
        left: 50px;
        z-index: 1000;
        background: white;
        padding: 15px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        width: 300px;
    }}
    .filter-section {{
        margin-bottom: 10px;
    }}
    .filter-section label {{
        display: block;
        margin-bottom: 5px;
        font-weight: bold;
        color: #333;
    }}
    .filter-section select {{
        width: 100%;
        margin-bottom: 10px;
    }}
    .search-input {{
        width: 100%;
        padding: 8px;
        margin-bottom: 10px;
        border: 1px solid #ccc;
        border-radius: 4px;
        box-sizing: border-box;
    }}
    .filter-buttons {{
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
    }}
    .filter-button {{
        padding: 8px 15px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: bold;
    }}
    .apply-filters {{
        background-color: #2c3e50;
        color: white;
    }}
    .reset-filters {{
        background-color: #95a5a6;
        color: white;
    }}
    .college-count {{
        margin-top: 10px;
        text-align: center;
        color: #666;
    }}
    </style>

    <div class="filter-container">
        <div class="filter-section">
            <input type="text" id="college-search" class="search-input" placeholder="Search college name...">
        </div>
        
        <div class="filter-section">
            <label>State</label>
            <select id="state-filter" multiple="multiple">
                {' '.join([f'<option value="{state}">{state}</option>' for state in states])}
            </select>
        </div>
        
        <div class="filter-section">
            <label>Institution Type</label>
            <select id="type-filter" multiple="multiple">
                {' '.join([f'<option value="{type_}">{type_}</option>' for type_ in institution_types])}
            </select>
        </div>
        
        <div class="filter-buttons">
            <button class="filter-button reset-filters" id="reset-filters">Reset</button>
            <button class="filter-button apply-filters" id="apply-filters">Apply Filters</button>
        </div>
        
        <div class="college-count">
            Showing <span id="visible-count">0</span> of <span id="total-count">0</span> colleges
        </div>
    </div>

    <script>
    $(document).ready(function() {{
        // Initialize Select2 for multiple select dropdowns
        $('#state-filter, #type-filter').select2({{
            placeholder: "Select options...",
            allowClear: true,
            width: '100%'
        }});
        
        // Store the original college data
        var colleges = {json.dumps(college_data)};
        var totalColleges = colleges.length;
        var map = document.querySelector('#map')._leaflet_map;
        var markerCluster = null;
        
        // Initialize counts
        $('#total-count').text(totalColleges);
        $('#visible-count').text(totalColleges);
        
        function createMarkers(filteredColleges) {{
            // Clear existing markers
            if (markerCluster) {{
                map.removeLayer(markerCluster);
            }}
            
            // Create new marker cluster
            markerCluster = L.markerClusterGroup({{
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: true,
                zoomToBoundsOnClick: true
            }});
            
            // Add markers for filtered colleges
            filteredColleges.forEach(function(college) {{
                var marker = L.marker([college.lat, college.lng]);
                marker.bindPopup(college.popup);
                marker.bindTooltip(college.name);
                markerCluster.addLayer(marker);
            }});
            
            map.addLayer(markerCluster);
            $('#visible-count').text(filteredColleges.length);
        }}
        
        function applyFilters() {{
            var searchTerm = $('#college-search').val().toLowerCase();
            var selectedStates = $('#state-filter').val() || [];
            var selectedTypes = $('#type-filter').val() || [];
            
            var filteredColleges = colleges.filter(function(college) {{
                var matchesSearch = !searchTerm || college.name.toLowerCase().includes(searchTerm);
                var matchesState = selectedStates.length === 0 || selectedStates.includes(college.state);
                var matchesType = selectedTypes.length === 0 || selectedTypes.includes(college.type);
                
                return matchesSearch && matchesState && matchesType;
            }});
            
            createMarkers(filteredColleges);
        }}
        
        // Initial creation of markers
        createMarkers(colleges);
        
        // Event listeners
        $('#apply-filters').click(applyFilters);
        
        $('#reset-filters').click(function() {{
            $('#college-search').val('');
            $('#state-filter, #type-filter').val(null).trigger('change');
            createMarkers(colleges);
        }});
        
        // Instant search
        $('#college-search').on('input', function() {{
            applyFilters();
        }});
        
        // Apply filters when select2 values change
        $('#state-filter, #type-filter').on('change', function() {{
            applyFilters();
        }});
    }});
    </script>
    """

    # Add the filter control to the map
    m.get_root().html.add_child(folium.Element(filter_html))
    
    # Save the map
    output_path = '/Users/apv/CascadeProjects/collegelinks_fresh/docs/simple_college_map.html'
    m.save(output_path)
    print(f"Map saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    create_simple_map()
