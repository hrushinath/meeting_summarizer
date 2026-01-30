"""
Main Pipeline Orchestrator
- Coordinates all modules (audio, STT, preprocessing, summarization)
- Handles errors and retries
- Generates outputs in multiple formats
- Provides progress tracking
"""

from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

from src.modules.audio_processor import AudioProcessor
from src.modules.speech_to_text import SpeechToText, TranscriptCleaner
from src.modules.text_preprocessor import TextPreprocessor
from src.modules.llm_summarizer import MeetingSummarizer
from src.utils import logger, PerformanceTimer, save_json, save_text, get_timestamp_string
from config.settings import OUTPUT_DIR, OUTPUT_FORMATS


class MeetingSummarizerPipeline:
    """
    Complete end-to-end pipeline for meeting summarization
    
    Pipeline Flow:
    1. Audio Input → Load & Validate
    2. Audio Processing → Resample, Chunk
    3. Speech-to-Text → Transcription
    4. Text Preprocessing → Clean, Segment
    5. LLM Summarization → Extract insights
    6. Output Generation → JSON + TXT
    """
    
    def __init__(self):
        """Initialize all pipeline components"""
        self.logger = logger
        
        # Initialize modules
        self.audio_processor = AudioProcessor()
        self.stt = SpeechToText()
        self.transcript_cleaner = TranscriptCleaner()
        self.text_preprocessor = TextPreprocessor()
        self.summarizer = MeetingSummarizer()
        
        # Output directory
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("✓ Pipeline initialized")
    
    def process_meeting(
        self,
        audio_file_path: str,
        meeting_title: str = None,
        save_transcript: bool = True,
    ) -> Dict[str, Any]:
        """
        Process complete meeting from audio to summary
        
        Args:
            audio_file_path: Path to audio file (MP3, WAV, M4A, OGG)
            meeting_title: Optional meeting title (auto-generated if None)
            save_transcript: Whether to save transcript text
            
        Returns:
            Dictionary with:
            - summary: Executive summary
            - key_topics: Extracted topics
            - decisions: Decisions made
            - action_items: Action items with owners
            - transcript: Full transcript
            - metadata: Processing stats
        """
        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"Starting meeting summarization pipeline")
        self.logger.info(f"Audio file: {audio_file_path}")
        self.logger.info(f"{'='*70}\n")
        
        # Generate meeting title if not provided
        if not meeting_title:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            meeting_title = f"Meeting {timestamp}"
        
        metadata = {
            "meeting_title": meeting_title,
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
        
        try:
            # ===== STAGE 1: AUDIO LOADING =====
            with PerformanceTimer("Stage 1: Audio Loading"):
                audio, sample_rate = self.audio_processor.load_audio(audio_file_path)
                audio_info = self.audio_processor.get_audio_info(audio_file_path)
                
            metadata["audio"] = {
                "duration_seconds": audio_info["duration_seconds"],
                "duration_minutes": audio_info["duration_minutes"],
                "file_size_mb": audio_info["file_size_mb"],
                "sample_rate": sample_rate,
            }
            
            # ===== STAGE 2: SPEECH-TO-TEXT =====
            with PerformanceTimer("Stage 2: Speech-to-Text"):
                transcription_result = self.stt.transcribe_long_audio(
                    audio,
                    sample_rate
                )
                raw_transcript = transcription_result.get("text", "")
            
            metadata["transcription"] = {
                "language": transcription_result.get("language"),
                "num_segments": len(transcription_result.get("segments", [])),
                "raw_length": len(raw_transcript),
            }
            
            # ===== STAGE 3: TRANSCRIPT CLEANING =====
            with PerformanceTimer("Stage 3: Transcript Cleaning"):
                # Clean segments
                segments = transcription_result.get("segments", [])
                segments = self.transcript_cleaner.merge_short_segments(segments)
                segments = self.transcript_cleaner.remove_duplicates(segments)
                
                # Format transcript
                formatted_transcript = self.transcript_cleaner.format_transcript(segments)
                
                # Clean text for summarization
                cleaned_text = self.text_preprocessor.clean_text(raw_transcript)
            
            metadata["cleaning"] = {
                "segments_after_merge": len(segments),
                "cleaned_length": len(cleaned_text),
            }
            
            # ===== STAGE 4: TEXT CHUNKING =====
            with PerformanceTimer("Stage 4: Text Chunking"):
                text_chunks = self.text_preprocessor.split_into_chunks(cleaned_text)
            
            metadata["chunking"] = {
                "num_chunks": len(text_chunks),
                "max_chunk_tokens": 1500,
            }
            
            # ===== STAGE 5: SUMMARIZATION =====
            with PerformanceTimer("Stage 5: LLM Summarization"):
                # Use first chunks for summarization (LLMs handle limited context)
                summary_text = " ".join(text_chunks[:3])  # Use first 3 chunks (usually ~5000 chars)
                summary_result = self.summarizer.summarize_transcript(summary_text)
            
            metadata["summary"] = {
                "num_topics": len(summary_result.get("key_topics", [])),
                "num_decisions": len(summary_result.get("decisions", [])),
                "num_action_items": len(summary_result.get("action_items", [])),
            }
            
            # ===== STAGE 6: OUTPUT GENERATION =====
            with PerformanceTimer("Stage 6: Output Generation"):
                output_files = self._save_outputs(
                    meeting_title,
                    formatted_transcript,
                    summary_result,
                    metadata,
                    save_transcript
                )
            
            metadata["output_files"] = output_files
            
            # ===== COMPLETION =====
            self.logger.info(f"\n{'='*70}")
            self.logger.info(f"✓ PIPELINE COMPLETE")
            self.logger.info(f"Outputs saved to: {self.output_dir}")
            self.logger.info(f"Files: {len(output_files)} generated")
            self.logger.info(f"{'='*70}\n")
            
            # Prepare final result
            result = {
                "meeting_title": meeting_title,
                "transcript": formatted_transcript if save_transcript else "[Not saved]",
                "summary": summary_result["summary"],
                "key_topics": summary_result["key_topics"],
                "decisions": summary_result["decisions"],
                "action_items": summary_result["action_items"],
                "metadata": metadata,
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
    
    def _save_outputs(
        self,
        meeting_title: str,
        transcript: str,
        summary: Dict,
        metadata: Dict,
        save_transcript: bool
    ) -> Dict[str, str]:
        """
        Save outputs in multiple formats
        
        Args:
            meeting_title: Title for the meeting
            transcript: Formatted transcript text
            summary: Summary dictionary
            metadata: Processing metadata
            save_transcript: Whether to save transcript
            
        Returns:
            Dictionary of saved file paths
        """
        timestamp = get_timestamp_string()
        output_files = {}
        
        # ===== SAVE STRUCTURED SUMMARY (JSON) =====
        json_output = {
            "meeting_title": meeting_title,
            "duration": metadata.get("audio", {}).get("duration_minutes", 0),
            "timestamp": metadata.get("timestamp"),
            "summary": summary.get("summary", ""),
            "key_topics": summary.get("key_topics", []),
            "decisions": summary.get("decisions", []),
            "action_items": summary.get("action_items", []),
            "metadata": {
                "language": metadata.get("transcription", {}).get("language"),
                "num_segments": metadata.get("transcription", {}).get("num_segments"),
                "processing_stages": metadata.get("stages"),
            }
        }
        
        json_file = self.output_dir / f"summary_{timestamp}.json"
        if save_json(json_output, str(json_file)):
            output_files["summary_json"] = str(json_file)
        
        # ===== SAVE READABLE TEXT SUMMARY =====
        text_summary = self._format_text_summary(meeting_title, json_output)
        txt_file = self.output_dir / f"summary_{timestamp}.txt"
        if save_text(text_summary, str(txt_file)):
            output_files["summary_txt"] = str(txt_file)
        
        # ===== SAVE TRANSCRIPT (OPTIONAL) =====
        if save_transcript and transcript:
            transcript_file = self.output_dir / f"transcript_{timestamp}.txt"
            if save_text(transcript, str(transcript_file)):
                output_files["transcript"] = str(transcript_file)
        
        return output_files
    
    def _format_text_summary(self, meeting_title: str, data: Dict) -> str:
        """
        Format summary as readable text
        
        Args:
            meeting_title: Meeting title
            data: Summary data dictionary
            
        Returns:
            Formatted text summary
        """
        lines = [
            "=" * 80,
            f"MEETING SUMMARY: {meeting_title}",
            "=" * 80,
            "",
            f"Date/Time: {data.get('timestamp', 'N/A')}",
            f"Duration: {data.get('duration', 'N/A')} minutes",
            "",
            "-" * 80,
            "EXECUTIVE SUMMARY",
            "-" * 80,
            data.get("summary", "No summary available"),
            "",
            "-" * 80,
            "KEY TOPICS",
            "-" * 80,
        ]
        
        for i, topic in enumerate(data.get("key_topics", []), 1):
            lines.append(f"{i}. {topic}")
        
        lines.extend([
            "",
            "-" * 80,
            "DECISIONS",
            "-" * 80,
        ])
        
        for i, decision in enumerate(data.get("decisions", []), 1):
            lines.append(f"{i}. {decision}")
        
        lines.extend([
            "",
            "-" * 80,
            "ACTION ITEMS",
            "-" * 80,
        ])
        
        action_items = data.get("action_items", [])
        if action_items:
            for i, item in enumerate(action_items, 1):
                lines.append(f"{i}. {item.get('task', 'N/A')}")
                lines.append(f"   Owner: {item.get('owner', 'TBD')}")
                lines.append(f"   Deadline: {item.get('deadline', 'TBD')}")
                lines.append("")
        else:
            lines.append("No action items identified.")
        
        lines.extend([
            "=" * 80,
            "Generated by: LLM-Based Meeting Summarizer",
            "=" * 80,
        ])
        
        return "\n".join(lines)


def main():
    """Test the pipeline"""
    from config.settings import AUDIO_INPUT_DIR
    
    # Find test audio file
    audio_files = (
        list(AUDIO_INPUT_DIR.glob("*.wav")) +
        list(AUDIO_INPUT_DIR.glob("*.mp3")) +
        list(AUDIO_INPUT_DIR.glob("*.m4a"))
    )
    
    if not audio_files:
        print(f"No audio files found in {AUDIO_INPUT_DIR}")
        print("Please place an audio file (MP3, WAV, M4A) in the audio_input folder")
        return
    
    # Process first audio file
    pipeline = MeetingSummarizerPipeline()
    result = pipeline.process_meeting(
        str(audio_files[0]),
        meeting_title="Test Meeting"
    )
    
    print("\nResult Summary:")
    print(f"Title: {result['meeting_title']}")
    print(f"Topics: {len(result['key_topics'])} identified")
    print(f"Decisions: {len(result['decisions'])} made")
    print(f"Action Items: {len(result['action_items'])} created")


if __name__ == "__main__":
    main()
