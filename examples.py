"""
Example usage of the Meeting Summarizer system
Run this file to test the system with sample code
"""

from src.pipeline import MeetingSummarizerPipeline
from src.modules.audio_processor import AudioProcessor
from src.modules.speech_to_text import SpeechToText
from src.modules.text_preprocessor import TextPreprocessor
from src.modules.llm_summarizer import MeetingSummarizer
from config.settings import AUDIO_INPUT_DIR, OUTPUT_DIR
import json


def example_1_full_pipeline():
    """Example 1: Complete pipeline (easiest)"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Full Pipeline (Recommended)")
    print("="*80)
    
    # Initialize pipeline
    pipeline = MeetingSummarizerPipeline()
    
    # Process a meeting
    try:
        result = pipeline.process_meeting(
            "audio_input/meeting.mp3",  # Replace with your file
            meeting_title="Team Standup"
        )
        
        # Access results
        print("\n[RESULTS]")
        print(f"Title: {result['meeting_title']}")
        print(f"\nSummary:\n{result['summary'][:200]}...")
        print(f"\nTopics: {', '.join(result['key_topics'][:3])}")
        print(f"Decisions: {len(result['decisions'])} made")
        print(f"Action Items: {len(result['action_items'])}")
        
    except FileNotFoundError:
        print("No audio file found. Place an audio file in audio_input/ folder")


def example_2_step_by_step():
    """Example 2: Step-by-step module usage"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Step-by-Step Module Usage")
    print("="*80)
    
    try:
        # Step 1: Load audio
        print("\n[1] Loading audio...")
        processor = AudioProcessor()
        audio, sample_rate = processor.load_audio("audio_input/meeting.mp3")
        print(f"    Loaded: {len(audio) / sample_rate:.1f} seconds")
        
        # Step 2: Transcribe
        print("[2] Transcribing with Whisper...")
        stt = SpeechToText()
        result = stt.transcribe_long_audio(audio, sample_rate)
        transcript = result["text"]
        print(f"    Transcript length: {len(transcript)} characters")
        
        # Step 3: Clean text
        print("[3] Cleaning text...")
        preprocessor = TextPreprocessor()
        cleaned = preprocessor.clean_text(transcript)
        print(f"    Cleaned: {len(cleaned)} characters")
        
        # Step 4: Split into chunks
        print("[4] Chunking text...")
        chunks = preprocessor.split_into_chunks(cleaned)
        print(f"    Created {len(chunks)} chunks")
        
        # Step 5: Summarize
        print("[5] Summarizing with LLM...")
        summarizer = MeetingSummarizer()
        summary = summarizer.summarize_transcript(cleaned)
        print(f"    Summary: {len(summary['summary'])} characters")
        print(f"    Topics: {len(summary['key_topics'])}")
        print(f"    Decisions: {len(summary['decisions'])}")
        print(f"    Action Items: {len(summary['action_items'])}")
        
    except FileNotFoundError:
        print("No audio file found. Place an audio file in audio_input/ folder")


def example_3_custom_workflow():
    """Example 3: Custom workflow"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Custom Workflow")
    print("="*80)
    
    try:
        # Load audio
        processor = AudioProcessor()
        audio, sr = processor.load_audio("audio_input/meeting.mp3")
        
        # Check audio info
        info = processor.get_audio_info("audio_input/meeting.mp3")
        print(f"\n[AUDIO INFO]")
        print(f"Duration: {info['duration_minutes']:.1f} minutes")
        print(f"File size: {info['file_size_mb']:.1f} MB")
        
        # Transcribe only
        stt = SpeechToText()
        result = stt.transcribe_long_audio(audio, sr)
        
        print(f"\n[TRANSCRIPTION]")
        print(f"Language: {result.get('language')}")
        print(f"Segments: {len(result.get('segments', []))}")
        print(f"First 200 chars:\n{result['text'][:200]}")
        
    except FileNotFoundError:
        print("No audio file found. Place an audio file in audio_input/ folder")


def example_4_batch_processing():
    """Example 4: Batch processing multiple files"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Batch Processing")
    print("="*80)
    
    from pathlib import Path
    
    pipeline = MeetingSummarizerPipeline()
    
    # Find all audio files
    audio_files = (
        list(AUDIO_INPUT_DIR.glob("*.mp3")) +
        list(AUDIO_INPUT_DIR.glob("*.wav")) +
        list(AUDIO_INPUT_DIR.glob("*.m4a"))
    )
    
    if not audio_files:
        print("No audio files found in audio_input/")
        return
    
    print(f"Found {len(audio_files)} audio files")
    
    for idx, audio_file in enumerate(audio_files, 1):
        print(f"\n[{idx}/{len(audio_files)}] Processing {audio_file.name}...")
        try:
            result = pipeline.process_meeting(
                str(audio_file),
                meeting_title=audio_file.stem
            )
            print(f"    ✓ Summary generated: {len(result['summary'])} chars")
        except Exception as e:
            print(f"    ✗ Failed: {e}")


