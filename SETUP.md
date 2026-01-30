# SETUP GUIDE: Complete Step-by-Step Instructions

This guide walks you through setting up the Meeting Summarizer system from scratch.

---

## System Requirements Check

Before starting, ensure you have:
- **Python 3.9+** installed
  - Check: `python --version`
- **8GB+ RAM** (16GB recommended)
- **20GB+ disk space** (for models and files)
- **Stable internet** (for initial setup only - system runs offline after)

---

## STEP 1: Environment Setup (5 minutes)

### 1.1 Python Virtual Environment (RECOMMENDED)

Create an isolated Python environment to avoid conflicts:

```bash
# Navigate to project directory
cd meeting_summarizer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### 1.2 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- openai-whisper (Speech-to-Text)
- torch (Deep Learning framework)
- transformers (LLM models)
- librosa (Audio processing)
- fastapi, uvicorn (Optional API)
- And more...

**Time:** ~5-10 minutes depending on internet speed

---

## STEP 2: Install ffmpeg (Required for Audio)

ffmpeg is needed to load audio files (MP3, M4A, etc.).

### Windows Users

**Option A: Using Chocolatey (Easiest)**
```bash
choco install ffmpeg
```

**Option B: Manual Installation**
1. Download from: https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add to PATH:
   - Right-click Computer → Properties
   - Advanced system settings → Environment Variables
   - Add `C:\ffmpeg\bin` to PATH
4. Verify: `ffmpeg -version`

### macOS Users

```bash
brew install ffmpeg
```

Verify: `ffmpeg -version`

### Linux Users

```bash
apt-get install ffmpeg
```

Verify: `ffmpeg -version`

---

## STEP 3: Choose & Setup Your LLM Backend (10-15 minutes)

You need a way to run local LLMs. Choose Option A (RECOMMENDED) or Option B.

### OPTION A: Ollama (RECOMMENDED - Easiest Setup)

**Why choose Ollama?**
- Single download & install
- Pre-optimized models
- No code configuration
- Just "pull model" and "run"
- Works locally without internet

**Setup Steps:**

1. **Download Ollama**
   - Go to: https://ollama.ai
   - Click "Download"
   - Install for your OS (Windows/macOS/Linux)

2. **Verify Installation**
   ```bash
   ollama --version
   ```

3. **Download a Language Model**
   
   Open terminal/command prompt and run:
   
   ```bash
   # Download Mistral 7B (Recommended for laptop)
   # ~4GB, excellent quality, fast
   ollama pull mistral
   ```
   
   **Other Options:**
   ```bash
   ollama pull llama2      # Alternative: Llama 2 7B
   ollama pull phi         # Smaller: Phi 2.7B (~2GB, faster)
   ollama pull neural-chat # Alternative: Neural Chat
   ```
   
   **Time:** 5-10 minutes (depends on model size and internet)

4. **Start Ollama Server**
   
   Keep this running in background while using the system:
   
   ```bash
   ollama serve
   ```
   
   Output should show:
   ```
   API server started listening on http://127.0.0.1:11434
   ```
   
   **Note:** Keep this terminal window open!

5. **Update Config (if using non-default model)**
   
   Edit `config/settings.py`:
   ```python
   LLM_MODEL = LLMModel.LLAMA2_7B.value  # or your choice
   ```

---

### OPTION B: HuggingFace Transformers (More Control)

**Why choose HuggingFace?**
- Direct model access
- Custom fine-tuning possible
- No external service needed
- Works offline after download

**Setup Steps:**

1. **Update Configuration**
   
   Edit `config/settings.py`:
   
   ```python
   LLM_BACKEND = LLMBackend.TRANSFORMERS.value
   
   HF_CONFIG = {
       "model_id": "mistralai/Mistral-7B-Instruct-v0.1",
       "device": "cuda",  # or "cpu"
       "max_new_tokens": 512,
   }
   ```

2. **Test the Setup**
   
   ```python
   # models auto-download on first use
   from src.modules.llm_summarizer import MeetingSummarizer
   summarizer = MeetingSummarizer("transformers")
   # First run will download model (~4-7GB)
   ```

**Note:** Models download to `~/.cache/huggingface/` (~4-7GB)

---

## STEP 4: Verify Installation

Run the status check to ensure everything is ready:

```bash
python main.py status
```

Expected output:
```
✓ Python Dependencies
✓ Audio Input Directory
✓ Output Directory
✓ Whisper Model
✓ LLM Backend
```

If any check fails, re-run the relevant setup step above.

---

## STEP 5: Test with Sample Audio

### 5.1 Create a Test Audio File

Option 1: Use an existing meeting recording
- Export from Zoom/Teams/Google Meet as MP3 or WAV
- Place in `audio_input/` folder

Option 2: Create a test recording
- Use your phone's voice recorder
- Record a 1-2 minute conversation
- Export as MP3 or WAV

Option 3: Use an online sample
- Find a podcast episode or speech
- Download as MP3
- Place in `audio_input/` folder

### 5.2 Run Your First Summary

```bash
# Basic usage
python main.py summarize audio_input/your_audio.mp3

