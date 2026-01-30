"""
Global configuration settings for the Meeting Summarizer
Manages all constants, paths, and environment variables
"""

import os
from pathlib import Path
from enum import Enum

# ============================================================================
# PROJECT STRUCTURE
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
AUDIO_INPUT_DIR = PROJECT_ROOT / "audio_input"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
LOGS_DIR = PROJECT_ROOT / "logs"
SRC_DIR = PROJECT_ROOT / "src"

# Create directories if they don't exist
for directory in [AUDIO_INPUT_DIR, OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# WHISPER CONFIGURATION
# ============================================================================
class WhisperModel(Enum):
    """Available Whisper models - trade-off between speed and accuracy"""
    TINY = "tiny"          # Fastest, ~39M params, lowest accuracy
    BASE = "base"          # Balanced, ~74M params
    SMALL = "small"        # Good quality, ~244M params
    MEDIUM = "medium"      # High quality, ~769M params (4GB VRAM)
    LARGE = "large"        # Highest accuracy, ~1.5B params (requires 10GB+ VRAM)

# Default for laptop: SMALL (good balance between speed and accuracy)
WHISPER_MODEL = WhisperModel.SMALL.value

# Whisper model configurations
WHISPER_CONFIG = {
    "model_name": WHISPER_MODEL,
    "device": "cuda",  # or "cpu" if CUDA not available
    "language": "en",
    "task": "transcribe",  # or "translate"
}

# Audio chunk size for Whisper (prevents memory overflow)
# Whisper works best with audio chunks of 15-30 minutes
WHISPER_CHUNK_DURATION = 900  # 15 minutes in seconds

# ============================================================================
# LLM CONFIGURATION
# ============================================================================
class LLMBackend(Enum):
    """Supported LLM backends for local execution"""
    OLLAMA = "ollama"
    TRANSFORMERS = "transformers"

class LLMModel(Enum):
    """Recommended models for laptop execution"""
    MISTRAL_7B = "mistral:7b"
    LLAMA2_7B = "llama2:7b"
    NEURAL_CHAT = "neural-chat"
    PHI = "phi"

# Choose backend and model
# OLLAMA is recommended: pre-optimized, easier setup
# TRANSFORMERS gives more control but requires more setup
LLM_BACKEND = LLMBackend.OLLAMA.value
LLM_MODEL = LLMModel.MISTRAL_7B.value

# Ollama configuration
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": LLM_MODEL,
    "temperature": 0.3,  # Lower = more deterministic, better for summaries
    "top_p": 0.9,
}

# HuggingFace Transformers configuration (if using TRANSFORMERS backend)
HF_CONFIG = {
    "model_id": "mistralai/Mistral-7B-Instruct-v0.1",
    "device": "cuda",  # or "cpu"
    "max_new_tokens": 512,
    "temperature": 0.3,
    "top_p": 0.9,
}

# ============================================================================
# TEXT PROCESSING
# ============================================================================
# Maximum tokens per chunk for LLM processing
# Keep under 2000 to avoid context length issues
MAX_TOKENS_PER_CHUNK = 1500

# Filler words to remove during preprocessing
FILLER_WORDS = {
    "um", "uh", "er", "ah", "hmm", "you know", "i mean", "like",
    "basically", "actually", "honestly", "literally", "right",
    "okay", "so", "just"
}

# Minimum summary length (to avoid truncated outputs)
MIN_SUMMARY_LENGTH = 100

# ============================================================================
# OUTPUT FORMATS
# ============================================================================
OUTPUT_FORMATS = {
    "json": "structured_summary_{timestamp}.json",
    "txt": "summary_{timestamp}.txt",
    "transcript": "transcript_{timestamp}.txt",
}

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL = "INFO"
LOG_FILE = LOGS_DIR / "meeting_summarizer.log"

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================
# For laptop optimization:
# - Batch size: 1 (process one audio file at a time)
# - Num workers: 0 (avoid multiprocessing overhead)
# - Enable memory optimization for LLM
BATCH_SIZE = 1
NUM_WORKERS = 0
ENABLE_MEMORY_OPTIMIZATION = True  # For Whisper and LLM

# ============================================================================
# AUDIO PROCESSING
# ============================================================================
# Target sample rate for Whisper (must be 16000 Hz)
SAMPLE_RATE = 16000

# Audio format support
SUPPORTED_AUDIO_FORMATS = (".wav", ".mp3", ".m4a", ".ogg", ".flac")

# Maximum audio file size (5GB - adjust for your storage)
MAX_AUDIO_FILE_SIZE_GB = 5

print(f"✓ Configuration loaded from {Path(__file__)}")
print(f"  - Project root: {PROJECT_ROOT}")
print(f"  - Whisper model: {WHISPER_MODEL}")
print(f"  - LLM backend: {LLM_BACKEND}")
print(f"  - LLM model: {LLM_MODEL}")
