# CollegeLinks: Interactive College Location Map

An interactive geographical visualization of college locations across India with advanced filtering capabilities.

## Features

- Interactive map visualization of colleges across India
- Clustered markers for better performance
- Detailed college information in popups
- Advanced filtering by:
  - College name search
  - State selection
  - Institution type
- Real-time updates of filtered results
- College count display

## Tech Stack

- **Backend**: Python 3.11
- **Libraries**:
  - Folium (mapping)
  - Pandas (data handling)
  - NumPy (numerical operations)
- **Frontend**:
  - JavaScript
  - jQuery 3.6.0
  - Select2 (advanced filtering)
  - Leaflet.js (via Folium)
- **Styling**: CSS

## Project Structure

```
collegelinks_fresh/
├── data/
│   └── processed/
│       └── geocoded_colleges.csv
├── docs/
│   └── planning/
├── src/
│   └── visualization/
│       └── simple_map.py
└── requirements.txt
```

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd collegelinks_fresh
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
cd src/visualization
python simple_map.py
```

5. Open the generated map:
```
docs/simple_college_map.html
```

## Data Source

The project uses a preprocessed dataset of Indian colleges (`geocoded_colleges.csv`) containing:
- College names
- Geographic coordinates
- Institution types
- States
- UGC recognition status
- Additional institutional details

## Features in Development

- Enhanced filtering functionality
- Performance optimization for large datasets
- Mobile responsiveness
- Cross-browser compatibility testing
- Advanced search capabilities

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Data source: [Add source information]
- Mapping library: Folium
- Clustering functionality: Leaflet.markercluster
