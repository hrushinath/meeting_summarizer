"""
Text Preprocessing Module
- Clean and normalize transcript text
- Split into chunks for LLM processing
- Remove filler words and noise
- Prepare text for summarization
"""

import re
import nltk
from typing import List, Dict, Tuple
from pathlib import Path

from src.utils import logger
from config.settings import FILLER_WORDS, MAX_TOKENS_PER_CHUNK


class TextPreprocessor:
    """
    Clean and preprocess transcript text
    """
    
    def __init__(self):
        self.logger = logger
        self.filler_words = FILLER_WORDS
        self.max_tokens = MAX_TOKENS_PER_CHUNK
        
        # Download required NLTK data
        self._ensure_nltk_data()
    
    def _ensure_nltk_data(self):
        """Download required NLTK data for tokenization"""
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            self.logger.info("Downloading NLTK punkt_tab tokenizer...")
            nltk.download('punkt_tab', quiet=True)
        
        # Also try the older punkt format as fallback
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            self.logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt', quiet=True)
    
    def clean_text(self, text: str) -> str:
        """
        Clean transcript text:
        - Remove extra whitespace
        - Fix common Whisper transcription errors
        - Normalize punctuation
        - Remove filler words (optional)
        
        Args:
            text: Raw transcript text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Fix common Whisper errors
        text = self._fix_common_errors(text)
        
        # Remove filler words (can be disabled by setting FILLER_WORDS = set())
        if self.filler_words:
            text = self._remove_filler_words(text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*([A-Z])', r'\1 \2', text)
        
        self.logger.debug(f"Cleaned text: {len(text)} characters")
        return text
    
    def _fix_common_errors(self, text: str) -> str:
        """
        Fix common transcription errors from Whisper
        
        Args:
            text: Text with errors
            
        Returns:
            Corrected text
        """
        # Fix [music] and similar tags
        text = re.sub(r'\[.*?\]', '', text)
        
        # Fix repeated words
        words = text.split()
        cleaned_words = []
        for i, word in enumerate(words):
            if i == 0 or word != words[i-1]:
                cleaned_words.append(word)
        text = ' '.join(cleaned_words)
        
        return text
    
    def _remove_filler_words(self, text: str) -> str:
        """
        Remove common filler words (um, uh, like, you know, etc.)
        
        Args:
            text: Original text
            
        Returns:
            Text with filler words removed
        """
        words = text.lower().split()
        cleaned = [w for w in words if w not in self.filler_words]
        
        # Preserve original casing
        result_words = []
        original_words = text.split()
        cleaned_idx = 0
        
        for original in original_words:
            if original.lower() not in self.filler_words:
                # Use original casing
                if cleaned_idx < len(cleaned):
                    result_words.append(original)
                    cleaned_idx += 1
        
        text = ' '.join(result_words)
        return text
    
    def split_into_chunks(self, text: str, max_tokens: int = None) -> List[str]:
        """
        Split text into chunks for LLM processing
        
        Why chunking?
        - LLMs have context length limits (e.g., 2048 tokens)
        - Prevents memory overflow
        - Allows parallel processing
        
        Strategy:
        - Split by sentences first
        - Combine sentences until hitting token limit
        - Preserve sentence boundaries for context
        
        Args:
            text: Full text to split
            max_tokens: Maximum tokens per chunk (default: MAX_TOKENS_PER_CHUNK)
            
        Returns:
            List of text chunks
        """
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        if not text:
            return []
        
        # Split into sentences
        sentences = nltk.sent_tokenize(text)
        self.logger.debug(f"Split into {len(sentences)} sentences")
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            # Rough token count (1 token ≈ 4 characters)
            sentence_tokens = len(sentence) // 4
            
            # If single sentence exceeds limit, add it alone
            if sentence_tokens > max_tokens:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                chunks.append(sentence)
                continue
            
            # Add sentence to current chunk if it fits
            if current_tokens + sentence_tokens <= max_tokens:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        self.logger.info(f"Created {len(chunks)} text chunks (max {max_tokens} tokens each)")
        return chunks
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """
        Extract important phrases/keywords from text
        Used for topic identification
        
        Args:
            text: Text to analyze
            
        Returns:
            List of key phrases
        """
        # Simple extraction: longer words and proper nouns
        words = text.split()
        
        # Filter: words > 5 chars, not common words
        common = {'about', 'there', 'their', 'would', 'could', 'should', 'think', 'really'}
        key_phrases = [
            w for w in words 
            if len(w) > 5 and w.lower() not in common
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for phrase in key_phrases:
            if phrase.lower() not in seen:
                unique.append(phrase)
                seen.add(phrase.lower())
        
        return unique[:20]  # Return top 20


class TokenCounter:
    """
    Estimate token count for text
    Different models have different tokenizers, so we use approximations
    """
    
    @staticmethod
    def count_tokens_approximate(text: str) -> int:
        """
        Approximate token count using character ratio
        
        Rules:
        - 1 token ≈ 4 characters for English
        - More accurate for context length planning
        
        Args:
            text: Text to count
            
        Returns:
            Approximate token count
        """
        # Simple heuristic
        return len(text) // 4
    
    @staticmethod
    def count_tokens_nltk(text: str) -> int:
        """
        More accurate token count using NLTK
        
        Args:
            text: Text to count
            
        Returns:
            Token count
        """
        from nltk.tokenize import word_tokenize
        tokens = word_tokenize(text)
        return len(tokens)


if __name__ == "__main__":
    # Test preprocessing
    preprocessor = TextPreprocessor()
    
    test_text = """
    Um, you know, like we had a really, really great meeting today.
    [laughter] So basically, the main points were, um, that we need to, like,
    focus on the product development. I mean, honestly, we should really, you know,
    accelerate the timeline. Actually, the team agreed that we should launch next quarter.
    """
    
    cleaned = preprocessor.clean_text(test_text)
    print(f"Cleaned text:\n{cleaned}\n")
    
    chunks = preprocessor.split_into_chunks(cleaned, max_tokens=100)
    print(f"Chunks ({len(chunks)}):")
    for i, chunk in enumerate(chunks, 1):
        print(f"  [{i}] {chunk[:100]}...")
    
    phrases = preprocessor.extract_key_phrases(cleaned)
    print(f"\nKey phrases: {phrases}")
