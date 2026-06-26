# py-tts — PDF to Speech

**py-tts** converts PDF, DOCX, and TXT documents to MP3 audio using text-to-speech. Built with Flask.

<p align="center">
    <img src="static/assets/preview.png" alt="py-tts app preview">
</p>

## Features

- **Drag-and-drop upload** with instant text preview and word count
- **Real-time progress** via Server-Sent Events — watch chunk-by-chunk as audio is generated
- **Multiple voices** — Matthew, Joanna, Amy, Brian, Emma, Russell, Nicole, Joey
- **AI text cleanup** (optional) — GPT-4o-mini removes headers, page numbers, and PDF extraction artifacts before conversion
- **WaveSurfer.js waveform player** with click-to-seek, play/pause, and variable playback speed
- **Multi-format support** — PDF, DOCX, and TXT files
- **REST API** — `POST /api/convert` returns raw MP3 for programmatic access
- Download generated MP3
- Responsive Bootstrap 5 design

## Getting Started

### Prerequisites

- Python 3.7+
- An `OPENAI_API_KEY` if you want AI text cleanup (optional)

### Installation

```bash
git clone https://github.com/yourusername/py-tts.git
cd py-tts
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in the project root:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes (prod) | Flask session secret key |
| `OPENAI_API_KEY` | No | Enables AI text cleanup via GPT-4o-mini |

### Running the app

```bash
python server.py
```

Visit `http://127.0.0.1:5000` in your browser.

### Running tests

```bash
pytest test_server.py test_progress.py test_ai_cleanup.py -v
```

## API Reference

A full interactive reference is available at `/api-docs`. Quick overview:

```bash
# List available voices
curl http://localhost:5000/api/voices

# Convert a PDF to MP3
curl -X POST http://localhost:5000/api/convert \
  -F "file=@document.pdf" \
  -F "voice=Joanna" \
  --output audio.mp3
```

## Architecture

```
server.py        Flask routes: /upload (async), /progress/<id> SSE, /preview, /reset, /api/*
utility.py       Text extraction (PDF/DOCX/TXT), TTS pipeline with progress callbacks
jobs.py          In-process job registry (uuid + queue.Queue) — no Redis needed
ai_cleanup.py    OpenAI GPT-4o-mini text normalizer with graceful fallback
```

The upload flow:
1. `POST /upload` — extracts text synchronously, starts a background thread, returns `{job_id}` in HTTP 202
2. `GET /progress/<job_id>` — SSE stream; client receives `{chunk, total}` events during conversion, then `{done: true}`
3. On `done`, the browser redirects to `/` where the WaveSurfer player renders the generated MP3

## Deployment

The app is deployed on [Render](https://py-tts.onrender.com). The `gunicorn` server is configured via the `Procfile`. Per-job audio files are stored in `static/assets/` and cleaned up when the user resets.

## License

MIT
