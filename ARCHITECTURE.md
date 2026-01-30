# SYSTEM ARCHITECTURE DOCUMENTATION

## High-Level System Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER INPUT LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│   │   CLI Interface  │  │   Python API     │  │  REST API        │    │
│   │   (main.py)      │  │ (Direct import)  │  │ (server.py)      │    │
│   └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘    │
│            │                     │                      │               │
└────────────┼─────────────────────┼──────────────────────┼───────────────┘
             │                     │                      │
             └─────────────────────┴──────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                    MeetingSummarizerPipeline                            │
│                        (src/pipeline.py)                                │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  • Coordinates all modules                                      │  │
│   │  • Manages error handling & retries                            │  │
│   │  • Tracks processing stages                                     │  │
│   │  • Generates structured outputs                                │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└────────────────────┬──────────────────────────────────────┬──────────────┘
                     │                                      │
          ┌──────────┴───────────────────────┬──────────────┴─────────┐
          │                                  │                        │
          ▼                                  ▼                        ▼
┌──────────────────────┐         ┌──────────────────┐    ┌──────────────────┐
│  AUDIO LAYER         │         │  STT LAYER       │    │  TEXT PROCESSING │
├──────────────────────┤         ├──────────────────┤    ├──────────────────┤
│ AudioProcessor       │         │ SpeechToText     │    │ TextPreprocessor │
│ (audio_processor.py) │         │ (speech_to..py)  │    │ (text_preproc..) │
│                      │         │                  │    │                  │
│ • Load audio files   │         │ • Whisper model  │    │ • Clean text     │
│ • Validate format    │         │ • Chunk audio    │    │ • Remove filler  │
│ • Resample to 16kHz  │         │ • Generate       │    │ • Split chunks   │
│ • Chunk long audio   │         │   timestamps     │    │ • Extract topics │
│ • Normalize levels   │         │ • Extract lang   │    │ • Count tokens   │
│                      │         │                  │    │                  │
└──────────────────────┘         └──────────────────┘    └──────────────────┘
          │                                  │                        │
          └──────────────────┬───────────────┴────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LLM SUMMARIZATION LAYER                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                    MeetingSummarizer                                    │
│                   (llm_summarizer.py)                                   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │  LLM Backend Interface                                          │  │
│   │  ├─ Ollama (recommended)                                        │  │
│   │  └─ HuggingFace Transformers                                   │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   Extracts:                                                             │
│   • Executive Summary                                                   │
│   • Key Topics (auto-detected)                                         │
│   • Decisions Made                                                      │
│   • Action Items (who/what/when)                                       │
│                                                                          │
└──────────────────────────────────────────┬───────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        OUTPUT GENERATION                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐      ┌──────────────────┐     ┌─────────────────┐│
│  │  JSON Output     │      │  Text Output     │     │ Transcript      ││
│  │  (Machine)       │      │  (Human)         │     │ (Timestamped)   ││
│  │                  │      │                  │     │                 ││
│  │ summary_*.json   │      │ summary_*.txt    │     │ transcript_*.tx ││
│  │                  │      │                  │     │                 ││
│  │ • Structured     │      │ • Formatted      │     │ • Full text     ││
│  │ • Easy parsing   │      │ • Easy reading   │     │ • With times    ││
│  │ • For systems    │      │ • For humans     │     │ • For reference ││
│  └──────────────────┘      └──────────────────┘     └─────────────────┘│
│                                                                          │
│                         (outputs/ folder)                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Module Architecture

### 1. Audio Processing Module

```python
AudioProcessor
├── load_audio(file_path)
│   ├─ Validates file format
│   ├─ Loads with librosa
│   └─ Resamples to 16kHz (Whisper requirement)
│
├── get_audio_info(file_path)
│   └─ Returns: duration, file size, format info
│
├── chunk_audio(audio, chunk_duration)
│   ├─ Splits long audio into 15-min chunks
│   ├─ Adds 30s overlap for context
│   └─ Returns: List of audio arrays
│
├── normalize_audio(audio)
│   └─ Normalizes to [-1, 1] range
│
└── export_audio(audio, output_path)
    └─ Saves audio to file (for testing)
```

**Key Design Decisions:**
- Uses librosa (handles all audio formats)
- Automatic resampling (16kHz is Whisper standard)
- Chunking strategy: prevents memory overflow
- 30s overlap: maintains context between chunks

---

