from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import threading
from datetime import datetime

app = Flask(__name__)
# Enable CORS for all routes, allowing all origins.
# This is necessary for the Figma plugin to communicate with the local server.
CORS(app, resources={r"/*": {"origins": "*"}})

# Global storage for JSON data (in production, use a database)
data_store = {}
data_lock = threading.Lock()

# File path for persistent storage
DATA_FILE = 'figma_data.json'

def save_data_to_file():
    """Save current data store to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data_store, f, indent=2)

def load_data_from_file():
    """Load data from file on startup"""
    global data_store
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data_store = json.load(f)
        except Exception as e:
            print(f"Error loading data file: {e}")
            data_store = {}

@app.route('/send_data', methods=['POST'])
def send_data():
    """Receive JSON data from Figma plugin"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Generate a unique ID for this dataset
        timestamp = datetime.now().isoformat()
        data_id = f"figma_export_{timestamp.replace(':', '-').replace('.', '-')}"
        
        # Store the data with metadata
        with data_lock:
            data_store[data_id] = {
                'timestamp': timestamp,
                'data': data,
                'status': 'received'
            }
            save_data_to_file()
        
        print(f"Received data with ID: {data_id}")
        print(f"Data contains {len(data.get('elements', []))} elements")
        
        return jsonify({
            'success': True, 
            'data_id': data_id,
            'message': f'Data received successfully with {len(data.get("elements", []))} elements'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error processing data: {str(e)}'}), 500

@app.route('/get_data', methods=['GET'])
def get_data():
    """Retrieve JSON data for DaVinci Resolve script"""
    try:
        data_id = request.args.get('id')
        
        with data_lock:
            if data_id:
                # Get specific dataset by ID
                if data_id in data_store:
                    return jsonify({
                        'success': True,
                        'data': data_store[data_id]['data'],
                        'metadata': {
                            'id': data_id,
                            'timestamp': data_store[data_id]['timestamp'],
                            'status': data_store[data_id]['status']
                        }
                    }), 200
                else:
                    return jsonify({'error': f'No data found for ID: {data_id}'}), 404
            else:
                # Get the most recent dataset
                if not data_store:
                    return jsonify({'error': 'No data available'}), 404
                
                # Find the most recent entry
                latest_id = max(data_store.keys(), key=lambda k: data_store[k]['timestamp'])
                latest_data = data_store[latest_id]
                
                return jsonify({
                    'success': True,
                    'data': latest_data['data'],
                    'metadata': {
                        'id': latest_id,
                        'timestamp': latest_data['timestamp'],
                        'status': latest_data['status']
                    }
                }), 200
                
    except Exception as e:
        return jsonify({'error': f'Error retrieving data: {str(e)}'}), 500

@app.route('/list_data', methods=['GET'])
def list_data():
    """List all available datasets"""
    with data_lock:
        datasets = []
        for data_id, data_info in data_store.items():
            datasets.append({
                'id': data_id,
                'timestamp': data_info['timestamp'],
                'status': data_info['status'],
                'element_count': len(data_info['data'].get('elements', []))
            })
        
        # Sort by timestamp, newest first
        datasets.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'datasets': datasets,
            'count': len(datasets)
        }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'stored_datasets': len(data_store)
    }), 200

if __name__ == '__main__':
    # Load existing data on startup
    load_data_from_file()
    
    print("Starting Figma-DaVinci Bridge Server...")
    print("Endpoints:")
    print("  POST /send_data - Receive data from Figma")
    print("  GET  /get_data  - Retrieve data for DaVinci")
    print("  GET  /list_data - List all datasets")
    print("  GET  /health    - Health check")
    print("\nServer running on http://localhost:5000")
    
    app.run(host='localhost', port=5000, debug=True)
