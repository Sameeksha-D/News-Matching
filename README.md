# News-Scan-AI

A powerful web application that helps verify news images by finding exactly where they appear in video footage. Instead of manually searching through long news clips, users can upload a screenshot, and the system will identify matching frames with precise timestamps.

## 🚀 Features

- Image-to-Video Matching: Upload any image and find where it appears in video files
- Precise Timestamps: Get exact time ranges where the image appears
- Multiple Similarity Algorithms: Uses histogram comparison, template matching, and structural similarity
- Web-Based Interface: Easy-to-use web application with drag-and-drop upload
- Video Database: Manage multiple videos in a searchable database
- Background Processing: Automatic frame extraction from uploaded videos
- Real-time Status: Live updates on video processing status

## 🛠️ Technology Stack

- Backend: Python Flask
- Computer Vision: OpenCV for image processing and matching
- Machine Learning: scikit-learn for similarity calculations
- Database: SQLite for storing video metadata and frame information
- Frontend: Bootstrap 5 with responsive design
- Image Processing: PIL/Pillow for image manipulation