### 2. Speech-to-Text Module

```python
SpeechToText
├── __init__(model_name, device)
│   ├─ Loads Whisper model lazily (first use)
│   └─ Supports: tiny, base, small, medium, large
│
├── transcribe_chunk(audio_chunk)
│   ├─ Transcribes single chunk
│   └─ Returns: {"text": ..., "segments": ..., "language": ...}
│
└── transcribe_long_audio(audio, sample_rate, chunk_duration)
    ├─ Handles long audio (>15 min)
    ├─ Processes chunks sequentially
    ├─ Merges results with time preservation
    └─ Returns: Full transcript with metadata

TranscriptCleaner
├── merge_short_segments(segments)
│   └─ Merges fragments <1s (reduces noise)
│
├── remove_duplicates(segments)
│   └─ Removes overlapping text from chunks
│
└── format_transcript(segments)
    └─ Formats as "[HH:MM:SS] text" per segment
```

**Why Two Classes?**
- `SpeechToText`: Handles transcription
- `TranscriptCleaner`: Post-processing & formatting
- Separation of concerns

---

### 3. Text Preprocessing Module

```python
TextPreprocessor
├── __init__()
│   └─ Initializes NLTK tokenizers
│
├── clean_text(text)
│   ├─ Removes extra whitespace
│   ├─ Fixes Whisper errors ([music], etc.)
│   ├─ Removes filler words (um, uh, like)
│   └─ Normalizes punctuation
│
├── _fix_common_errors(text)
│   ├─ Removes [music], [applause] tags
│   └─ Removes repeated words
│
├── split_into_chunks(text, max_tokens)
│   ├─ Splits by sentences first (NLTK)
│   ├─ Combines sentences until token limit
│   ├─ Prevents breaking mid-sentence
│   └─ Returns: List of text chunks
│
└── extract_key_phrases(text)
    └─ Extracts important words/topics

TokenCounter
├── count_tokens_approximate(text)
│   └─ Rule: ~1 token = 4 characters
│
└── count_tokens_nltk(text)
    └─ More accurate using word tokenization
```

**Chunking Strategy:**
```
Text: "Sentence 1. Sentence 2. Sentence 3. Sentence 4."
      └─ Split by sentences → [S1, S2, S3, S4]
      └─ Combine: [S1+S2], [S3+S4] (each ≤max_tokens)
      └─ Output: 2 chunks
```

---

### 4. LLM Summarization Module

```python
LLMInterface
├── __init__(backend: str)
│   ├─ "ollama" → Ollama backend
│   └─ "transformers" → HuggingFace backend
│
├── _init_ollama()
│   ├─ Connects to http://localhost:11434
│   ├─ Verifies model availability
│   └─ Sets temperature, top_p params
│
├── _init_transformers()
│   ├─ Downloads model from HuggingFace
│   ├─ Loads to GPU or CPU
│   └─ Initializes tokenizer
│
└── generate(prompt, max_tokens)
    ├─ "ollama" → Calls ollama client
    └─ "transformers" → Calls model.generate()

MeetingSummarizer
├── __init__(llm_backend)
│   └─ Initializes LLMInterface
│
├── summarize_transcript(transcript, style)
│   └─ Orchestrates all extraction methods
│
├── _generate_summary(transcript)
│   ├─ Prompt: Generate 2-3 paragraph overview
│   └─ Returns: Executive summary string
│
├── _extract_topics(transcript)
│   ├─ Prompt: Identify main topics
│   ├─ Parses bullet points
│   └─ Returns: List of topics
│
├── _extract_decisions(transcript)
│   ├─ Prompt: What was decided?
│   └─ Returns: List of decisions
│
└── _extract_action_items(transcript)
    ├─ Prompt: Extract task/owner/deadline
    ├─ Parses structured format
    └─ Returns: List of action items
```

**Backend Comparison:**

| Aspect | Ollama | Transformers |
|--------|--------|--------------|
| Setup | 1 download | Auto-download |
| Config | Minimal | Code-based |
| Speed | ~5 tok/s | ~3 tok/s |
| GPU | Yes | Yes |
| Flexibility | Low | High |
| Code Changes | None | Edit code |

---

### 5. Pipeline Orchestrator

