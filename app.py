from flask import Flask, request, render_template, jsonify, send_from_directory, redirect, url_for, flash
import os
import uuid
from werkzeug.utils import secure_filename
import threading
import time

from app.database import init_database, add_video, get_all_videos, save_search_result
from app.video_processor import extract_frames_from_video, get_video_info
from app.image_matcher import find_matching_frames, get_time_ranges

app = Flask(__name__)
app.secret_key = 'news-scan-ai-secret-key-change-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Global variable to track processing status
processing_status = {}

def allowed_file(filename, extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions

def process_video_frames(video_id, video_path):
    """Process video frames in background"""
    global processing_status
    processing_status[video_id] = {'status': 'processing', 'progress': 0}
    
    try:
        frames_dir = f'frames/video_{video_id}'
        frames_extracted = extract_frames_from_video(video_path, video_id, frames_dir)
        processing_status[video_id] = {'status': 'completed', 'progress': 100, 'frames': frames_extracted}
    except Exception as e:
        processing_status[video_id] = {'status': 'error', 'error': str(e)}

@app.route('/')
def index():
    """Main page"""
    videos = get_all_videos()
    return render_template('index.html', videos=videos)

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """Handle video upload"""
    if 'video' not in request.files:
        flash('No video file selected')
        return redirect(request.url)
    
    file = request.files['video']
    if file.filename == '':
        flash('No video file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join('videos', unique_filename)
        
        # Ensure videos directory exists
        os.makedirs('videos', exist_ok=True)
        
        file.save(filepath)
        
        # Get video info
        video_info = get_video_info(filepath)
        
        if video_info:
            # Add to database
            video_id = add_video(
                filename=unique_filename,
                original_name=filename,
                file_path=filepath,
                duration=video_info['duration'],
                fps=video_info['fps']
            )
            
            # Start processing frames in background
            thread = threading.Thread(target=process_video_frames, args=(video_id, filepath))
            thread.daemon = True
            thread.start()
            
            flash(f'Video uploaded successfully! Processing frames in background...')
        else:
            flash('Error reading video file')
    else:
        flash('Invalid video file format')
    
    return redirect(url_for('index'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Image search page"""
    if request.method == 'GET':
        videos = get_all_videos()
        return render_template('search.html', videos=videos)
    
    if 'image' not in request.files or 'video_id' not in request.form:
        return jsonify({'error': 'Missing image or video selection'}), 400
    
    file = request.files['image']
    video_id = request.form['video_id']
    
    if file.filename == '':
        return jsonify({'error': 'No image file selected'}), 400
    
    if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
        return jsonify({'error': 'Invalid image file format'}), 400
    
    try:
        # Save uploaded image
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)
        
        # Find matching frames
        matches = find_matching_frames(filepath, int(video_id))
        
        if matches:
            # Group matches into time ranges
            time_ranges = get_time_ranges(matches)
            
            # Prepare results
            results = {
                'matches_found': len(matches),
                'time_ranges': time_ranges,
                'detailed_matches': matches[:10]  # Return top 10 matches
            }
            
            # Save search result to database
            save_search_result(filepath, results)
            
            return render_template('results.html', 
                                 results=results, 
                                 uploaded_image=unique_filename,
                                 video_id=video_id)
        else:
            return render_template('results.html', 
                                 results={'matches_found': 0, 'time_ranges': []},
                                 uploaded_image=unique_filename,
                                 video_id=video_id)
    
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/video_status/<int:video_id>')
def video_status(video_id):
    """Check video processing status"""
    status = processing_status.get(video_id, {'status': 'not_found'})
    return jsonify(status)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/frames/<path:filename>')
def frame_file(filename):
    """Serve frame files"""
    return send_from_directory('frames', filename)

@app.route('/static/images/<filename>')
def static_image(filename):
    """Serve static image files"""
    return send_from_directory('static/images', filename)

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for image search"""
    if 'image' not in request.files or 'video_id' not in request.form:
        return jsonify({'error': 'Missing image or video selection'}), 400
    
    file = request.files['image']
    video_id = request.form['video_id']
    
    if file.filename == '':
        return jsonify({'error': 'No image file selected'}), 400
    
    try:
        # Save uploaded image
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)
        
        # Find matching frames
        matches = find_matching_frames(filepath, int(video_id))
        
        # Group matches into time ranges
        time_ranges = get_time_ranges(matches)
        
        results = {
            'success': True,
            'matches_found': len(matches),
            'time_ranges': time_ranges,
            'uploaded_image': unique_filename
        }
        
        # Save search result
        save_search_result(filepath, results)
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('videos', exist_ok=True)
    os.makedirs('frames', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
