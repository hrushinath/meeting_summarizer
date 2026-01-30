"""
Meeting Summarizer Package
LLM-based automatic meeting summarization system
"""

__version__ = "1.0.0"
__author__ = "AI Engineer"
__description__ = "Convert meeting audio to structured summaries using local LLMs"

from src.pipeline import MeetingSummarizerPipeline
from src.modules.audio_processor import AudioProcessor
from src.modules.speech_to_text import SpeechToText, TranscriptCleaner
from src.modules.text_preprocessor import TextPreprocessor
from src.modules.llm_summarizer import MeetingSummarizer

__all__ = [
    "MeetingSummarizerPipeline",
    "AudioProcessor",
    "SpeechToText",
    "TranscriptCleaner",
    "TextPreprocessor",
    "MeetingSummarizer",
]

print(f"Meeting Summarizer v{__version__} loaded")
