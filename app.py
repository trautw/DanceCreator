from flask import Flask, send_from_directory, request, jsonify, abort
import os
import json
from pathlib import Path

app = Flask(__name__, static_folder='static', static_url_path='')
FIG_DIR = Path('Figures')
FIG_DIR.mkdir(exist_ok=True)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/list', methods=['GET'])
def list_files():
    files = [p.name for p in FIG_DIR.glob('*.json')]
    return jsonify(files)

@app.route('/api/save', methods=['POST'])
def save_figure():
    data = request.get_json()
    if not data or 'Name' not in data:
        return jsonify({'error': 'Invalid payload, requires JSON with Name field.'}), 400
    filename = request.args.get('filename', data.get('Name'))
    safe_name = ''.join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
    path = FIG_DIR / f"{safe_name}.json"
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'ok': True, 'filename': path.name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load', methods=['GET'])
def load_figure():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error': 'filename query param required'}), 400
    path = FIG_DIR / filename
    if not path.exists():
        return jsonify({'error': 'file not found'}), 404
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ping')
def ping():
    return jsonify({'ping': 'pong'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
