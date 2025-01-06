from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

# Load college data
def load_college_data():
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'landmarks.json')
    with open(data_path, 'r') as f:
        return json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/colleges')
def get_colleges():
    colleges = load_college_data()
    return jsonify(colleges)

if __name__ == '__main__':
    app.run(debug=True)
