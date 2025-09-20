import cv2
import os
import hashlib
from app.database import add_frame, update_video_frames_count

def extract_frames_from_video(video_path, video_id, output_dir, frame_interval=30):
    """
    Extract frames from video at specified intervals
    
    Args:
        video_path: Path to the video file
        video_id: Database ID of the video
        output_dir: Directory to save extracted frames
        frame_interval: Extract every N frames (default: 30 = 1 frame per second at 30fps)
    
    Returns:
        Number of frames extracted
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return 0
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frame_count = 0
    extracted_count = 0
    
    print(f"Processing video: FPS={fps}, Total frames={total_frames}")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Extract frame at specified intervals
        if frame_count % frame_interval == 0:
            timestamp = frame_count / fps
            frame_filename = f"video_{video_id}_frame_{extracted_count:06d}.jpg"
            frame_path = os.path.join(output_dir, frame_filename)
            
            # Save frame
            cv2.imwrite(frame_path, frame)
            
            # Generate a simple feature hash (you can improve this with better feature extraction)
            feature_hash = generate_frame_hash(frame)
            
            # Add frame to database
            add_frame(video_id, frame_count, timestamp, frame_path, feature_hash)
            
            extracted_count += 1
            
            if extracted_count % 100 == 0:
                print(f"Extracted {extracted_count} frames...")
        
        frame_count += 1
    
    cap.release()
    
    # Update video frames count in database
    update_video_frames_count(video_id, extracted_count)
    
    print(f"Extraction complete: {extracted_count} frames extracted")
    return extracted_count

def generate_frame_hash(frame):
    """Generate a simple hash for frame comparison"""
    # Resize frame for consistent hashing
    resized = cv2.resize(frame, (64, 64))
    # Convert to grayscale
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    # Create hash
    return hashlib.md5(gray.tobytes()).hexdigest()

def get_video_info(video_path):
    """Get basic information about a video file"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    cap.release()
    
    return {
        'fps': fps,
        'frame_count': frame_count,
        'duration': duration,
        'width': width,
        'height': height
    }

def extract_single_frame(video_path, timestamp):
    """Extract a single frame at a specific timestamp"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_number = int(timestamp * fps)
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    cap.release()
    
    return frame if ret else None
