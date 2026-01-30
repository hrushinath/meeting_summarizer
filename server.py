"""
FastAPI Optional Server
Provides REST API for meeting summarization
Run with: uvicorn server:app --reload
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile
import os

from src.pipeline import MeetingSummarizerPipeline
from src.utils import logger, validate_audio_file
from config.settings import SUPPORTED_AUDIO_FORMATS

# Initialize FastAPI app
app = FastAPI(
    title="Meeting Summarizer API",
    description="Convert meeting audio to structured summaries",
    version="1.0.0"
)

# Initialize pipeline (lazy load)
pipeline = None

def get_pipeline():
    """Get or create pipeline instance"""
    global pipeline
    if pipeline is None:
        pipeline = MeetingSummarizerPipeline()
    return pipeline


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "ok",
        "service": "Meeting Summarizer API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/summarize")
async def summarize_meeting(
    file: UploadFile = File(...),
    title: str = None
):
    """
    Summarize a meeting from audio file
    
    Args:
        file: Audio file (MP3, WAV, M4A, OGG, FLAC)
        title: Optional meeting title
        
    Returns:
        JSON with summary, topics, decisions, action items
    """
    try:
        # Validate file type
        if not any(file.filename.endswith(fmt) for fmt in SUPPORTED_AUDIO_FORMATS):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Supported: {SUPPORTED_AUDIO_FORMATS}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            # Process meeting
            pipeline = get_pipeline()
            result = pipeline.process_meeting(
                tmp_path,
                meeting_title=title or file.filename
            )
            
            # Return structured result
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "meeting_title": result["meeting_title"],
                    "summary": result["summary"],
                    "key_topics": result["key_topics"],
                    "decisions": result["decisions"],
                    "action_items": result["action_items"],
                    "metadata": result["metadata"]
                }
            )
        
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)
    
    except Exception as e:
        logger.error(f"API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )


@app.get("/info")
async def get_info():
    """Get system information"""
    return {
        "service": "Meeting Summarizer API",
        "version": "1.0.0",
        "supported_formats": SUPPORTED_AUDIO_FORMATS,
        "components": {
            "stt": "OpenAI Whisper",
            "llm": "Ollama or HuggingFace Transformers",
            "text_processing": "NLTK"
        }
    }


# Optional: Add CORS for browser requests
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*80)
    print("Starting Meeting Summarizer API")
    print("="*80)
    print("\nAPI will be available at: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Swagger UI: http://localhost:8000/redoc")
    print("\n" + "="*80 + "\n")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
