"""
Utility functions for logging, file operations, and data validation
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
import os

from config.settings import LOGS_DIR, LOG_LEVEL, LOG_FILE, SUPPORTED_AUDIO_FORMATS

# ============================================================================
# LOGGING SETUP
# ============================================================================
def setup_logging(name: str = "MeetingSummarizer") -> logging.Logger:
    """
    Initialize logging configuration
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Avoid duplicate handlers if logger already configured
    if logger.hasHandlers():
        return logger
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()

# ============================================================================
# FILE OPERATIONS
# ============================================================================
def validate_audio_file(file_path: str) -> tuple[bool, str]:
    """
    Validate audio file existence and format
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        return False, f"Audio file not found: {file_path}"
    
    # Check file extension
    if path.suffix.lower() not in SUPPORTED_AUDIO_FORMATS:
        supported = ", ".join(SUPPORTED_AUDIO_FORMATS)
        return False, f"Unsupported format. Supported: {supported}"
    
    # Check file size
    file_size_gb = path.stat().st_size / (1024**3)
    if file_size_gb > 5:
        return False, f"File too large ({file_size_gb:.1f}GB). Max: 5GB"
    
    return True, "OK"


def get_timestamp_string(include_date: bool = True) -> str:
    """
    Get current timestamp as string for file naming
    
    Args:
        include_date: Include date in timestamp
        
    Returns:
        Formatted timestamp string
    """
    if include_date:
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        return datetime.now().strftime("%H%M%S")


def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load JSON file with error handling
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Dictionary loaded from JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Loaded JSON from {file_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise
    except FileNotFoundError:
        logger.error(f"JSON file not found: {file_path}")
        raise


def save_json(data: Dict[str, Any], file_path: str) -> bool:
    """
    Save dictionary to JSON file with pretty printing
    
    Args:
        data: Dictionary to save
        file_path: Output file path
        
    Returns:
        True if successful
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        return False


def save_text(content: str, file_path: str) -> bool:
    """
    Save text content to file
    
    Args:
        content: Text content to save
        file_path: Output file path
        
    Returns:
        True if successful
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved text to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save text to {file_path}: {e}")
        return False


# ============================================================================
# DATA VALIDATION AND CLEANING
# ============================================================================
def validate_transcript(transcript: str) -> bool:
    """
    Validate transcript is not empty
    
    Args:
        transcript: Transcript text
        
    Returns:
        True if valid
    """
    if not transcript or len(transcript.strip()) < 10:
        logger.warning("Transcript is empty or too short")
        return False
    return True


def format_duration(seconds: float) -> str:
    """
    Convert seconds to HH:MM:SS format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# ============================================================================
# PROMPT MANAGEMENT
# ============================================================================
def load_prompt_template(template_name: str) -> str:
    """
    Load LLM prompt template
    
    Args:
        template_name: Name of prompt template (e.g., 'summarize', 'extract_actions')
        
    Returns:
        Prompt template string
    """
    prompt_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompt_dir / f"{template_name}.txt"
    
    if not prompt_file.exists():
        logger.warning(f"Prompt template not found: {template_name}")
        return ""
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================
class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.elapsed = 0
    
    def __enter__(self):
        self.start_time = datetime.now()
        logger.info(f"Started: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = (datetime.now() - self.start_time).total_seconds()
        status = "completed" if exc_type is None else "failed"
        logger.info(f"{self.operation_name.capitalize()} {status} in {self.elapsed:.2f}s")
        return False


# ============================================================================
# MEMORY OPTIMIZATION HELPERS
# ============================================================================
def clear_cache():
    """Clear CUDA cache to free GPU memory"""
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.debug("Cleared CUDA cache")
    except Exception as e:
        logger.debug(f"Could not clear cache: {e}")


if __name__ == "__main__":
    # Test logging
    logger.info("Utilities module initialized")
    logger.debug("Debug message test")