```python
MeetingSummarizerPipeline
│
├── __init__()
│   └─ Initializes all modules
│
└── process_meeting(audio_file, title, save_transcript)
    │
    ├─ STAGE 1: Load Audio
    │   └─ AudioProcessor.load_audio()
    │
    ├─ STAGE 2: Transcribe
    │   └─ SpeechToText.transcribe_long_audio()
    │
    ├─ STAGE 3: Clean Transcript
    │   ├─ TranscriptCleaner.merge_short_segments()
    │   ├─ TranscriptCleaner.remove_duplicates()
    │   ├─ TextPreprocessor.clean_text()
    │   └─ Format for output
    │
    ├─ STAGE 4: Chunk Text
    │   └─ TextPreprocessor.split_into_chunks()
    │
    ├─ STAGE 5: Summarize
    │   └─ MeetingSummarizer.summarize_transcript()
    │
    ├─ STAGE 6: Save Outputs
    │   ├─ JSON (summary_*.json)
    │   ├─ TXT (summary_*.txt)
    │   └─ Transcript (transcript_*.txt)
    │
    └─ Returns: Complete result dict with metadata

_save_outputs()
├─ Creates JSON with structured data
├─ Creates readable text summary
└─ Creates full transcript (optional)

_format_text_summary()
└─ Formats JSON data as readable text
```

---

## Data Flow Diagram

```
AUDIO FILE
    │
    ├─ [librosa] Load + resample to 16kHz
    │
    ▼
AUDIO ARRAY (np.ndarray)
    │
    ├─ [If >15 min] Split into chunks
    │
    ▼
AUDIO CHUNKS
    │
    ├─ [Whisper] Transcribe each chunk
    │
    ▼
SEGMENTS + RAW TEXT
    ├─ [TranscriptCleaner] Merge short, remove dups
    │
    ▼
CLEAN SEGMENTS
    │
    ├─ [Format] Convert to "[HH:MM:SS] text" format
    │
    ├─────────────────────────────┐
    │                             │
    ▼                             ▼
  TEXT                     FORMATTED TRANSCRIPT
  │                        (for output file)
  │
  ├─ [Clean] Remove filler words, fix errors
  │
  ▼
CLEANED TEXT
  │
  ├─ [Split] Chunk by sentences + tokens
  │
  ▼
TEXT CHUNKS (list of strings)
  │
  ├─ [LLM] Summarize each chunk
  │
  ▼
SUMMARY COMPONENTS
  ├─ summary (string)
  ├─ key_topics (list)
  ├─ decisions (list)
  └─ action_items (list of dicts)
      │
      └─ {"task": ..., "owner": ..., "deadline": ...}
  │
  ▼
STRUCTURED RESULT
  │
  ├─ [JSON] Save as summary_*.json
  ├─ [TXT] Save as summary_*.txt
  └─ [TXT] Save as transcript_*.txt
```

---

## Memory Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        RAM USAGE                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Audio Buffer (largest):                                    │
│  ├─ 1 hour audio @ 16kHz = 16000 * 3600 * 2 bytes ≈ 100MB │
│  └─ With chunking: max 15 min = ~25MB at a time            │
│                                                              │
│  Whisper Model:                                             │
│  ├─ SMALL: ~500MB                                          │
│  └─ Loaded once, reused                                    │
│                                                              │
│  Transcription Results:                                     │
│  ├─ Segments list: ~1KB per minute                         │
│  └─ 1 hour = ~60KB                                         │
│                                                              │
│  Text Processing:                                           │
│  ├─ Full transcript in memory: ~50-100KB per hour          │
│  ├─ Text chunks: processed one at a time                   │
│  └─ NLTK/spaCy models: ~50-200MB                           │
│                                                              │
│  LLM Model:                                                │
│  ├─ Mistral 7B: ~14GB (quantized: ~4GB)                   │
│  ├─ Loaded for entire session                              │
│  └─ GPU VRAM if available                                  │
│                                                              │
│  TOTAL for 1-hour meeting:                                 │
│  ├─ With CPU: ~5-7GB (Whisper + LLM in RAM)               │
│  ├─ With GPU: ~1GB (text, Whisper) + VRAM (LLM)          │
│  └─ Peak: When both models loaded                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘

