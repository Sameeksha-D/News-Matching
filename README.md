# News-Scan-AI

A powerful web application that helps verify news images by finding exactly where they appear in video footage. Instead of manually searching through long news clips, users can upload a screenshot, and the system will identify matching frames with precise timestamps.

## 🚀 Features

- **Image-to-Video Matching**: Upload any image and find where it appears in video files
- **Precise Timestamps**: Get exact time ranges where the image appears
- **Multiple Similarity Algorithms**: Uses histogram comparison, template matching, and structural similarity
- **Web-Based Interface**: Easy-to-use web application with drag-and-drop upload
- **Video Database**: Manage multiple videos in a searchable database
- **Background Processing**: Automatic frame extraction from uploaded videos
- **Real-time Status**: Live updates on video processing status

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Computer Vision**: OpenCV for image processing and matching
- **Machine Learning**: scikit-learn for similarity calculations
- **Database**: SQLite for storing video metadata and frame information
- **Frontend**: Bootstrap 5 with responsive design
- **Image Processing**: PIL/Pillow for image manipulation

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/News-Scan-AI.git
   cd News-Scan-AI
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python -c "from app.database import init_database; init_database()"
   ```

## 🚀 Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Open your web browser**
   Navigate to `http://localhost:5000`

3. **Upload a video**
   - Click "Upload Video" and select a news video file
   - Wait for frame extraction to complete (runs in background)

4. **Search for images**
   - Go to the Search page
   - Select a video from the database
   - Upload an image you want to find
   - View results with timestamps and similarity scores

## 📁 Project Structure

```
News-Scan-AI/
├── app/                    # Application modules
│   ├── database.py        # Database operations
│   ├── video_processor.py # Video frame extraction
│   └── image_matcher.py   # Image matching algorithms
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── search.html       # Search page
│   └── results.html      # Results page
├── static/               # Static files
│   ├── css/             # Custom stylesheets
│   ├── js/              # Custom JavaScript
│   └── images/          # Sample images
├── database/            # SQLite database files
├── uploads/             # User uploaded images
├── videos/              # Uploaded video files
├── frames/              # Extracted video frames
├── app.py               # Main Flask application
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🔍 How It Works

1. **Video Processing**: When you upload a video, the system:
   - Extracts frames at regular intervals (default: every second)
   - Generates feature hashes for each frame
   - Stores frame metadata in the database

2. **Image Matching**: When searching for an image, the system:
   - Compares the uploaded image against all video frames
   - Uses multiple similarity algorithms:
     - **Histogram Comparison**: Compares color distributions
     - **Template Matching**: Looks for exact visual matches
     - **Structural Similarity**: Analyzes image structure
   - Combines scores using weighted averages
   - Groups nearby matches into time ranges

3. **Results**: Displays:
   - Exact timestamps where the image appears
   - Similarity confidence scores
   - Frame previews
   - Time range visualizations

## 🎯 Use Cases

- **Fact-checking**: Verify if a news image actually appears in claimed video footage
- **Content verification**: Check if screenshots match original video content
- **Media analysis**: Find specific moments in long video files
- **Reverse video search**: Locate source videos from image snippets

## ⚙️ Configuration

### Similarity Thresholds
- **Low (0.2)**: More matches, may include false positives
- **Medium (0.3)**: Balanced accuracy (recommended)
- **High (0.4)**: Precise matches only
- **Very High (0.5)**: Extremely strict matching

### Frame Extraction
Default: Extract 1 frame per second. Modify in `video_processor.py`:
```python
extract_frames_from_video(video_path, video_id, output_dir, frame_interval=30)
```

## 🐛 Troubleshooting

### Common Issues

1. **"No matches found" but image should match**
   - Lower the similarity threshold
   - Ensure video processing completed
   - Check if image quality is sufficient

2. **Slow processing**
   - Large videos take time to process
   - Consider adjusting frame extraction interval
   - Use smaller video files for testing

3. **Memory issues with large videos**
   - Increase frame extraction interval
   - Process videos in smaller chunks
   - Ensure sufficient disk space

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenCV community for computer vision tools
- Flask framework for web development
- Bootstrap for responsive UI components

## 📞 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/News-Scan-AI/issues) on GitHub.

---

**News-Scan-AI** - Helping fight misinformation through image verification 🛡️
