"""
Audio Processing Module
- Load and validate audio files
- Handle format conversion (MP3 -> WAV)
- Chunk long audio for Whisper processing
- Ensure correct sample rate (16kHz for Whisper)
"""

import librosa
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict
import soundfile as sf

from src.utils import logger, PerformanceTimer, validate_audio_file
from config.settings import SAMPLE_RATE, WHISPER_CHUNK_DURATION, AUDIO_INPUT_DIR


class AudioProcessor:
    """
    Handles audio loading, validation, and chunking
    """
    
    def __init__(self):
        """Initialize audio processor"""
        self.logger = logger
        self.sample_rate = SAMPLE_RATE
        self.chunk_duration = WHISPER_CHUNK_DURATION
    
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file and resample to 16kHz (Whisper requirement)
        
        Args:
            file_path: Path to audio file (MP3, WAV, M4A, OGG)
            
        Returns:
            Tuple of (audio_array, sample_rate)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format not supported
        """
        # Validate file
        is_valid, error_msg = validate_audio_file(file_path)
        if not is_valid:
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.info(f"Loading audio from: {file_path}")
        
        with PerformanceTimer("Audio loading"):
            try:
                # Load audio with librosa (handles MP3, WAV, M4A, OGG, etc.)
                # sr=None preserves original sample rate initially
                audio, sr = librosa.load(file_path, sr=None, mono=True)
                
                # Resample to 16kHz if necessary (Whisper requirement)
                if sr != self.sample_rate:
                    self.logger.info(f"Resampling from {sr}Hz to {self.sample_rate}Hz")
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
                
                # Validate audio
                if len(audio) == 0:
                    raise ValueError("Audio file is empty")
                
                duration_seconds = len(audio) / self.sample_rate
                self.logger.info(f"✓ Audio loaded: {duration_seconds:.1f}s duration")
                
                return audio, self.sample_rate
                
            except Exception as e:
                self.logger.error(f"Failed to load audio: {e}")
                raise
    
    def get_audio_info(self, file_path: str) -> Dict[str, float]:
        """
        Get audio file information without loading entire file
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio info (duration, channels, etc.)
        """
        try:
            # Get audio duration
            duration = librosa.get_duration(filename=file_path)
            
            info = {
                "duration_seconds": duration,
                "duration_minutes": duration / 60,
                "file_size_mb": Path(file_path).stat().st_size / (1024**2),
            }
            
            self.logger.debug(f"Audio info: {info}")
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get audio info: {e}")
            raise
    
    def chunk_audio(self, audio: np.ndarray, chunk_duration: int = None) -> List[np.ndarray]:
        """
        Split long audio into chunks for Whisper processing
        
        This prevents memory overflow when processing long meetings
        Whisper handles 15-30 minute chunks well
        
        Args:
            audio: Audio array
            chunk_duration: Duration of each chunk in seconds (default: WHISPER_CHUNK_DURATION)
            
        Returns:
            List of audio chunks (numpy arrays)
        """
        if chunk_duration is None:
            chunk_duration = self.chunk_duration
        
        total_duration = len(audio) / self.sample_rate
        
        # If audio is shorter than chunk duration, return as single chunk
        if total_duration <= chunk_duration:
            self.logger.debug(f"Audio duration ({total_duration:.1f}s) < chunk duration ({chunk_duration}s)")
            return [audio]
        
        # Calculate number of chunks with 30s overlap for context
        overlap_seconds = 30
        chunk_samples = chunk_duration * self.sample_rate
        overlap_samples = overlap_seconds * self.sample_rate
        stride = chunk_samples - overlap_samples
        
        chunks = []
        start_idx = 0
        
        while start_idx < len(audio):
            end_idx = min(start_idx + chunk_samples, len(audio))
            chunk = audio[start_idx:end_idx]
            chunks.append(chunk)
            
            # Move start pointer by stride (accounts for overlap)
            start_idx += stride
        
        self.logger.info(f"Split audio into {len(chunks)} chunks (duration: {chunk_duration}s each, 30s overlap)")
        return chunks
    
    def normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio to [-1, 1] range
        
        Args:
            audio: Audio array
            
        Returns:
            Normalized audio array
        """
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        return audio
    
    def detect_silence(self, audio: np.ndarray, threshold_db: float = -40) -> Tuple[int, int]:
        """
        Detect silence regions in audio (optional feature)
        
        Args:
            audio: Audio array
            threshold_db: Silence threshold in dB
            
        Returns:
            Tuple of (silence_start_sample, silence_end_sample)
        """
        # Convert to dB
        S = librosa.feature.melspectrogram(y=audio, sr=self.sample_rate)
        S_db = librosa.power_to_db(S, ref=np.max)
        
        # Find silent frames
        silence_mask = np.mean(S_db, axis=0) < threshold_db
        
        # Find continuous silence regions
        changes = np.diff(silence_mask.astype(int))
        silence_starts = np.where(changes == 1)[0]
        silence_ends = np.where(changes == -1)[0]
        
        return silence_starts, silence_ends
    
    def export_audio(self, audio: np.ndarray, output_path: str):
        """
        Export audio to file (for debugging/testing)
        
        Args:
            audio: Audio array
            output_path: Output file path
        """
        try:
            sf.write(output_path, audio, self.sample_rate)
            self.logger.info(f"Exported audio to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to export audio: {e}")


if __name__ == "__main__":
    # Test audio processor
    processor = AudioProcessor()
    
    # Example: Load and chunk audio
    test_audio_dir = AUDIO_INPUT_DIR
    test_files = list(test_audio_dir.glob("*.wav")) + list(test_audio_dir.glob("*.mp3"))
    
    if test_files:
        print(f"\nFound {len(test_files)} audio files to test")
        audio, sr = processor.load_audio(str(test_files[0]))
        info = processor.get_audio_info(str(test_files[0]))
        print(f"Audio info: {info}")
        chunks = processor.chunk_audio(audio)
        print(f"Created {len(chunks)} chunks")
    else:
        print("No audio files found in audio_input directory")
