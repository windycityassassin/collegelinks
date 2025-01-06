# CollegeLinks Project
An interactive map visualization platform for exploring colleges across India.

## Project Structure
```
collegelinks/
├── collegelinks/           # Main package directory
│   ├── __init__.py
│   ├── data_loader.py     # Data loading utilities
│   ├── data_processor_improved.py  # Data processing
│   ├── visualization.py   # Map visualization
│   └── address_processor.py # Address processing
├── data/                  # Data files
│   ├── raw/              # Original data files
│   └── processed/        # Processed data files
├── src/                  # Source code
│   ├── data_processing/  # Data processing modules
│   ├── geocoding/       # Geocoding implementation
│   ├── visualization/   # Visualization components
│   └── utils/          # Utility functions
├── tests/               # Test files
├── requirements.txt     # Project dependencies
└── README.md           # Project documentation
```

## Features
- Interactive map visualization of colleges across India
- Search functionality to find colleges by name
- Marker clustering for better visualization
- Color-coded markers based on college type
- Detailed popups with college information
- Full-screen map view

## Setup
1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Generate the interactive college map:
   ```bash
   python create_all_colleges_map.py
   ```

2. Features:
   - Use the search box in the top-left to find colleges by name
   - Click on markers to view college details
   - Use the full-screen button to expand the map
   - Zoom in/out to see marker clusters

## Dependencies
- folium: Map visualization
- pandas: Data processing
- numpy: Numerical operations
