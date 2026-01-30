# LLM-Based Meeting Summarization System

## Overview

A complete, **locally-running** system that converts meeting audio into structured summaries, transcripts, action items, and key decisions. Built with open-source tools - **no cloud APIs required**.

```
Audio File (MP3/WAV) 
    ↓
[Whisper STT] → Accurate Transcription
    ↓
[Text Preprocessing] → Clean & Chunk
    ↓
[Local LLM] → Extract Insights
    ↓
[JSON + TXT] → Structured Output
```

---

## Project Structure

```
meeting_summarizer/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── main.py                      # CLI entry point
├── server.py                    # FastAPI (optional REST API)
│
├── config/
│   └── settings.py             # Configuration (models, paths, etc.)
│
├── src/
│   ├── utils.py                # Logging, file operations, utilities
│   ├── pipeline.py             # Main orchestrator
│   └── modules/
│       ├── audio_processor.py  # Load, resample, chunk audio
│       ├── speech_to_text.py   # Whisper transcription
│       ├── text_preprocessor.py # Clean text, split chunks
│       └── llm_summarizer.py   # LLM summarization & extraction
│
├── prompts/                    # LLM prompt templates
│   ├── summarize.txt
│   └── action_items.txt
│
├── audio_input/               # Place audio files here
├── outputs/                   # Generated summaries (JSON + TXT)
└── logs/                      # Debug logs
```

---

## Features

✅ **End-to-End Pipeline**
- Audio loading (MP3, WAV, M4A, OGG, FLAC)
- Automatic speech-to-text
- Transcript cleaning
- LLM-powered summarization

✅ **Structured Outputs**
- Executive summary
- Key topics (auto-extracted)
- Decisions made
- Action items with owners & deadlines
- Full timestamped transcript

✅ **Laptop-Optimized**
- Chunking for long meetings (15-min chunks)
- Memory-efficient processing
- CPU or GPU support
- No internet required

✅ **Flexible Backends**
- **Ollama**: Easy setup, pre-optimized
- **HuggingFace Transformers**: Full control
- Multiple model options (Mistral, Llama 2, Phi)

✅ **Multiple Interfaces**
- Command-line (Python)
- REST API (FastAPI)
- Direct Python module usage

---

## Installation

### Prerequisites

