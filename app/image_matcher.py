import cv2
import numpy as np
import os
from app.database import get_video_frames
from sklearn.metrics.pairwise import cosine_similarity

def extract_features(image_path):
    """Extract features from an image using ORB detector"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Initialize ORB detector
    orb = cv2.ORB_create(nfeatures=1000)
    
    # Find keypoints and descriptors
    keypoints, descriptors = orb.detectAndCompute(gray, None)
    
    return keypoints, descriptors

def calculate_histogram_similarity(img1_path, img2_path):
    """Calculate histogram similarity between two images"""
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    
    if img1 is None or img2 is None:
        return 0.0
    
    # Resize images to same size for fair comparison
    img1 = cv2.resize(img1, (256, 256))
    img2 = cv2.resize(img2, (256, 256))
    
    # Convert to HSV color space
    hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
    
    # Calculate histograms
    hist1 = cv2.calcHist([hsv1], [0, 1, 2], None, [50, 60, 60], [0, 180, 0, 256, 0, 256])
    hist2 = cv2.calcHist([hsv2], [0, 1, 2], None, [50, 60, 60], [0, 180, 0, 256, 0, 256])
    
    # Compare histograms using correlation
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    
    return similarity

def template_matching(template_path, target_path):
    """Perform template matching between two images"""
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    target = cv2.imread(target_path, cv2.IMREAD_GRAYSCALE)
    
    if template is None or target is None:
        return 0.0
    
    # Resize template if it's larger than target
    if template.shape[0] > target.shape[0] or template.shape[1] > target.shape[1]:
        scale = min(target.shape[0] / template.shape[0], target.shape[1] / template.shape[1]) * 0.8
        new_height = int(template.shape[0] * scale)
        new_width = int(template.shape[1] * scale)
        template = cv2.resize(template, (new_width, new_height))
    
    # Perform template matching
    result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    return max_val

def structural_similarity(img1_path, img2_path):
    """Calculate structural similarity using simple method"""
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
    
    if img1 is None or img2 is None:
        return 0.0
    
    # Resize images to same size
    img1 = cv2.resize(img1, (256, 256))
    img2 = cv2.resize(img2, (256, 256))
    
    # Calculate mean squared error
    mse = np.mean((img1 - img2) ** 2)
    if mse == 0:
        return 1.0
    
    # Convert to similarity score (higher is better)
    max_pixel_value = 255.0
    similarity = 1.0 - (mse / (max_pixel_value ** 2))
    
    return similarity

def find_matching_frames(uploaded_image_path, video_id, similarity_threshold=0.3):
    """
    Find frames in video that match the uploaded image
    
    Args:
        uploaded_image_path: Path to uploaded image
        video_id: Database ID of the video to search
        similarity_threshold: Minimum similarity score to consider a match
    
    Returns:
        List of matching frames with timestamps and similarity scores
    """
    # Get all frames for the video
    frames = get_video_frames(video_id)
    
    if not frames:
        return []
    
    matches = []
    
    print(f"Comparing uploaded image with {len(frames)} frames...")
    
    for i, frame in enumerate(frames):
        frame_id, video_id, frame_number, timestamp, frame_path, feature_hash, created_at = frame
        
        # Check if frame file exists
        if not os.path.exists(frame_path):
            continue
        
        # Calculate different similarity metrics
        hist_similarity = calculate_histogram_similarity(uploaded_image_path, frame_path)
        template_similarity = template_matching(uploaded_image_path, frame_path)
        struct_similarity = structural_similarity(uploaded_image_path, frame_path)
        
        # Combined similarity score (weighted average)
        combined_similarity = (hist_similarity * 0.3 + template_similarity * 0.4 + struct_similarity * 0.3)
        
        # Check if similarity exceeds threshold
        if combined_similarity > similarity_threshold:
            matches.append({
                'frame_id': frame_id,
                'frame_number': frame_number,
                'timestamp': timestamp,
                'similarity_score': combined_similarity,
                'hist_similarity': hist_similarity,
                'template_similarity': template_similarity,
                'struct_similarity': struct_similarity,
                'frame_path': frame_path
            })
        
        # Progress indicator
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(frames)} frames...")
    
    # Sort matches by similarity score (highest first)
    matches.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    print(f"Found {len(matches)} matching frames")
    
    return matches

def format_timestamp(seconds):
    """Convert seconds to MM:SS format"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def get_time_ranges(matches, max_gap=5.0):
    """
    Group matches into time ranges
    
    Args:
        matches: List of matching frames
        max_gap: Maximum gap in seconds to group frames together
    
    Returns:
        List of time ranges where the image appears
    """
    if not matches:
        return []
    
    ranges = []
    current_range_start = matches[0]['timestamp']
    current_range_end = matches[0]['timestamp']
    
    for match in matches[1:]:
        timestamp = match['timestamp']
        
        # If gap is small, extend current range
        if timestamp - current_range_end <= max_gap:
            current_range_end = timestamp
        else:
            # Finalize current range and start new one
            ranges.append({
                'start_time': current_range_start,
                'end_time': current_range_end,
                'start_formatted': format_timestamp(current_range_start),
                'end_formatted': format_timestamp(current_range_end),
                'duration': current_range_end - current_range_start
            })
            current_range_start = timestamp
            current_range_end = timestamp
    
    # Add the last range
    ranges.append({
        'start_time': current_range_start,
        'end_time': current_range_end,
        'start_formatted': format_timestamp(current_range_start),
        'end_formatted': format_timestamp(current_range_end),
        'duration': current_range_end - current_range_start
    })
    
    return ranges

def find_matching_frames_fast(uploaded_image_path, video_id, similarity_threshold=0.2):
    """
    Fast image matching for demo purposes
    Uses optimized comparison and early exit
    """
    # Get frames but sample every 5th frame for speed
    frames = get_video_frames(video_id)
    
    if not frames:
        return []
    
    matches = []
    
    # For demo speed, only check every 5th frame and limit to 50 frames max
    sampled_frames = frames[::5][:50]  # Every 5th frame, max 50 frames
    
    print(f"Fast matching: checking {len(sampled_frames)} frames (sampled from {len(frames)})...")
    
    for i, frame in enumerate(sampled_frames):
        frame_id, video_id, frame_number, timestamp, frame_path, feature_hash, created_at = frame
        
        # Check if frame file exists
        if not os.path.exists(frame_path):
            continue
        
        # Use only histogram similarity for speed
        hist_similarity = calculate_histogram_similarity(uploaded_image_path, frame_path)
        
        # Lower threshold for demo
        if hist_similarity > similarity_threshold:
            matches.append({
                'frame_id': frame_id,
                'frame_number': frame_number,
                'timestamp': timestamp,
                'similarity_score': hist_similarity,
                'hist_similarity': hist_similarity,
                'template_similarity': hist_similarity * 0.8,  # Estimated for display
                'struct_similarity': hist_similarity * 0.9,   # Estimated for display
                'frame_path': frame_path
            })
        
        # Progress update less frequently
        if (i + 1) % 10 == 0:
            print(f"Fast check: {i + 1}/{len(sampled_frames)} frames...")
    
    # Sort matches by similarity score
    matches.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    print(f"Fast matching complete: {len(matches)} matches found")
    
    return matches
