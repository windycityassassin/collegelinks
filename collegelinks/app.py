from flask import Flask, jsonify, request
from .data_loader import DataLoader
from .schemas.college_profile import CollegeProfile
from .search.college_search import CollegeSearch
from .visualization.filtered_college_map import FilteredCollegeMap
import os

app = Flask(__name__)

# Initialize data loader
data_loader = DataLoader()
college_search = CollegeSearch()
map_visualizer = FilteredCollegeMap()

@app.route('/api/colleges', methods=['GET'])
def get_colleges():
    """Get a list of colleges with optional filtering"""
    try:
        # Get query parameters
        filters = request.args.to_dict()
        
        # Get colleges from data loader
        colleges = data_loader.get_colleges(filters)
        
        # Convert to dictionary format
        college_list = [college.dict() for college in colleges]
        
        return jsonify({
            'status': 'success',
            'data': college_list,
            'count': len(college_list)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/colleges/search', methods=['GET'])
def search_colleges():
    """Search colleges based on query parameters"""
    try:
        query = request.args.get('q', '')
        filters = request.args.to_dict()
        filters.pop('q', None)  # Remove query from filters
        
        results = college_search.search(query, filters)
        
        return jsonify({
            'status': 'success',
            'data': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/colleges/map', methods=['GET'])
def get_college_map():
    """Get map visualization data for colleges"""
    try:
        filters = request.args.to_dict()
        map_data = map_visualizer.generate_map(filters)
        
        return jsonify({
            'status': 'success',
            'data': map_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/colleges/stats', methods=['GET'])
def get_college_stats():
    """Get statistical information about the colleges dataset"""
    try:
        stats = data_loader.get_statistics()
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Load initial data
    data_loader.load_data()
    
    # Run the Flask app
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