- **Windows 11** (or Windows 10)
- **Python 3.9 or higher** - Download from [python.org](https://www.python.org/downloads/)
- **8GB RAM minimum** (16GB recommended)
- **10GB free disk space** (for models and dependencies)

### Step 1: Install Python (if not installed)

1. Download Python 3.11+ from https://www.python.org/downloads/windows/
2. **Important:** Check "Add Python to PATH" during installation
3. Verify installation:
   ```powershell
   python --version
   ```

### Step 2: Clone/Download Project

```powershell
# Navigate to project folder
cd C:\Users\YourUsername\Downloads\meeting_summarizer
```

### Step 3: Install Python Dependencies

```powershell
# Install all required packages
pip install -r requirements.txt

# Or install individually:
pip install librosa soundfile numpy torch transformers nltk fastapi uvicorn python-multipart tqdm python-dotenv pydantic openai-whisper ollama streamlit streamlit-audiorec
```

**Note:** First installation may take 5-10 minutes as it downloads PyTorch and other large packages.

### Step 4: Install ffmpeg (Required for Audio Processing)

**Option A - Using Chocolatey (Recommended):**
```powershell
# Install Chocolatey first if not installed (Run as Administrator):
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install ffmpeg:
choco install ffmpeg
```

**Option B - Manual Installation:**
1. Download ffmpeg from https://www.gyan.dev/ffmpeg/builds/ (choose "ffmpeg-release-essentials.zip")
2. Extract to `C:\ffmpeg`
3. Add to PATH:
   - Open "Environment Variables" in Windows Settings
   - Edit "Path" under System variables
   - Add `C:\ffmpeg\bin`
   - Click OK and restart terminal
4. Verify: `ffmpeg -version`

### Step 5: Install Ollama (LLM Backend)

1. Download Ollama for Windows from https://ollama.ai/download
2. Run the installer (OllamaSetup.exe)
3. After installation, open PowerShell and download the model:
   ```powershell
   # Download Mistral 7B model (~4GB)
   ollama pull mistral:7b
   
   # Or download smaller/faster alternatives:
   ollama pull phi           # 2GB - faster, less accurate
   ollama pull llama2        # 4GB - good alternative
   ```
4. Ollama runs automatically as a Windows service - no need to start manually

### Step 6: Verify Installation

```powershell
# Check system status
python main.py status
```

Expected output:
```
✓ Configuration loaded
✓ Python Dependencies
✓ Audio Input Directory
✓ Output Directory
✓ Whisper Model
✓ LLM Backend
```

### Step 7: Run the Application

**Option A - Streamlit Web UI (Recommended):**
```powershell
streamlit run app.py
```
Then open http://localhost:8501 in your browser

**Option B - Command Line:**
```powershell
# Place audio file in audio_input/ folder
python main.py summarize audio_input\your_meeting.mp3
```

### Troubleshooting Windows 11

**Issue: "Python not recognized"**
- Solution: Reinstall Python and check "Add to PATH" option

**Issue: "ffmpeg not found"**
- Solution: Restart terminal after installing ffmpeg, or manually add to PATH

**Issue: "Permission denied" during pip install**
- Solution: Run PowerShell as Administrator

**Issue: Ollama connection failed**
- Solution: Check if Ollama service is running:
  ```powershell
  Get-Service Ollama
  # If stopped, start it:
  Start-Service Ollama
  ```

**Issue: "CUDA error" with Whisper**
- Solution: This is normal - the app automatically falls back to CPU mode

**Issue: Slow processing**
- Solution: Use smaller models:
  - Whisper: Change to "tiny" or "base" in config/settings.py
  - LLM: Use "phi" model instead of "mistral"

---

## Configuration

Edit `config/settings.py` to customize:

```python
# Speech-to-Text Model
WHISPER_MODEL = WhisperModel.SMALL.value  # Options: tiny, base, small, medium, large
# Recommendation: SMALL (good balance) or MEDIUM (higher accuracy)

# LLM Backend & Model
LLM_BACKEND = LLMBackend.OLLAMA.value  # or "transformers"
LLM_MODEL = LLMModel.MISTRAL_7B.value   # Options: Mistral, Llama2, Neural-Chat, Phi

# Text Processing
MAX_TOKENS_PER_CHUNK = 1500  # LLM context length
WHISPER_CHUNK_DURATION = 900  # 15 minutes per chunk
```

---

## Setup: Choosing Your LLM Backend

### Option A: Ollama (RECOMMENDED - Easiest)

**Why Ollama?**
- Single download & install
- Pre-optimized models
- No code setup needed
- Works locally at ~5 tokens/sec

**Setup:**

1. Download Ollama from https://ollama.ai
2. Run installer and follow prompts
3. Pull desired model:
   ```bash
   ollama pull mistral      # ~4GB, excellent quality
   ollama pull llama2       # ~4GB, good alternative
   ollama pull phi          # ~2GB, smaller/faster
   ```
4. Start Ollama server:
   ```bash
   ollama serve
   ```
   (Keep this running in background)

5. Test with our system:
   ```bash
   python main.py status
   ```

### Option B: HuggingFace Transformers (More Control)

**Setup:**

1. Models auto-download on first use (~4-7GB)
2. Update `config/settings.py`:
   ```python
   LLM_BACKEND = "transformers"
   HF_CONFIG["model_id"] = "mistralai/Mistral-7B-Instruct-v0.1"
   ```
3. No additional setup needed - models download automatically

---

## Usage

### Method 1: Command Line (Easiest)

Place audio file in `audio_input/` folder, then:

```bash
# Basic usage
python main.py summarize audio_input/meeting.mp3

# With meeting title
python main.py summarize audio_input/meeting.wav --title "Q1 Planning"

# Skip transcript (faster)
python main.py summarize meeting.m4a --no-save-transcript

# Get system info
python main.py info

# Check status
python main.py status
```

### Method 2: Python API

```python
from src.pipeline import MeetingSummarizerPipeline

# Initialize
pipeline = MeetingSummarizerPipeline()

# Process meeting
result = pipeline.process_meeting(
    "meeting.mp3",
    meeting_title="Team Standup"
)

# Access results
print(result['summary'])          # Executive summary
print(result['key_topics'])       # [topic1, topic2, ...]
print(result['decisions'])        # [decision1, decision2, ...]
print(result['action_items'])     # [{"task": ..., "owner": ..., "deadline": ...}, ...]
```

### Method 3: REST API

```bash
# Start server
python server.py
```

API available at http://localhost:8000

**Example request:**
```bash
curl -X POST "http://localhost:8000/summarize" \
  -F "file=@meeting.mp3" \
  -F "title=Team Meeting"
```

**Response:**
```json
{
  "success": true,
  "meeting_title": "Team Meeting",
  "summary": "The team discussed...",
  "key_topics": ["Product Development", "Timeline", ...],
  "decisions": ["Launch Q2 instead of Q3"],
  "action_items": [
    {
      "task": "Finalize requirements",
      "owner": "John",
      "deadline": "2024-02-15"
    }
  ]
}
```

---

## How the System Works

### 1. Audio Loading & Processing
```python
# Load audio (handles MP3, WAV, M4A, OGG, FLAC)
audio, sr = processor.load_audio("meeting.mp3")

# Automatically resamples to 16kHz (Whisper requirement)
# Splits long audio into 15-minute chunks (if >15 min)
```

**Why resampling?**
- Whisper expects 16kHz mono audio
- Reduces memory usage
- Consistent processing

### 2. Speech-to-Text (Whisper)

```python
# Transcribe with timestamps
transcription = stt.transcribe_long_audio(audio, sample_rate)
# Returns: {"text": "...", "segments": [...], "duration": ...}
```

**Key Features:**
- Multilingual support (auto-detects)
- Punctuation restoration
- Timestamp preservation
- Handles background noise well
- Chunking for memory efficiency

**Model Comparison:**
| Model | Size | Speed | Accuracy | VRAM |
|-------|------|-------|----------|------|
| tiny  | 39M  | Fast  | Low      | 1GB  |
| base  | 74M  | Good  | Medium   | 1GB  |
| **small** | **244M** | **~5min/hour** | **High** | **2GB** |
| medium | 769M | Slow | Very High | 5GB |
| large | 1.5B | Very Slow | Highest | 10GB |

*Recommendation: SMALL for laptops*

### 3. Text Preprocessing

```python
# Clean text (remove filler words, fix errors)
cleaned = preprocessor.clean_text(transcript)

# Split into chunks (~1500 tokens max)
chunks = preprocessor.split_into_chunks(cleaned)
```

**Preprocessing Steps:**
1. Remove extra whitespace
2. Fix Whisper errors ([music], repeated words)
3. Remove filler words (um, uh, like, you know)
4. Fix punctuation spacing
5. Split by sentences → chunk by token count

### 4. LLM Summarization

```python
# Initialize LLM (Ollama or Transformers)
summarizer = MeetingSummarizer()

# Generate structured summary
result = summarizer.summarize_transcript(cleaned_text)
# Returns:
# {
#   "summary": "Executive summary...",
#   "key_topics": [...],
#   "decisions": [...],
#   "action_items": [{"task": ..., "owner": ..., "deadline": ...}]
# }
```

**How it extracts information:**
1. **Summary**: Prompts LLM to create 2-3 paragraph overview
2. **Topics**: Asks LLM to identify main subjects
3. **Decisions**: Extracts what was decided
4. **Action Items**: Identifies tasks, owners, deadlines

### 5. Output Generation

```python
# Saves to outputs/ directory:
# - summary_YYYYMMDD_HHMMSS.json   (machine-readable)
# - summary_YYYYMMDD_HHMMSS.txt    (human-readable)
# - transcript_YYYYMMDD_HHMMSS.txt (full transcript)
```

---

## Output Format

### JSON Output (`summary_*.json`)

```json
{
  "meeting_title": "Q1 Planning Meeting",
  "duration": 45.5,
  "timestamp": "2024-01-20T14:30:00",
  "summary": "The team met to plan Q1 objectives...",
  "key_topics": [
    "Product roadmap",
    "Team capacity",
    "Timeline adjustments"
  ],
  "decisions": [
    "Launch Phase 2 in March",
    "Allocate 2 engineers to research"
  ],
  "action_items": [
    {
      "task": "Complete architecture design",
      "owner": "Alice",
      "deadline": "2024-02-15"
    },
    {
      "task": "Update project timeline",
      "owner": "Bob",
      "deadline": "2024-01-25"
    }
  ],
  "metadata": {
    "language": "English",
    "num_segments": 342,
    "processing_stages": {...}
  }
}
```

### Text Output (`summary_*.txt`)

```
================================================================================
MEETING SUMMARY: Q1 Planning Meeting
================================================================================

Date/Time: 2024-01-20T14:30:00
Duration: 45.5 minutes

--------------------------------------------------------------------------------
EXECUTIVE SUMMARY
--------------------------------------------------------------------------------
The team met to plan Q1 objectives and discuss resource allocation...

--------------------------------------------------------------------------------
KEY TOPICS
--------------------------------------------------------------------------------
1. Product roadmap
2. Team capacity planning
3. Timeline adjustments for Phase 2

[... rest of topics ...]

--------------------------------------------------------------------------------
DECISIONS
--------------------------------------------------------------------------------
1. Launch Phase 2 in March instead of April
2. Allocate 2 engineers to research tasks

[... rest of decisions ...]

--------------------------------------------------------------------------------
ACTION ITEMS
--------------------------------------------------------------------------------
1. Complete architecture design
   Owner: Alice
   Deadline: 2024-02-15

2. Update project timeline
   Owner: Bob
   Deadline: 2024-01-25

[... rest of action items ...]
```

---

## Performance Tips for Laptops

### 1. Audio Preprocessing
```python
# Trim silence at beginning/end (saves processing time)
trimmed = librosa.effects.trim(audio)

# Reduce bit depth (if memory-constrained)
audio = audio.astype(np.float16)
```

### 2. Model Selection
```python
# For 8GB RAM: Use SMALL Whisper + Mistral 7B
# For 16GB+ RAM: Use MEDIUM Whisper + Mistral 7B

# For speed priority: Use TINY/BASE Whisper
# For accuracy priority: Use MEDIUM/LARGE Whisper
```

### 3. Chunk Processing
```python
# Larger chunks = faster but uses more memory
# Smaller chunks = slower but less memory
WHISPER_CHUNK_DURATION = 600  # 10 min chunks (faster on 8GB)
WHISPER_CHUNK_DURATION = 1200 # 20 min chunks (for 16GB+)
```

### 4. LLM Optimization
```python
# In config/settings.py:
ENABLE_MEMORY_OPTIMIZATION = True  # Enable for laptop

# With Ollama, configure:
ollama run mistral --options="num_thread=4 num_gpu=1"
```

### 5. Parallel Processing (Future)
```python
# Currently: Process one file at a time
# Can add: Process multiple files in queue mode
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'whisper'"
```bash
# Solution: Install openai-whisper
pip install openai-whisper
```

### Issue: "CUDA out of memory"
```python
# Solution: Use CPU instead
WHISPER_CONFIG["device"] = "cpu"
# Or use smaller model
WHISPER_MODEL = WhisperModel.TINY.value
```

### Issue: "Ollama not running"
```bash
# Solution: Start Ollama server in new terminal
ollama serve
```

### Issue: "Model not found: mistral"
```bash
# Solution: Download model first
ollama pull mistral
```

### Issue: "ffmpeg not found"
```bash
# Solution: Install ffmpeg
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg
# Linux: apt-get install ffmpeg
```

### Issue: Slow transcription (>10 min per hour)
```python
# Solution 1: Use smaller Whisper model
WHISPER_MODEL = WhisperModel.TINY.value

# Solution 2: Use GPU (CUDA)
WHISPER_CONFIG["device"] = "cuda"

# Solution 3: Increase chunk size (trades accuracy)
WHISPER_CHUNK_DURATION = 1200  # 20 min chunks
```

---

## Architecture Decisions Explained

### Why Whisper for STT?
- ✓ State-of-the-art accuracy
- ✓ Handles accents, background noise
- ✓ Open-source, no API costs
- ✓ Multilingual support
- ✓ Already trained on 680k hours of audio

### Why Ollama for LLM?
- ✓ Easy setup (single install)
- ✓ No configuration needed
- ✓ Pre-optimized models
- ✓ Works without internet
- ✓ Good speed (~5 tokens/sec on CPU)

**Alternative: HuggingFace Transformers**
- More control over inference
- Custom prompt formatting
- Fine-tuning support
- Requires more setup

### Why Local Processing?
- ✓ Privacy (data never leaves device)
- ✓ No API costs
- ✓ Works offline
- ✓ No rate limits
- ✓ Suitable for sensitive meetings

### Why Chunking?
- ✓ Prevents memory overflow
- ✓ Whisper handles 15-30 min chunks optimally
- ✓ LLM context length limits (~2000 tokens)
- ✓ Enables processing of unlimited-length meetings

---

## Advanced Usage

### Custom Prompt Templates

Edit `prompts/summarize.txt` to customize summary style:

```
You are a meeting summarization AI specialized in technical discussions.
Extract:
1. Technical decisions made
2. Architecture changes
3. Timeline impacts

Focus on: implementation details, code changes, technical risks.
```

### Custom Filler Words

In `config/settings.py`:

```python
FILLER_WORDS = {
    "um", "uh", "like", "basically",
    # Add custom words here
}
```

### Programmatic Usage

```python
from src.modules.audio_processor import AudioProcessor
from src.modules.speech_to_text import SpeechToText
from src.modules.llm_summarizer import MeetingSummarizer

# Load audio
processor = AudioProcessor()
audio, sr = processor.load_audio("meeting.mp3")

# Transcribe
stt = SpeechToText()
transcript = stt.transcribe_long_audio(audio, sr)

# Summarize
summarizer = MeetingSummarizer()
result = summarizer.summarize_transcript(transcript["text"])

# Access results
print(result["summary"])
print(result["action_items"])
```

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 8GB | 16GB |
| **CPU** | i5 (4 cores) | i7/Ryzen7 (8+ cores) |
| **GPU** | None | NVIDIA (4GB VRAM) |
| **Disk** | 20GB | 50GB |
| **Python** | 3.9 | 3.10-3.11 |
| **ffmpeg** | Required | Required |

### Storage Breakdown
- Whisper model: ~500MB (SMALL)
- Mistral 7B: ~4GB
- Sample audio files: ~100MB per hour
- Dependencies: ~2GB

---

## Performance Metrics

**Typical Processing Times (on Intel i7, 8GB RAM)**

| Component | Duration |
|-----------|----------|
| Load model (first run) | ~30 seconds |
| Transcribe 1 hour audio | ~15-20 minutes |
| Clean & preprocess | ~2 seconds |
| Summarization (via LLM) | ~10-20 seconds |
| **Total for 1-hour meeting** | **~15-20 minutes** |

**With GPU (NVIDIA 3060)**
- Transcription: ~3-5 minutes (4x faster)
- Total: ~4-6 minutes

---

## Limitations & Future Improvements

### Current Limitations
- No speaker diarization (can't identify who said what)
- Single language per meeting
- No conversation turn detection
- Basic action item extraction

### Planned Features
- [ ] Speaker diarization (identify speakers)
- [ ] Multiple summary styles (bullet, narrative, technical)
- [ ] Meeting participant tracking
- [ ] Automatic meeting categorization
- [ ] Integration with calendar APIs
- [ ] Web dashboard UI
- [ ] Batch processing multiple meetings
- [ ] Custom model fine-tuning

---

## License & Attribution

This system uses:
- **Whisper**: OpenAI (MIT License)
- **Ollama**: Local Large Language Models
- **FastAPI**: Modern Python API framework
- **Librosa**: Audio analysis library

All code in this project is open and available for modification.

---

## Support & Contribution

For issues, suggestions, or contributions, refer to the code documentation in each module.

Key contact points:
- `config/settings.py` - Configuration
- `src/pipeline.py` - Main orchestrator
- `main.py` - CLI entry point

---

## Quick Start Summary

```bash
# 1. Install
pip install -r requirements.txt
apt-get install ffmpeg  # or brew/choco on Mac/Windows

# 2. Setup LLM (Ollama recommended)
# Download from ollama.ai, then:
ollama pull mistral
ollama serve  # In background

# 3. Run
python main.py summarize audio_input/meeting.mp3

# 4. Check outputs
ls outputs/
cat outputs/summary_*.txt
```

Done! Your meeting is summarized. 🎉

---

**Version:** 1.0.0  
**Last Updated:** January 2024  
**Python:** 3.9+  
**License:** MIT
