import express from 'express';
import cors from 'cors';
import multer from 'multer';
import fetch from 'node-fetch';
import FormData from 'form-data';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

dotenv.config();

const app = express();
const port = process.env.PORT || 5174;

const storage = multer.memoryStorage();
const upload = multer({ storage });

app.use(cors());
app.use(express.json());

// Resolve __dirname for ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Serve static frontend
app.use(express.static(path.join(__dirname, '..', 'public')));

app.post('/api/search', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image uploaded. Ensure the form field is named "image".' });
    }

    const isMock = (process.env.MOCK || 'true').toLowerCase() === 'true';

    if (isMock) {
      // Return demo results for testing the UI
      return res.json({
        results: [
          {
            platform: 'youtube',
            videoId: 'dQw4w9WgXcQ',
            videoUrl: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            title: 'Sample News Clip (Demo Result)',
            channel: 'Demo Channel',
            matchedAtSeconds: 42,
            matchedAtHMS: '00:00:42',
            confidence: 0.92
          },
          {
            platform: 'youtube',
            videoId: '9Auq9mYxFEE',
            videoUrl: 'https://www.youtube.com/watch?v=9Auq9mYxFEE',
            title: 'Sample News Clip 2 (Demo Result)',
            channel: 'Demo Channel 2',
            matchedAtSeconds: 125,
            matchedAtHMS: '00:02:05',
            confidence: 0.87
          }
        ]
      });
    }

    const apiUrl = process.env.NEWS_API_URL;
    const apiKey = process.env.NEWS_API_KEY;

    if (!apiUrl || !apiKey) {
      return res.status(500).json({ error: 'Missing NEWS_API_URL or NEWS_API_KEY. Set them in .env or enable MOCK mode.' });
    }

    const form = new FormData();
    form.append('image', req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype
    });

    // NOTE: Adjust the fetch and headers according to your real API spec
    const apiResp = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`
      },
      body: form
    });

    if (!apiResp.ok) {
      const text = await apiResp.text();
      return res.status(502).json({ error: `Upstream API error (${apiResp.status})`, details: text });
    }

    const apiData = await apiResp.json();

    const resultsRaw = apiData.results || apiData.matches || apiData.data || [];
    const results = resultsRaw.map((r) => normalizeResult(r));

    return res.json({ results });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'Internal server error', details: String(err) });
  }
});

function normalizeResult(r) {
  const url = r.url || r.videoUrl || null;
  const videoId = r.videoId || r.youtubeId || (url ? extractYouTubeId(url) : null);
  const hms = r.matchedAtHMS || r.hms || r.timecode || r.timestampHMS || null;
  const secondsRaw = r.matchedAtSeconds ?? r.seconds ?? r.timestamp ?? null;
  const matchedAtSeconds = typeof secondsRaw === 'number' ? secondsRaw : (hms ? hmsToSeconds(hms) : null);

  return {
    platform: r.platform || 'youtube',
    videoId,
    videoUrl: url || (videoId ? `https://www.youtube.com/watch?v=${videoId}` : null),
    title: r.title || r.videoTitle || null,
    channel: r.channel || r.channelTitle || null,
    matchedAtSeconds,
    matchedAtHMS: secondsToHms(matchedAtSeconds),
    confidence: r.confidence ?? null,
    raw: r
  };
}

function hmsToSeconds(hms) {
  if (!hms || typeof hms !== 'string') return null;
  const parts = hms.trim().split(':').map(Number);
  if (parts.some((n) => Number.isNaN(n))) return null;
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 1) return parts[0];
  return null;
}

function secondsToHms(sec) {
  if (sec == null || Number.isNaN(sec)) return null;
  const s = Math.max(0, Math.floor(sec));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const ss = s % 60;
  const hh = String(h).padStart(2, '0');
  const mm = String(m).padStart(2, '0');
  const ssStr = String(ss).padStart(2, '0');
  return `${hh}:${mm}:${ssStr}`;
}

function extractYouTubeId(u) {
  try {
    const url = new URL(u);
    if (url.hostname.includes('youtu.be')) {
      return url.pathname.replace('/', '');
    }
    if (url.hostname.includes('youtube.com')) {
      if (url.searchParams.get('v')) return url.searchParams.get('v');
      const m = url.pathname.match(/\/embed\/([^/?#]+)/);
      if (m) return m[1];
    }
    return null;
  } catch {
    return null;
  }
}

app.listen(port, () => {
  console.log(`Server listening on http://localhost:${port}`);
});