# With title
python main.py summarize audio_input/meeting.wav --title "Weekly Standup"
```

### 5.3 Check Results

Results are saved in `outputs/` folder:

```bash
# View summary
cat outputs/summary_*.txt

# View structured data
cat outputs/summary_*.json

# View full transcript
cat outputs/transcript_*.txt
```

---

## STEP 6: Choose Your Interface

### Option 1: Command Line (Simplest)

```bash
python main.py summarize meeting.mp3
```

See all commands:
```bash
python main.py --help
```

### Option 2: Python API (For Developers)

```python
from src.pipeline import MeetingSummarizerPipeline

pipeline = MeetingSummarizerPipeline()
result = pipeline.process_meeting("meeting.mp3", "Team Meeting")

print(result['summary'])
print(result['action_items'])
```

### Option 3: REST API (For Web Apps)

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start API server
python server.py
```

API available at: http://localhost:8000

Swagger UI: http://localhost:8000/docs

---

## STEP 7: Configuration Tuning (Optional)

For optimal performance on your laptop, edit `config/settings.py`:

```python
# For 8GB RAM laptops (prioritize speed):
WHISPER_MODEL = WhisperModel.SMALL.value  # instead of MEDIUM
WHISPER_CHUNK_DURATION = 600  # 10 min chunks instead of 15

# For 16GB+ RAM (prioritize accuracy):
WHISPER_MODEL = WhisperModel.MEDIUM.value
WHISPER_CHUNK_DURATION = 900  # 15 min chunks

# To use GPU (if you have NVIDIA):
WHISPER_CONFIG["device"] = "cuda"
HF_CONFIG["device"] = "cuda"

# To use CPU only:
WHISPER_CONFIG["device"] = "cpu"
HF_CONFIG["device"] = "cpu"
```

---

## STEP 8: Next Steps

### Try Different Workflows

1. **Batch Processing**
   ```bash
   for file in audio_input/*.mp3; do
       python main.py summarize "$file"
   done
   ```

2. **Custom Prompts**
   - Edit `prompts/summarize.txt`
   - Customize summary style or focus areas

3. **API Integration**
   - Use REST API with your own app
   - See `server.py` for examples

### Troubleshooting

**Common Issues:**

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError: whisper" | `pip install openai-whisper` |
| "ffmpeg not found" | Reinstall ffmpeg, add to PATH |
| "Ollama not running" | Run `ollama serve` in new terminal |
| "Model not found" | Run `ollama pull mistral` |
| "CUDA out of memory" | Use smaller model or CPU mode |
| "Slow transcription" | Use smaller Whisper model (TINY) |

**For Help:**
- Check logs in `logs/meeting_summarizer.log`
- Review `README.md` troubleshooting section
- Check module docstrings in code

---

## FOLDER STRUCTURE AFTER SETUP

```
meeting_summarizer/
├── venv/                      # Python virtual environment
├── src/                       # Source code
├── config/
│   └── settings.py           # Configure models, paths, etc.
├── audio_input/              # 👈 Place audio files here
├── outputs/                  # 👈 Find results here
├── logs/
├── prompts/
├── main.py                   # CLI entry point
├── server.py                 # API server
├── requirements.txt
└── README.md
```

---

## PERFORMANCE EXPECTATIONS

**First Time Setup:**
- Whisper model download: ~500MB, ~2-5 min
- LLM model download: ~4GB, ~10-15 min
- Total: ~15-20 minutes

**Ongoing Usage (per meeting):**
- 1-hour meeting: ~15-20 minutes (CPU)
- 1-hour meeting: ~3-5 minutes (GPU)

**System Requirements Met:**
- ✓ Runs fully offline (after setup)
- ✓ No API keys or internet needed
- ✓ Privacy: data stays on your device
- ✓ Cost: $0 (fully open-source)

---

## UNINSTALL/CLEANUP

To completely remove the system:

```bash
# Remove project folder
rm -rf meeting_summarizer

# Remove downloaded models (optional, takes space)
# Whisper cache: ~/.cache/torch
# HuggingFace models: ~/.cache/huggingface
# Ollama models: ~/.ollama
```

---

## YOU'RE ALL SET! 🎉

Start summarizing meetings:

```bash
python main.py summarize audio_input/your_meeting.mp3
```

Outputs appear in `outputs/` folder.

---

**Questions?** Check:
- `README.md` - Full documentation
- `config/settings.py` - Configuration options
- Module docstrings - Code documentation
- `logs/meeting_summarizer.log` - Debug info

**Happy Summarizing!**
