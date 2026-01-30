# QUICK START GUIDE

Get your meeting summarization system running in 10 minutes.

---

## Super Quick Setup (TL;DR)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install ffmpeg (one-time)
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg
# Linux: apt-get install ffmpeg

# 3. Setup LLM (pick one)
# OPTION A: Ollama (recommended)
# - Download from ollama.ai
# - Run: ollama pull mistral && ollama serve

# OPTION B: Auto-download (HuggingFace)
# - Already configured, models auto-download

# 4. Run
python main.py summarize your_meeting.mp3

# 5. Check results
ls outputs/
cat outputs/summary_*.txt
```

---

## Detailed Quick Start (Step by Step)

### Step 1: Prerequisites (2 min)

Check you have:
- Python 3.9+ installed: `python --version`
- 8GB+ RAM available
- Internet for downloads (first-time only)

### Step 2: Install (3 min)

```bash
# Navigate to project
cd meeting_summarizer

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install packages
pip install -r requirements.txt
```

### Step 3: Install ffmpeg (2 min)

**Windows:**
```bash
# With Chocolatey (easiest)
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
apt-get install ffmpeg
```

Verify: `ffmpeg -version`

### Step 4: Setup LLM (2 min)

#### Option A: Ollama (Easiest)
```bash
# 1. Download from https://ollama.ai
# 2. Install and run
# 3. In a new terminal:
ollama pull mistral
ollama serve  # Keep this running!
```

#### Option B: Auto-download (No extra install)
No additional setup needed - uses HuggingFace with auto-download.

### Step 5: First Run (1 min)

```bash
# Test with a sample audio file
python main.py summarize sample_meeting.mp3

# Or use your own meeting audio
python main.py summarize my_meeting.wav --title "Team Standup"
```

### Step 6: Check Results (< 1 min)

```bash
# View human-readable summary
cat outputs/summary_*.txt

# View JSON (for parsing)
cat outputs/summary_*.json

# View full transcript
cat outputs/transcript_*.txt
```

---

## Example Usage

### Example 1: Basic Usage

```bash
python main.py summarize meeting.mp3
```

**Output:**
```
==================================================
Starting meeting summarization pipeline
==================================================

[✓] Audio loaded: 45.2s duration
[✓] Speech-to-Text complete: 342 segments
[✓] Text cleaning done
[✓] LLM Summarization complete

==================================================
✓ PIPELINE COMPLETE
Output: outputs/summary_20240120_143000.json
        outputs/summary_20240120_143000.txt
==================================================
```

### Example 2: With Title

```bash
python main.py summarize meeting.wav --title "Q1 Planning Meeting"
```

### Example 3: Using Python API

```python
from src.pipeline import MeetingSummarizerPipeline

# Create pipeline
pipeline = MeetingSummarizerPipeline()

# Process meeting
result = pipeline.process_meeting(
    "meeting.mp3",
    meeting_title="Team Standup"
)

# Print results
print("SUMMARY:")
print(result['summary'])
print("\nACTION ITEMS:")
for item in result['action_items']:
    print(f"  - {item['task']} (Owner: {item['owner']})")
```

### Example 4: REST API

```bash
# Terminal 1: Start API
python server.py

# Terminal 2: Call API
curl -X POST "http://localhost:8000/summarize" \
  -F "file=@meeting.mp3" \
  -F "title=Team Meeting"
```

**Response:**
```json
{
  "success": true,
  "meeting_title": "Team Meeting",
  "summary": "...",
  "key_topics": [...]
}
```

---

## File Structure After Setup

```
meeting_summarizer/
├── audio_input/              👈 Put audio files here
│   ├── meeting1.mp3
│   ├── meeting2.wav
│   └── ...
├── outputs/                  👈 Find results here
│   ├── summary_*.json
│   ├── summary_*.txt
│   └── transcript_*.txt
├── logs/
│   └── meeting_summarizer.log
├── src/
│   ├── pipeline.py
│   └── modules/
│       ├── audio_processor.py
│       ├── speech_to_text.py
│       ├── text_preprocessor.py
│       └── llm_summarizer.py
├── config/
│   └── settings.py           👈 Customize here
├── main.py                   👈 Start here
├── server.py
├── requirements.txt
├── README.md
├── SETUP.md
└── ARCHITECTURE.md
```

---

## Common Commands

```bash
# Get help
python main.py --help

# Check system status
python main.py status

# Get system info
python main.py info

# Summarize single file
python main.py summarize meeting.mp3

# Summarize with title
python main.py summarize meeting.mp3 --title "Q1 Planning"

# Batch process (bash)
for file in audio_input/*.mp3; do
    python main.py summarize "$file"
done
```

---

## Troubleshooting Quick Fixes

| Problem | Fix |
|---------|-----|
| "ffmpeg not found" | Install ffmpeg (see Step 3) |
| "No module named 'whisper'" | Run `pip install openai-whisper` |
| "Ollama not running" | Run `ollama serve` in new terminal |
| "CUDA out of memory" | Use CPU: edit `config/settings.py` |
| Very slow | Use smaller model (TINY) in config |

---

## Next Steps

1. **Read Full Documentation**
   - [README.md](README.md) - Full feature list
   - [ARCHITECTURE.md](ARCHITECTURE.md) - How it works
   - [SETUP.md](SETUP.md) - Detailed setup

2. **Customize Configuration**
   - Edit `config/settings.py`
   - Choose different models
   - Adjust chunk sizes

3. **Integrate with Your App**
   - Use Python API directly
   - Deploy REST API
   - Add to your pipeline

4. **Batch Processing**
   - Process multiple meetings
   - Create scheduling/cron jobs
   - Export to spreadsheet

---

## Performance Tips

For slower systems:
1. Use smaller Whisper model: `WhisperModel.TINY`
2. Increase chunk duration: `WHISPER_CHUNK_DURATION = 1200` (20 min)
3. Skip transcript: `--no-save-transcript`
4. Use GPU if available (NVIDIA): Set device to "cuda"

---

## Estimated Times

On Intel i7, 8GB RAM:
- Setup: ~20 minutes (first time)
- Per 1-hour meeting: ~15-20 minutes
- Per 30-min meeting: ~8-10 minutes

With GPU (NVIDIA):
- Per 1-hour meeting: ~3-5 minutes

---

## What Gets Generated

For each audio file, you get:

1. **summary_TIMESTAMP.json** - Machine-readable
   - Executive summary
   - Key topics
   - Decisions
   - Action items (task, owner, deadline)

2. **summary_TIMESTAMP.txt** - Human-readable
   - Formatted summary
   - Easy to read
   - Can email/share

3. **transcript_TIMESTAMP.txt** - Full transcript
   - Timestamped
   - [00:05] Speaker text
   - Full reference

---

## You're Ready! 🚀

```bash
python main.py summarize meeting.mp3
```

Check `outputs/` for your results!

For detailed info, see [README.md](README.md)
