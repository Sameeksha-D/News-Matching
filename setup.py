#!/usr/bin/env python3
"""
Setup script for News-Scan-AI
Initializes database and adds sample video to the system
"""

import os
import sys
from app.database import init_database, add_video
from app.video_processor import get_video_info, extract_frames_from_video

def setup_database():
    """Initialize the database"""
    print("Initializing database...")
    init_database()
    print("✓ Database initialized")

def add_sample_video():
    """Add sample video to the database"""
    sample_video_path = "videos/sample_video.mp4"
    
    if not os.path.exists(sample_video_path):
        print(f"⚠ Sample video not found at {sample_video_path}")
        return None
    
    print("Adding sample video to database...")
    
    # Get video information
    video_info = get_video_info(sample_video_path)
    if not video_info:
        print("✗ Could not read sample video information")
        return None
    
    # Add video to database
    video_id = add_video(
        filename="sample_video.mp4",
        original_name="Election Commission Challenges Rahul Gandhi_s _Vote-Theft_ Allegations, Seeks Proof _ India Today.mp4",
        file_path=sample_video_path,
        duration=video_info['duration'],
        fps=video_info['fps']
    )
    
    print(f"✓ Sample video added to database with ID: {video_id}")
    
    # Extract frames
    print("Extracting frames from sample video...")
    frames_dir = f"frames/video_{video_id}"
    frames_extracted = extract_frames_from_video(sample_video_path, video_id, frames_dir)
    
    print(f"✓ Extracted {frames_extracted} frames from sample video")
    
    return video_id

def main():
    """Main setup function"""
    print("🚀 Setting up News-Scan-AI...")
    print("=" * 50)
    
    # Create necessary directories
    directories = ['database', 'uploads', 'videos', 'frames', 'static/images']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    # Initialize database
    setup_database()
    
    # Add sample video
    video_id = add_sample_video()
    
    print("=" * 50)
    print("🎉 Setup complete!")
    print(f"📁 Project directory: {os.getcwd()}")
    
    if video_id:
        print(f"🎥 Sample video ready with ID: {video_id}")
        print("📷 Sample image available at: static/images/i1.jpg")
    
    print("\n🚀 To start the application:")
    print("   python app.py")
    print("\n🌐 Then open your browser to:")
    print("   http://localhost:5000")

if __name__ == "__main__":
    main()
