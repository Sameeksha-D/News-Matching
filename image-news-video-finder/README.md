# Image → Indian News Video Finder

This project lets users upload an image and finds Indian news YouTube videos where the image appears. It ships with a mock mode for demo/testing and can proxy to a real image-search API when configured.

Project layout:
- server/ — Node.js Express server that serves the static frontend and exposes POST /api/search

Quick start (Windows PowerShell):
1) Copy env template and keep mock mode on for now
   - Path: image-news-video-finder/server
   - Copy .env.example to .env and keep MOCK=true

2) Install dependencies
   - In PowerShell:
     cd "C:\Users\dubba_n5nz3rq\Desktop\major project\News-Scan-AI\image-news-video-finder\server"
     npm install

3) Run the server
   - npm start
   - Open http://localhost:5174
   - Upload an image to see demo matches (YouTube embeds with timestamps)

Switch to a real API:
- Edit image-news-video-finder/server/.env
  - Set MOCK=false
  - Set NEWS_API_URL to your API endpoint that accepts a multipart/form-data with field name image
  - Set NEWS_API_KEY to your API key/token
- The server will POST the image to NEWS_API_URL with Authorization: Bearer <NEWS_API_KEY>
- If your API uses a different auth/header or response schema, update src/server.js accordingly

Expected API response (flexible):
- The server tries to normalize a few common shapes. Ideally return an array under results or matches like:
  {
    "results": [
      {
        "platform": "youtube",
        "videoId": "<YOUTUBE_ID>",
        "url": "https://www.youtube.com/watch?v=<YOUTUBE_ID>",
        "title": "...",
        "channel": "...",
        "timestamp": 125  // or "02:05"
      }
    ]
  }

Notes:
- The frontend is plain HTML/JS served from server/public/index.html
- The YouTube embed uses the start parameter to jump to the match time
- Keep your API key in .env; it is never exposed to the browser

Troubleshooting:
- If upload fails with 400, ensure the form field is image (the frontend does this already)
- If you get Missing NEWS_API_URL or NEWS_API_KEY, either enable MOCK=true or configure .env
- On Windows, if port 5174 is in use, change PORT in .env
