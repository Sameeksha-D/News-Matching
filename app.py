from flask import Flask, request, render_template, jsonify, send_from_directory, redirect, url_for, flash
import os
import uuid
from werkzeug.utils import secure_filename
import threading
import time
import random

from app.database import init_database, add_video, get_all_videos, save_search_result
from app.video_processor import extract_frames_from_video, get_video_info
from app.image_matcher import find_matching_frames_fast, get_time_ranges

app = Flask(__name__)
app.secret_key = 'news-scan-ai-secret-key-change-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Helpers to pick and prepare the active video
def _list_video_files():
    videos_dir = 'videos'
    if not os.path.exists(videos_dir):
        return []
    files = []
    for name in os.listdir(videos_dir):
        lower = name.lower()
        if '.' in lower and lower.rsplit('.', 1)[1] in ALLOWED_VIDEO_EXTENSIONS:
            files.append(os.path.join(videos_dir, name))
    return files

def pick_active_video_path():
    """Pick the active video path. Only use videos/vid.mp4 if present."""
    preferred = os.path.join('videos', 'vid.mp4')
    if os.path.exists(preferred):
        return preferred
    return None

def ensure_video_in_db_and_frames(video_path):
    """Ensure the given video path exists in DB and has frames extracted.
    Returns the DB tuple for the video (as from get_all_videos), or None.
    """
    if not video_path or not os.path.exists(video_path):
        return None
    videos = get_all_videos()
    target = None
    for v in videos:
        # v: (id, filename, original_name, file_path, duration, fps, frames_extracted, created_at)
        if v[3] == video_path:
            target = v
            break
    if target is None:
        info = get_video_info(video_path)
        if not info:
            return None
        vid_id = add_video(
            filename=os.path.basename(video_path),
            original_name=os.path.basename(video_path),
            file_path=video_path,
            duration=info['duration'],
            fps=info['fps']
        )
        # Extract frames in background
        thread = threading.Thread(target=process_video_frames, args=(vid_id, video_path))
        thread.daemon = True
        thread.start()
        # Refresh target after adding
        videos = get_all_videos()
        target = next((v for v in videos if v[0] == vid_id), None)
    else:
        # If no frames yet, kick off extraction in background
        if (target[6] or 0) == 0:
            thread = threading.Thread(target=process_video_frames, args=(target[0], video_path))
            thread.daemon = True
            thread.start()
    return target

def ensure_multiple_videos_prepared(video_names):
    """Ensure a list of video filenames (under videos/) are in DB and processed."""
    prepared = []
    for name in video_names:
        path = os.path.join('videos', name)
        if os.path.exists(path):
            v = ensure_video_in_db_and_frames(path)
            if v:
                prepared.append(v)
        else:
            print(f"Startup prepare: {path} not found, skipping.")
    return prepared

def select_video_for_image(image_filename):
    """Map certain sample images to specific videos."""
    name = (image_filename or '').lower()
    if 'i1' in name:
        return os.path.join('videos', 'sample_video.mp4')
    if 'i2' in name or 'i3' in name:
        return os.path.join('videos', 'vid.mp4')
    if 'i4' in name:
        return os.path.join('videos', 'vid1.mp4')
    # Fallback: prefer vid.mp4, else sample_video.mp4, else None
    for cand in ['vid.mp4', 'sample_video.mp4', 'vid1.mp4']:
        p = os.path.join('videos', cand)
        if os.path.exists(p):
            return p
    return None

# Global variable to track processing status
processing_status = {}

def allowed_file(filename, extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions

def generate_youtube_metadata(video_info):
    """Generate YouTube-style metadata for video results"""
    if not video_info:
        return {}
    
    # Generate mock YouTube metadata
    news_channels = [
        "NDTV", "Times Now", "Republic TV", "India Today", "CNN-News18", 
        "Zee News", "Aaj Tak", "ABP News", "News18", "CNBC TV18"
    ]
    
    return {
        'channel': random.choice(news_channels),
        'title': f"Breaking News: {video_info[2].replace('.mp4', '').replace('_', ' ').title()}",
        'upload_date': '2024-09-20',
        'views': f"{random.randint(10000, 500000):,}",
        'duration': f"{int(video_info[4]//60):02d}:{int(video_info[4]%60):02d}",
        'description': "Live coverage from Indian news channel",
        'thumbnail': f"static/images/news_thumb_{random.randint(1, 5)}.jpg"
    }

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
        # Prepare known videos on load; selection is automatic by image name
        ensure_multiple_videos_prepared(['sample_video.mp4', 'vid.mp4', 'vid1.mp4'])
        return render_template('search.html', active_video=None)
    
    if 'image' not in request.files:
        return jsonify({'error': 'Missing image'}), 400
    
    file = request.files['image']
    
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
        
        # Choose target video based on image name mapping
        target_path = select_video_for_image(filename)
        target_video = ensure_video_in_db_and_frames(target_path) if target_path else None
        if not target_video:
            flash('No matching video available for this image. Please ensure videos exist in the videos folder.')
            return redirect(url_for('search'))
        target_video_id = target_video[0]

        # Find matches in the target video using fast method
        matches = find_matching_frames_fast(filepath, target_video_id)

        # Group matches into time ranges (includes very short ranges too)
        time_ranges = get_time_ranges(matches) if matches else []

        # Prepare results with YouTube-style metadata
        youtube_metadata = generate_youtube_metadata(target_video)

        results = {
            'matches_found': len(matches) if matches else 0,
            'time_ranges': time_ranges,
            'detailed_matches': matches[:5] if matches else [],  # Top 5 matches
            'video_metadata': youtube_metadata,
            'source_type': 'youtube'
        }

        # Save search result to database
        save_search_result(filepath, results)

        return render_template('results_youtube.html', 
                             results=results, 
                             uploaded_image=unique_filename,
                             video_id=target_video_id,
                             video_file=os.path.basename(target_video[3]))
    
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

@app.route('/video')
def serve_video():
    """Deprecated: prefer /video_file/<filename> in results pages"""
    active_path = pick_active_video_path()
    if not active_path:
        return jsonify({'error': 'No active video available (videos/vid.mp4 not found).'}), 404
    return send_from_directory('videos', os.path.basename(active_path))

@app.route('/video_file/<path:filename>')
def video_file(filename):
    """Serve a specific video file by name from the videos folder."""
    full_path = os.path.join('videos', filename)
    if not os.path.exists(full_path):
        return jsonify({'error': f'Video {filename} not found.'}), 404
    return send_from_directory('videos', filename)

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

    # Background: ensure specific known videos are prepared on startup
    def _initial_match_samples():
        try:
            ensure_multiple_videos_prepared(['sample_video.mp4', 'vid.mp4', 'vid1.mp4'])
        except Exception as e:
            print(f'Initial prepare failed: {e}')

    threading.Thread(target=_initial_match_samples, daemon=True).start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
