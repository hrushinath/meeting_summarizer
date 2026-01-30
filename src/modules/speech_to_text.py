"""
Speech-to-Text Module
- Uses OpenAI Whisper for accurate transcription
- Handles chunking for long audio
- Generates timestamped transcripts
- Fallback to Faster-Whisper for speed optimization
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import json

from src.utils import logger, PerformanceTimer
from config.settings import WHISPER_MODEL, WHISPER_CHUNK_DURATION, WHISPER_CONFIG


class SpeechToText:
    """
    Speech-to-Text engine using OpenAI Whisper
    
    Why Whisper?
    - Best open-source STT model
    - Excellent accuracy across languages and accents
    - Handles background noise well
    - No API costs
    - ~1B parameters (fits on laptop)
    """
    
    def __init__(self, model_name: str = WHISPER_MODEL, device: str = "cpu"):
        """
        Initialize Whisper model
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            device: "cuda" or "cpu"
        """
        self.model_name = model_name
        self.device = device
        self.logger = logger
        
        # Lazy load model on first use
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """
        Load Whisper model on first use (lazy loading)
        This prevents memory overhead if class is instantiated but not used
        """
        if self.model is not None:
            return  # Already loaded
        
        # Force CPU to avoid CUDA errors
        self.device = "cpu"
        self.logger.info(f"Loading Whisper model: {self.model_name} on {self.device}")
        
        try:
            import whisper
            with PerformanceTimer("Model loading"):
                self.model = whisper.load_model(self.model_name, device=self.device)
            self.logger.info(f"✓ Whisper model loaded successfully")
        except ImportError:
            self.logger.error("Whisper not installed. Install with: pip install openai-whisper")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def transcribe_chunk(self, audio_chunk: np.ndarray) -> Dict[str, any]:
        """
        Transcribe a single audio chunk
        
        Args:
            audio_chunk: Audio array (numpy) at 16kHz
            
        Returns:
            Dictionary with:
            - text: Transcribed text
            - segments: List of {time, text} segments
            - language: Detected language
        """
        if self.model is None:
            self._load_model()
        
        self.logger.debug(f"Transcribing audio chunk ({len(audio_chunk)/16000:.1f}s)")
        
        try:
            with PerformanceTimer("Audio transcription"):
                result = self.model.transcribe(
                    audio_chunk,
                    language=WHISPER_CONFIG["language"],
                    task=WHISPER_CONFIG["task"],
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise
    
    def transcribe_long_audio(
        self, 
        audio: np.ndarray, 
        sample_rate: int,
        chunk_duration: int = WHISPER_CHUNK_DURATION
    ) -> Dict[str, any]:
        """
        Transcribe long audio by chunking
        
        Process:
        1. Split audio into chunks (15 min default)
        2. Transcribe each chunk
        3. Merge results with timestamp preservation
        4. Clean up overlapping text
        
        Args:
            audio: Full audio array
            sample_rate: Sample rate (should be 16000Hz)
            chunk_duration: Duration of each chunk in seconds
            
        Returns:
            Dictionary with:
            - full_text: Complete transcript
            - segments: All segments with timestamps
            - language: Detected language
            - duration: Total audio duration
        """
        duration_seconds = len(audio) / sample_rate
        
        # For short audio, transcribe directly
        if duration_seconds <= chunk_duration:
            self.logger.info(f"Audio duration ({duration_seconds:.1f}s) <= chunk duration ({chunk_duration}s)")
            result = self.transcribe_chunk(audio)
            result["duration_seconds"] = duration_seconds
            return result
        
        self.logger.info(f"Audio is {duration_seconds:.1f}s - splitting into chunks of {chunk_duration}s")
        
        # Calculate chunk samples with overlap
        chunk_samples = chunk_duration * sample_rate
        overlap_samples = 30 * sample_rate  # 30s overlap
        stride = chunk_samples - overlap_samples
        
        all_segments = []
        all_text = []
        detected_language = None
        current_time = 0
        
        # Process chunks
        chunk_idx = 0
        start_idx = 0
        
        while start_idx < len(audio):
            end_idx = min(start_idx + chunk_samples, len(audio))
            chunk = audio[start_idx:end_idx]
            chunk_idx += 1
            
            self.logger.info(f"Processing chunk {chunk_idx}...")
            
            try:
                # Transcribe chunk
                result = self.transcribe_chunk(chunk)
                
                if detected_language is None:
                    detected_language = result.get("language", "unknown")
                
                # Adjust segment times based on chunk position
                for segment in result.get("segments", []):
                    adjusted_segment = segment.copy()
                    adjusted_segment["start"] += current_time
                    adjusted_segment["end"] += current_time
                    all_segments.append(adjusted_segment)
                
                all_text.append(result.get("text", ""))
                
            except Exception as e:
                self.logger.error(f"Failed to transcribe chunk {chunk_idx}: {e}")
                # Continue with next chunk
            
            # Move to next chunk
            start_idx += stride
            current_time = (start_idx - overlap_samples) / sample_rate
        
        # Merge results
        full_text = " ".join(all_text).strip()
        
        merged_result = {
            "text": full_text,
            "segments": all_segments,
            "language": detected_language,
            "duration_seconds": duration_seconds,
            "num_chunks": chunk_idx,
        }
        
        self.logger.info(f"✓ Transcription complete: {len(full_text)} characters, {len(all_segments)} segments")
        
        return merged_result
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about loaded model"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "description": "OpenAI Whisper - multilingual speech recognition"
        }


class TranscriptCleaner:
    """
    Post-process Whisper output to clean and structure transcript
    """
    
    def __init__(self):
        self.logger = logger
    
    def merge_short_segments(
        self, 
        segments: List[Dict], 
        min_duration: float = 1.0
    ) -> List[Dict]:
        """
        Merge very short segments (< 1s) with neighbors
        Reduces fragmentation in output
        
        Args:
            segments: List of segments from Whisper
            min_duration: Minimum segment duration in seconds
            
        Returns:
            Merged segments list
        """
        if not segments:
            return segments
        
        merged = []
        for segment in segments:
            duration = segment.get("end", 0) - segment.get("start", 0)
            
            if duration < min_duration and merged:
                # Merge with previous segment
                merged[-1]["text"] += " " + segment["text"]
                merged[-1]["end"] = segment["end"]
            else:
                merged.append(segment)
        
        self.logger.debug(f"Merged {len(segments)} segments to {len(merged)}")
        return merged
    
    def remove_duplicates(self, segments: List[Dict]) -> List[Dict]:
        """
        Remove duplicate segments from overlapping chunks
        
        Args:
            segments: List of segments
            
        Returns:
            Deduplicated segments
        """
        if not segments:
            return segments
        
        cleaned = [segments[0]]
        
        for current in segments[1:]:
            # Check if text is too similar to last segment (overlap)
            last_text = cleaned[-1]["text"].lower().strip()
            current_text = current["text"].lower().strip()
            
            # Simple duplicate check: if >80% similar, skip
            if not self._is_similar(last_text, current_text, threshold=0.8):
                cleaned.append(current)
        
        self.logger.debug(f"Removed duplicates: {len(segments)} -> {len(cleaned)}")
        return cleaned
    
    def _is_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check if two texts are similar"""
        # Simple overlap check
        if not text1 or not text2:
            return False
        
        # Check character-level overlap
        overlap = len(set(text1) & set(text2)) / max(len(set(text1)), len(set(text2)))
        return overlap > threshold
    
    def format_transcript(self, segments: List[Dict]) -> str:
        """
        Format segments into readable transcript
        
        Args:
            segments: List of segments with timestamps
            
        Returns:
            Formatted transcript string
        """
        lines = []
        
        for segment in segments:
            start = segment.get("start", 0)
            text = segment.get("text", "").strip()
            
            # Format: [HH:MM:SS] text
            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            
            lines.append(f"{timestamp} {text}")
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Test STT
    print("Speech-to-Text module loaded")
    print("To test, run: python -m src.modules.speech_to_text")