OPTIMIZATION STRATEGIES:
1. Model Lazy Loading: Load on first use
2. Audio Chunking: Process 15 min at a time
3. Text Chunking: Process one chunk at a time
4. Memory Clearing: Clear CUDA cache between batches
5. Quantization: Use quantized models (~4GB instead of 14GB)
```

---

## Error Handling Architecture

```python
┌─────────────────────────────────────────────┐
│         Error Handling Strategy             │
├─────────────────────────────────────────────┤
│                                             │
│  Try-Except at Module Level:                │
│  ├─ audio_processor.py: FileNotFoundError   │
│  ├─ speech_to_text.py: Model loading       │
│  ├─ text_preprocessor.py: Text errors      │
│  └─ llm_summarizer.py: LLM connection      │
│                                             │
│  Error Propagation:                         │
│  └─ Modules raise exceptions               │
│  └─ Pipeline catches & logs                │
│  └─ Caller gets error with context         │
│                                             │
│  Logging Hierarchy:                         │
│  ├─ DEBUG: Detailed processing info        │
│  ├─ INFO: Major milestones                 │
│  ├─ WARNING: Non-critical issues           │
│  └─ ERROR: Failures requiring attention    │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Configuration Architecture

```python
config/settings.py
│
├─ PATHS
│  ├─ PROJECT_ROOT: Base directory
│  ├─ AUDIO_INPUT_DIR: Where to place audio
│  ├─ OUTPUT_DIR: Where summaries go
│  └─ LOGS_DIR: Debug logs
│
├─ WHISPER CONFIG
│  ├─ WHISPER_MODEL: tiny/base/small/medium/large
│  ├─ WHISPER_CONFIG["device"]: cuda/cpu
│  ├─ WHISPER_CHUNK_DURATION: 15 min default
│  └─ SAMPLE_RATE: 16000 Hz
│
├─ LLM CONFIG
│  ├─ LLM_BACKEND: ollama/transformers
│  ├─ LLM_MODEL: Mistral/Llama/Phi/etc
│  ├─ OLLAMA_CONFIG: URL, temp, top_p
│  └─ HF_CONFIG: Model ID, device, tokens
│
├─ TEXT PROCESSING
│  ├─ MAX_TOKENS_PER_CHUNK: 1500
│  ├─ FILLER_WORDS: Set of words to remove
│  └─ MIN_SUMMARY_LENGTH: 100 chars
│
└─ PERFORMANCE
   ├─ BATCH_SIZE: 1 (one file at a time)
   ├─ NUM_WORKERS: 0 (avoid multiprocessing)
   └─ ENABLE_MEMORY_OPTIMIZATION: True
```

---

## Performance Characteristics

```
TIMING BREAKDOWN (1-hour meeting, i7, 8GB RAM):

Audio Loading:        ~5 seconds
├─ File I/O
└─ Resampling

Speech-to-Text:       ~15 minutes ⭐ (longest phase)
├─ Whisper inference
└─ Chunking overhead

Text Preprocessing:   ~2 seconds
├─ Cleaning
└─ Chunking

LLM Summarization:    ~15 seconds
├─ Summary generation
├─ Topic extraction
├─ Decision extraction
└─ Action item parsing

Output Generation:    ~1 second
├─ JSON writing
└─ Text formatting

TOTAL:               ~15 minutes

WITH GPU (NVIDIA 3060):
├─ STT: ~3 minutes (5x faster)
├─ Total: ~4 minutes
└─ Improvement: 4x faster
```

---

## Scalability Considerations

```
CURRENT (v1.0):
├─ One file at a time (sequential)
├─ Full model loading per session
└─ Limited to available RAM/VRAM

POTENTIAL (Future):
├─ Queue-based batch processing
├─ Model pooling across files
├─ Streaming processing for real-time
├─ Distributed processing (multi-machine)
└─ Model quantization for speed
```

---

## External Dependencies

```
CRITICAL (System won't work without):
├─ Python 3.9+ (language)
├─ pip (package manager)
├─ ffmpeg (audio processing)
├─ CUDA 11.8+ (optional, for GPU)
└─ Ollama or HuggingFace (LLM)

PYTHON PACKAGES (auto-installed):
├─ torch: Deep learning (required by Whisper)
├─ transformers: Hugging Face models
├─ librosa: Audio processing
├─ numpy: Numerical computing
├─ nltk: Text processing
├─ fastapi: REST API framework
└─ ollama: Ollama client library
```

---

This architecture is designed for:
- ✓ Modularity (easy to swap components)
- ✓ Extensibility (add new features)
- ✓ Maintainability (clear separation)
- ✓ Performance (optimized for laptops)
- ✓ Reliability (error handling)