def example_5_programmatic_api():
    """Example 5: Using as a library in your code"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Using as a Library")
    print("="*80)
    
    # This is how you'd use it in your own application
    code_example = '''
from src.pipeline import MeetingSummarizerPipeline

# Your application code
def summarize_team_meeting(audio_file_path):
    """Summarize a team meeting"""
    
    pipeline = MeetingSummarizerPipeline()
    
    try:
        result = pipeline.process_meeting(
            audio_file_path,
            meeting_title="Team Sync"
        )
        
        # Use the results
        return {
            'summary': result['summary'],
            'action_items': result['action_items'],
            'topics': result['key_topics']
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return None

# Call it
meeting_summary = summarize_team_meeting("meeting.mp3")
print(meeting_summary)
    '''
    
    print("\nExample code:")
    print(code_example)


def example_6_rest_api():
    """Example 6: Using REST API"""
    print("\n" + "="*80)
    print("EXAMPLE 6: REST API Usage")
    print("="*80)
    
    curl_example = '''
# Start the server (in a terminal):
python server.py

# Then call the API from another terminal or script:

# Using curl:
curl -X POST "http://localhost:8000/summarize" \\
  -F "file=@meeting.mp3" \\
  -F "title=Team Meeting"

# Using Python:
import requests

files = {'file': open('meeting.mp3', 'rb')}
data = {'title': 'Team Meeting'}

response = requests.post(
    'http://localhost:8000/summarize',
    files=files,
    data=data
)

result = response.json()
print(result['summary'])
print(result['action_items'])

# Using JavaScript (Fetch API):
const formData = new FormData();
formData.append('file', audioFile);
formData.append('title', 'Team Meeting');

fetch('http://localhost:8000/summarize', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data))
    '''
    
    print("\nAPI examples (curl, Python, JavaScript):")
    print(curl_example)


def example_7_configuration():
    """Example 7: Configuration options"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Configuration Customization")
    print("="*80)
    
    config_example = '''
# Edit config/settings.py to customize:

# Use faster but less accurate Whisper
WHISPER_MODEL = WhisperModel.TINY.value

# Use GPU acceleration
WHISPER_CONFIG["device"] = "cuda"

# Use different LLM
LLM_MODEL = LLMModel.LLAMA2_7B.value

# Adjust chunk size (smaller = more memory efficient)
WHISPER_CHUNK_DURATION = 600  # 10 minutes

# Maximum tokens per LLM chunk
MAX_TOKENS_PER_CHUNK = 2000

# Custom filler words
FILLER_WORDS = {"um", "uh", "like", "basically"}

# Enable memory optimization for laptops
ENABLE_MEMORY_OPTIMIZATION = True
    '''
    
    print("\nConfiguration examples:")
    print(config_example)


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("MEETING SUMMARIZER - USAGE EXAMPLES")
    print("="*80)
    
    examples = [
        ("1", "Full Pipeline (Easiest)", example_1_full_pipeline),
        ("2", "Step-by-Step Modules", example_2_step_by_step),
        ("3", "Custom Workflow", example_3_custom_workflow),
        ("4", "Batch Processing", example_4_batch_processing),
        ("5", "Library Usage", example_5_programmatic_api),
        ("6", "REST API", example_6_rest_api),
        ("7", "Configuration", example_7_configuration),
    ]
    
    print("\nAvailable examples:")
    for num, title, _ in examples:
        print(f"  {num}. {title}")
    
    print("\nRun from Python:")
    print("  from examples import example_1_full_pipeline")
    print("  example_1_full_pipeline()")
    
    print("\nRun from command line:")
    print("  python examples.py")
    
    # Run first example
    print("\n\nRunning Example 1...")
    example_1_full_pipeline()


if __name__ == "__main__":
    main()
