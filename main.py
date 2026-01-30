"""
Command-Line Interface for Meeting Summarizer
Provides easy access to the complete pipeline
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.pipeline import MeetingSummarizerPipeline
from src.utils import logger, validate_audio_file
from config.settings import AUDIO_INPUT_DIR, OUTPUT_DIR


class MeetingSummarizerCLI:
    """Command-line interface for meeting summarization"""
    
    def __init__(self):
        self.logger = logger
        self.pipeline = None
    
    def run(self, args):
        """Execute based on command-line arguments"""
        
        if args.command == "summarize":
            return self.summarize(
                args.audio_file,
                args.title,
                args.save_transcript
            )
        
        elif args.command == "info":
            return self.show_info()
        
        elif args.command == "status":
            return self.show_status()
        
        else:
            print("Unknown command")
            return 1
    
    def summarize(
        self,
        audio_file: str,
        title: Optional[str] = None,
        save_transcript: bool = True
    ) -> int:
        """
        Summarize a meeting from audio file
        
        Args:
            audio_file: Path to audio file
            title: Optional meeting title
            save_transcript: Whether to save transcript
            
        Returns:
            Exit code (0 = success)
        """
        try:
            # Validate audio file
            is_valid, error_msg = validate_audio_file(audio_file)
            if not is_valid:
                self.logger.error(error_msg)
                return 1
            
            # Initialize pipeline
            if self.pipeline is None:
                self.pipeline = MeetingSummarizerPipeline()
            
            # Process meeting
            result = self.pipeline.process_meeting(
                audio_file,
                meeting_title=title,
                save_transcript=save_transcript
            )
            
            # Print results
            self.print_result(result)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to summarize meeting: {e}")
            return 1
    
    def show_info(self) -> int:
        """Show system information"""
        print("\n" + "="*80)
        print("MEETING SUMMARIZER - SYSTEM INFORMATION")
        print("="*80)
        
        print("\nProject Paths:")
        print(f"  Audio Input:  {AUDIO_INPUT_DIR}")
        print(f"  Outputs:      {OUTPUT_DIR}")
        
        print("\nSupported Audio Formats:")
        print("  - WAV (.wav)")
        print("  - MP3 (.mp3)")
        print("  - M4A (.m4a)")
        print("  - OGG (.ogg)")
        print("  - FLAC (.flac)")
        
        print("\nComponents:")
        print("  - Speech-to-Text: OpenAI Whisper")
        print("  - LLM Backend: Ollama or HuggingFace Transformers")
        print("  - Text Processing: NLTK")
        
        print("\n" + "="*80 + "\n")
        return 0
    
    def show_status(self) -> int:
        """Show system status and dependencies"""
        print("\n" + "="*80)
        print("MEETING SUMMARIZER - STATUS CHECK")
        print("="*80)
        
        checks = {
            "Python Dependencies": self._check_dependencies(),
            "Audio Input Directory": self._check_input_dir(),
            "Output Directory": self._check_output_dir(),
            "Whisper Model": self._check_whisper(),
            "LLM Backend": self._check_llm_backend(),
        }
        
        for check_name, status in checks.items():
            icon = "✓" if status else "✗"
            print(f"{icon} {check_name}")
        
        print("\n" + "="*80 + "\n")
        
        # Return 0 if all checks passed
        return 0 if all(checks.values()) else 1
    
    def _check_dependencies(self) -> bool:
        """Check if required packages are installed"""
        required = ["librosa", "torch", "transformers", "nltk"]
        
        for package in required:
            try:
                __import__(package)
            except ImportError:
                self.logger.warning(f"Missing: {package}")
                return False
        
        return True
    
    def _check_input_dir(self) -> bool:
        """Check if audio input directory exists"""
        exists = AUDIO_INPUT_DIR.exists()
        if not exists:
            AUDIO_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        return True
    
    def _check_output_dir(self) -> bool:
        """Check if output directory exists"""
        exists = OUTPUT_DIR.exists()
        if not exists:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return True
    
    def _check_whisper(self) -> bool:
        """Check if Whisper is available"""
        try:
            import whisper
            return True
        except ImportError:
            self.logger.warning("Whisper not installed")
            return False
    
    def _check_llm_backend(self) -> bool:
        """Check if LLM backend is available"""
        try:
            import ollama
            return True
        except ImportError:
            try:
                import transformers
                return True
            except ImportError:
                self.logger.warning("No LLM backend available")
                return False
    
    def print_result(self, result: dict):
        """Print summarization results"""
        print("\n" + "="*80)
        print("SUMMARIZATION RESULTS")
        print("="*80)
        
        print(f"\nMeeting: {result['meeting_title']}")
        
        print("\n" + "-"*80)
        print("SUMMARY")
        print("-"*80)
        print(result['summary'][:500] + "..." if len(result['summary']) > 500 else result['summary'])
        
        print("\n" + "-"*80)
        print("KEY TOPICS")
        print("-"*80)
        for topic in result['key_topics'][:5]:
            print(f"  • {topic}")
        
        print("\n" + "-"*80)
        print("DECISIONS")
        print("-"*80)
        for decision in result['decisions'][:5]:
            print(f"  • {decision}")
        
        print("\n" + "-"*80)
        print("ACTION ITEMS")
        print("-"*80)
        for item in result['action_items'][:5]:
            print(f"  • {item['task']}")
            print(f"    Owner: {item['owner']} | Deadline: {item['deadline']}")
        
        print("\n" + "="*80)
        print("See output files for complete results")
        print("="*80 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LLM-Based Meeting Summarization System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py summarize meeting.wav
  python main.py summarize meeting.mp3 --title "Team Standup"
  python main.py summarize meeting.m4a --save-transcript
  python main.py info
  python main.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Summarize command
    summarize_parser = subparsers.add_parser(
        "summarize",
        help="Summarize a meeting from audio file"
    )
    summarize_parser.add_argument(
        "audio_file",
        help="Path to audio file (MP3, WAV, M4A, OGG, FLAC)"
    )
    summarize_parser.add_argument(
        "--title",
        help="Optional meeting title"
    )
    summarize_parser.add_argument(
        "--save-transcript",
        action="store_true",
        default=True,
        help="Save transcript to file (default: True)"
    )
    
    # Info command
    subparsers.add_parser("info", help="Show system information")
    
    # Status command
    subparsers.add_parser("status", help="Check system status and dependencies")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    cli = MeetingSummarizerCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
