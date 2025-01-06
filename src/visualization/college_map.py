"""
Generate an interactive map of all colleges in India
"""
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from pathlib import Path

def create_college_map(df):
    """Create an interactive map with all colleges"""
    
    # Create a base map centered on India
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
    
    # Create marker clusters for better performance
    marker_cluster = MarkerCluster().add_to(m)
    
    # Color scheme for different institution types
    colors = {
        'Private': 'red',
        'State': 'blue',
        'Central': 'green',
        'Deemed to be Universities': 'purple',
        'Colleges': 'orange'
    }
    
    # Add markers for each college
    for idx, row in df.iterrows():
        # Skip if no coordinates
        if pd.isna(row['latitude']) or pd.isna(row['longitude']):
            continue
            
        # Create popup content
        popup_content = f"""
            <b>{row['name']}</b><br>
            Type: {row['institution_type']}<br>
            Address: {row['address']}<br>
            State: {row['state']}<br>
            PIN: {row['postal_code'] if pd.notna(row['postal_code']) else 'N/A'}<br>
        """
        
        # Create marker
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color=colors.get(row['institution_type'], 'gray')),
        ).add_to(marker_cluster)
    
    # Add a legend
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border: 2px solid grey; border-radius: 5px;">
    <h4>Institution Types</h4>
    """
    for inst_type, color in colors.items():
        legend_html += f'<p><i class="fa fa-map-marker fa-2x" style="color:{color}"></i> {inst_type}</p>'
    legend_html += "</div>"
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def main():
    # Read the geocoded data
    data_path = Path(__file__).parent.parent.parent / 'data/processed/geocoded_colleges.csv'
    df = pd.read_csv(data_path)
    
    # Create the map
    m = create_college_map(df)
    
    # Save the map
    output_path = Path(__file__).parent.parent.parent / 'docs/college_map.html'
    m.save(str(output_path))
    print(f"Map generated at: {output_path}")

if __name__ == "__main__":
    main()
