"""
LLM Summarization Module
- Interface with local LLM (Ollama or HuggingFace Transformers)
- Generate structured summaries
- Extract action items, decisions, key topics
- Support multiple summary styles
"""

from typing import Dict, List, Optional, Any
import json
import re

from src.utils import logger, PerformanceTimer
from config.settings import LLM_BACKEND, OLLAMA_CONFIG, HF_CONFIG


class LLMInterface:
    """
    Abstract interface for LLM backends
    Supports Ollama and HuggingFace Transformers
    """
    
    def __init__(self, backend: str = LLM_BACKEND):
        """
        Initialize LLM interface
        
        Args:
            backend: 'ollama' or 'transformers'
        """
        self.backend = backend
        self.logger = logger
        self.model = None
        
        if backend == "ollama":
            self._init_ollama()
        elif backend == "transformers":
            self._init_transformers()
        else:
            raise ValueError(f"Unknown backend: {backend}")
    
    def _init_ollama(self):
        """
        Initialize Ollama backend
        
        Ollama advantages:
        - Easy setup (single install)
        - Pre-optimized models
        - Runs locally without code
        - Supports multiple models via `ollama pull`
        """
        self.logger.info("Initializing Ollama backend...")
        
        try:
            import ollama
            self.client = ollama.Client()
            
            # Test connection
            try:
                # Try to get model info
                self.client.list()
                self.logger.info(f"✓ Ollama connected")
            except Exception as e:
                self.logger.error(f"Ollama not running. Start with: ollama serve")
                raise
            
        except ImportError:
            self.logger.error("Ollama not installed. Install with: pip install ollama")
            raise
    
    def _init_transformers(self):
        """
        Initialize HuggingFace Transformers backend
        
        Transformers advantages:
        - More control over model
        - Custom training possible
        - Works without Ollama
        
        Note: Requires more setup and dependencies
        """
        self.logger.info("Initializing HuggingFace Transformers backend...")
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            model_id = HF_CONFIG["model_id"]
            device = HF_CONFIG["device"]
            
            self.logger.info(f"Loading model: {model_id}")
            
            with PerformanceTimer("Model loading"):
                self.tokenizer = AutoTokenizer.from_pretrained(model_id)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    device_map=device,
                    offload_folder="/tmp",  # Offload to disk if needed
                )
            
            self.logger.info(f"✓ Model loaded on {device}")
            
        except ImportError as e:
            self.logger.error(f"Transformers not installed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise
    
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """
        Generate response from LLM
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum output length
            
        Returns:
            Generated text
        """
        if self.backend == "ollama":
            return self._generate_ollama(prompt, max_tokens)
        else:
            return self._generate_transformers(prompt, max_tokens)
    
    def _generate_ollama(self, prompt: str, max_tokens: int) -> str:
        """Generate using Ollama"""
        try:
            self.logger.debug(f"Generating with Ollama ({OLLAMA_CONFIG['model']})...")
            
            with PerformanceTimer("LLM generation"):
                response = self.client.generate(
                    model=OLLAMA_CONFIG["model"],
                    prompt=prompt,
                    stream=False,
                    options={
                        "temperature": OLLAMA_CONFIG["temperature"],
                        "top_p": OLLAMA_CONFIG["top_p"],
                        "num_predict": max_tokens,
                    }
                )
            
            return response["response"].strip()
            
        except Exception as e:
            self.logger.error(f"Ollama generation failed: {e}")
            raise
    
    def _generate_transformers(self, prompt: str, max_tokens: int) -> str:
        """Generate using HuggingFace Transformers"""
        try:
            import torch
            
            self.logger.debug("Generating with Transformers...")
            
            with torch.no_grad():
                inputs = self.tokenizer(prompt, return_tensors="pt")
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                
                with PerformanceTimer("LLM generation"):
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=max_tokens,
                        temperature=HF_CONFIG["temperature"],
                        top_p=HF_CONFIG["top_p"],
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id,
                    )
            
            # Decode output (remove prompt from output)
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove input prompt from output
            if prompt in generated_text:
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Transformers generation failed: {e}")
            raise


