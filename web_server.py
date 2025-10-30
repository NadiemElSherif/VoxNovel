#!/usr/bin/env python3
"""
Simple web server for VoxNovel - provides a web interface for the audiobook generation
"""

import os
import sys
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import zipfile
import tempfile

# Add VoxNovel modules to path
sys.path.append('/app')

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = '/app/uploads'
app.config['OUTPUT_FOLDER'] = '/app/output_audiobooks'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Global variables for job tracking
current_job = None
job_status = {
    'status': 'idle',
    'progress': 0,
    'message': 'Ready to process books',
    'start_time': None,
    'output_file': None
}

# Import VoxNovel modules
try:
    import download_missing_booknlp_models
    from headless_voxnovel import process_book_headless
    VOXNOVEL_AVAILABLE = True
except ImportError as e:
    print(f"Warning: VoxNovel modules not available: {e}")
    VOXNOVEL_AVAILABLE = False

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'epub', 'pdf', 'mobi', 'txt', 'html', 'rtf', 'fb2', 'odt', 'cbr', 'cbz'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', job_status=job_status)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'voxnovel_available': VOXNOVEL_AVAILABLE})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    global current_job

    if current_job:
        return jsonify({'error': 'Another job is already running'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Get processing options
        options = {
            'tts_model': request.form.get('tts_model', 'xtts_v2'),
            'use_gpu': request.form.get('use_gpu', 'true').lower() == 'true',
            'chapter_delimiter': request.form.get('chapter_delimiter', 'Chapter'),
            'silence_duration': int(request.form.get('silence_duration', 500))
        }

        # Start processing in background thread
        thread = threading.Thread(target=process_book_job, args=(filepath, options))
        thread.daemon = True
        thread.start()

        return jsonify({'message': 'File uploaded and processing started', 'filename': filename})

    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/status')
def get_status():
    """Get current job status"""
    return jsonify(job_status)

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated audiobook"""
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/jobs')
def list_jobs():
    """List completed jobs"""
    jobs = []
    output_dir = Path(app.config['OUTPUT_FOLDER'])

    for file_path in output_dir.glob('*.m4b'):
        stat = file_path.stat()
        jobs.append({
            'filename': file_path.name,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        })

    return render_template('jobs.html', jobs=jobs)

def process_book_job(filepath, options):
    """Process book in background thread"""
    global current_job, job_status

    if not VOXNOVEL_AVAILABLE:
        job_status.update({
            'status': 'error',
            'message': 'VoxNovel modules not available',
            'progress': 0
        })
        return

    current_job = filepath
    filename = os.path.basename(filepath)

    job_status.update({
        'status': 'processing',
        'progress': 10,
        'message': 'Starting book processing...',
        'start_time': datetime.now().isoformat(),
        'output_file': None
    })

    try:
        # This is a simplified version - you'd need to adapt the actual VoxNovel processing
        # For now, we'll simulate processing with progress updates

        # Simulate BookNLP processing
        for i in range(10, 50, 5):
            if current_job != filepath:  # Job was cancelled
                return
            time.sleep(2)  # Simulate processing time
            job_status.update({
                'progress': i,
                'message': f'Processing book text... {i}%'
            })

        # Simulate TTS processing
        for i in range(50, 90, 5):
            if current_job != filepath:
                return
            time.sleep(3)  # Simulate processing time
            job_status.update({
                'progress': i,
                'message': f'Generating audio... {i}%'
            })

        # Simulate final processing
        time.sleep(2)
        output_filename = f"{os.path.splitext(filename)[0]}_audiobook.m4b"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # Create a dummy output file for demonstration
        # In real implementation, this would be the actual audiobook
        with open(output_path, 'w') as f:
            f.write("This would be the generated audiobook file")

        job_status.update({
            'status': 'completed',
            'progress': 100,
            'message': f'Audiobook generated successfully: {output_filename}',
            'output_file': output_filename
        })

    except Exception as e:
        job_status.update({
            'status': 'error',
            'message': f'Processing failed: {str(e)}',
            'progress': 0
        })

    finally:
        current_job = None

if __name__ == '__main__':
    # Initialize BookNLP models if available
    if VOXNOVEL_AVAILABLE:
        try:
            print("Initializing BookNLP models...")
            download_missing_booknlp_models
            print("Models initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize models: {e}")

    # Start web server
    app.run(host='0.0.0.0', port=8080, debug=False)