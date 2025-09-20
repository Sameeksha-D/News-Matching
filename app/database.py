import sqlite3
import os
from datetime import datetime
import json

DATABASE_PATH = 'database/news_scan_ai.db'

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create videos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            duration REAL,
            fps REAL,
            frames_extracted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create frames table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            frame_number INTEGER,
            timestamp REAL,
            frame_path TEXT,
            feature_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos (id)
        )
    ''')
    
    # Create searches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uploaded_image_path TEXT,
            search_results TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_video(filename, original_name, file_path, duration=None, fps=None):
    """Add a new video to the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO videos (filename, original_name, file_path, duration, fps)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, original_name, file_path, duration, fps))
    
    video_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return video_id

def add_frame(video_id, frame_number, timestamp, frame_path, feature_hash=None):
    """Add a frame to the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO frames (video_id, frame_number, timestamp, frame_path, feature_hash)
        VALUES (?, ?, ?, ?, ?)
    ''', (video_id, frame_number, timestamp, frame_path, feature_hash))
    
    conn.commit()
    conn.close()

def get_all_videos():
    """Get all videos from the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM videos ORDER BY created_at DESC')
    videos = cursor.fetchall()
    conn.close()
    return videos

def get_video_frames(video_id):
    """Get all frames for a specific video"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM frames WHERE video_id = ? ORDER BY frame_number', (video_id,))
    frames = cursor.fetchall()
    conn.close()
    return frames

def update_video_frames_count(video_id, frames_count):
    """Update the frames extracted count for a video"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('UPDATE videos SET frames_extracted = ? WHERE id = ?', (frames_count, video_id))
    conn.commit()
    conn.close()

def save_search_result(uploaded_image_path, results):
    """Save search results to database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO searches (uploaded_image_path, search_results)
        VALUES (?, ?)
    ''', (uploaded_image_path, json.dumps(results)))
    
    search_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return search_id