class MeetingSummarizer:
    """
    Generate summaries from meeting transcripts
    """
    
    def __init__(self, llm_backend: str = LLM_BACKEND):
        """
        Initialize summarizer with LLM
        
        Args:
            llm_backend: 'ollama' or 'transformers'
        """
        self.logger = logger
        self.llm = LLMInterface(backend=llm_backend)
    
    def summarize_transcript(
        self, 
        transcript: str,
        summary_style: str = "structured"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive meeting summary
        
        Args:
            transcript: Full meeting transcript
            summary_style: 'structured' (JSON), 'bullets', or 'paragraph'
            
        Returns:
            Dictionary with summary components
        """
        if not transcript or len(transcript.strip()) < 50:
            self.logger.warning("Transcript too short for summarization")
            return {
                "summary": "Transcript too short to summarize",
                "key_topics": [],
                "decisions": [],
                "action_items": [],
            }
        
        self.logger.info("Generating meeting summary...")
        
        with PerformanceTimer("Summary generation"):
            # Generate executive summary
            summary = self._generate_summary(transcript)
            
            # Extract key topics
            topics = self._extract_topics(transcript)
            
            # Extract decisions
            decisions = self._extract_decisions(transcript)
            
            # Extract action items
            action_items = self._extract_action_items(transcript)
        
        result = {
            "summary": summary,
            "key_topics": topics,
            "decisions": decisions,
            "action_items": action_items,
        }
        
        self.logger.info(f"✓ Summary generated")
        return result
    
    def _generate_summary(self, transcript: str, length: str = "medium") -> str:
        """
        Generate concise executive summary
        
        Args:
            transcript: Full transcript
            length: 'short' (100 words), 'medium' (200), 'long' (500)
            
        Returns:
            Summary text
        """
        length_hints = {
            "short": "100 words",
            "medium": "200 words",
            "long": "500 words",
        }
        
        prompt = f"""You are an expert meeting summarizer. Read the following meeting transcript and provide a clear, concise executive summary in {length_hints.get(length, '200 words')}.

The summary should capture:
- Main topics discussed
- Key decisions made
- Overall outcome of the meeting

Meeting Transcript:
{transcript[:2000]}

Executive Summary:"""
        
        summary = self.llm.generate(prompt, max_tokens=512)
        return summary.strip()
    
    def _extract_topics(self, transcript: str) -> List[str]:
        """
        Extract main topics from transcript
        
        Args:
            transcript: Full transcript
            
        Returns:
            List of topics
        """
        prompt = f"""Extract the main topics discussed in this meeting transcript. Return as a Python list of strings, one topic per line.

Format:
- Topic 1
- Topic 2
- Topic 3

Transcript:
{transcript[:2000]}

Topics:"""
        
        response = self.llm.generate(prompt, max_tokens=256)
        
        # Parse bullet points
        topics = [
            line.strip("- •").strip()
            for line in response.split("\n")
            if line.strip().startswith(("-", "•"))
        ]
        
        return topics[:10]  # Top 10 topics
    
    def _extract_decisions(self, transcript: str) -> List[str]:
        """
        Extract decisions made during meeting
        
        Args:
            transcript: Full transcript
            
        Returns:
            List of decisions
        """
        prompt = f"""Extract all decisions made in this meeting. Format as bullet points.

Transcript:
{transcript[:2000]}

Decisions made:"""
        
        response = self.llm.generate(prompt, max_tokens=256)
        
        decisions = [
            line.strip("- •").strip()
            for line in response.split("\n")
            if line.strip().startswith(("-", "•"))
        ]
        
        return decisions[:5]  # Top 5 decisions
    
    def _extract_action_items(self, transcript: str) -> List[Dict[str, str]]:
        """
        Extract action items with owner and deadline
        
        Args:
            transcript: Full transcript
            
        Returns:
            List of action items with task, owner, deadline
        """
        prompt = f"""Extract all action items from this meeting. For each action item, identify:
1. The task/action
2. The person responsible (owner)
3. The deadline (if mentioned, otherwise say "TBD")

Format each as:
Task: [task description]
Owner: [person name or "TBD"]
Deadline: [date or "TBD"]
---

Transcript:
{transcript[:2000]}

Action Items:"""
        
        response = self.llm.generate(prompt, max_tokens=512)
        
        # Parse action items
        action_items = self._parse_action_items(response)
        
        return action_items
    
    def _parse_action_items(self, response: str) -> List[Dict[str, str]]:
        """
        Parse LLM response into structured action items
        
        Args:
            response: LLM response text
            
        Returns:
            List of structured action items
        """
        items = []
        current_item = {}
        
        for line in response.split("\n"):
            line = line.strip()
            
            if line.startswith("Task:"):
                if current_item:
                    items.append(current_item)
                current_item = {"task": line.replace("Task:", "").strip()}
            elif line.startswith("Owner:"):
                current_item["owner"] = line.replace("Owner:", "").strip()
            elif line.startswith("Deadline:"):
                current_item["deadline"] = line.replace("Deadline:", "").strip()
            elif line == "---" and current_item:
                items.append(current_item)
                current_item = {}
        
        # Add last item
        if current_item:
            items.append(current_item)
        
        # Ensure all fields exist
        for item in items:
            item.setdefault("task", "")
            item.setdefault("owner", "TBD")
            item.setdefault("deadline", "TBD")
        
        return items[:10]  # Top 10 action items


if __name__ == "__main__":
    print("LLM Summarization module loaded")
