"""
Streamlit Web Application for Meeting Summarizer
Provides an intuitive web interface for uploading and processing meeting recordings
"""

import streamlit as st
import os
import json
from pathlib import Path
from datetime import datetime
import tempfile
from src.pipeline import MeetingSummarizerPipeline
from src.utils import validate_audio_file

# Page configuration
st.set_page_config(
    page_title="Meeting Summarizer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem 0;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        color: #1e1e1e;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        color: #1e1e1e;
    }
    .action-item {
        background-color: #fff3cd;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        border-left: 3px solid #ffc107;
        color: #1e1e1e;
    }
    .decision-item {
        background-color: #d1ecf1;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        border-left: 3px solid #17a2b8;
        color: #1e1e1e;
    }
    .topic-badge {
        display: inline-block;
        background-color: #667eea;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        margin: 0.25rem;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'pipeline' not in st.session_state:
    st.session_state.pipeline = None

def init_pipeline():
    """Initialize the summarization pipeline"""
    if st.session_state.pipeline is None:
        with st.spinner("Initializing AI models... This may take a minute on first run."):
            st.session_state.pipeline = MeetingSummarizerPipeline()
    return st.session_state.pipeline

def process_audio(audio_file, audio_path):
    """Process the uploaded audio file"""
    try:
        st.session_state.processing = True
        
        # Initialize pipeline
        pipeline = init_pipeline()
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Stage 1: Loading audio
        status_text.text("📂 Loading audio file...")
        progress_bar.progress(10)
        
        # Stage 2: Transcription
        status_text.text("🎤 Transcribing audio with Whisper AI... (this may take a few minutes)")
        progress_bar.progress(20)
        
        # Process the meeting
        result = pipeline.process_meeting(audio_path)
        
        # Stage 3: Text processing
        status_text.text("📝 Processing transcript...")
        progress_bar.progress(60)
        
        # Stage 4: AI Summarization
        status_text.text("🤖 Generating summary with local LLM...")
        progress_bar.progress(80)
        
        # Complete
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        
        st.session_state.results = result
        st.session_state.processing = False
        
        return result
        
    except Exception as e:
        st.session_state.processing = False
        st.error(f"❌ Error processing audio: {str(e)}")
        return None

def display_results(result):
    """Display the summarization results"""
    if not result:
        return
    
    # Summary section
    st.markdown('<div class="section-header">📋 Executive Summary</div>', unsafe_allow_html=True)
    summary_text = result.get("summary", "No summary available")
    st.markdown(f'<div class="info-box">{summary_text}</div>', unsafe_allow_html=True)
    
    # Create two columns for topics and metadata
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Topics
        st.markdown('<div class="section-header">🏷️ Key Topics</div>', unsafe_allow_html=True)
        topics = result.get("topics", [])
        if topics:
            topics_html = "".join([f'<span class="topic-badge">{topic}</span>' for topic in topics])
            st.markdown(f'<div>{topics_html}</div>', unsafe_allow_html=True)
        else:
            st.write("No topics extracted")
    
    with col2:
        # Metadata
        st.markdown('<div class="section-header">ℹ️ Meeting Info</div>', unsafe_allow_html=True)
        metadata = result.get("metadata", {})
        audio_info = metadata.get("audio", {})
        duration = audio_info.get('duration_seconds', 0)
        transcript = result.get("transcript", "")
        word_count = len(transcript.split()) if transcript else 0
        
        if duration > 0:
            st.write(f"**Duration:** {int(duration)} seconds ({duration/60:.1f} min)")
        else:
            st.write(f"**Duration:** N/A")
        st.write(f"**Word Count:** {word_count}")
        st.write(f"**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Decisions
    if result.get("decisions"):
        st.markdown('<div class="section-header">⚖️ Key Decisions</div>', unsafe_allow_html=True)
        for i, decision in enumerate(result["decisions"], 1):
            st.markdown(f'<div class="decision-item"><strong>Decision {i}:</strong> {decision}</div>', 
                       unsafe_allow_html=True)
    
    # Action Items
    if result.get("action_items"):
        st.markdown('<div class="section-header">✅ Action Items</div>', unsafe_allow_html=True)
        for item in result["action_items"]:
            if isinstance(item, dict):
                owner = item.get("owner", "Unassigned")
                task = item.get("task", "")
                deadline = item.get("deadline", "No deadline")
                st.markdown(
                    f'<div class="action-item">'
                    f'<strong>👤 {owner}</strong><br>'
                    f'📌 {task}<br>'
                    f'📅 Deadline: {deadline}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f'<div class="action-item">{item}</div>', unsafe_allow_html=True)
    
    # Transcript section (collapsible)
    with st.expander("📄 Full Transcript", expanded=False):
        st.text_area("Transcript", result.get("transcript", ""), height=300, disabled=True)
    
    # Download section
    st.markdown('<div class="section-header">💾 Download Results</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON download
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"meeting_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col2:
        # Text download
        text_summary = f"""MEETING SUMMARY
{'='*80}

EXECUTIVE SUMMARY
{result.get('summary', 'No summary available')}

KEY TOPICS
{', '.join(result.get('topics', ['None']))}

KEY DECISIONS
{chr(10).join(f"{i}. {d}" for i, d in enumerate(result.get('decisions', []), 1)) if result.get('decisions') else 'None'}

ACTION ITEMS
{chr(10).join(f"- {item}" for item in result.get('action_items', [])) if result.get('action_items') else 'None'}

FULL TRANSCRIPT
{result.get('transcript', 'No transcript available')}
"""
        st.download_button(
            label="📥 Download Text",
            data=text_summary,
            file_name=f"meeting_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

def main():
    # Header
    st.markdown('<h1 class="main-header">🎙️ AI Meeting Summarizer</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; color: #666; font-size: 1.1rem;">'
        'Transform your meeting recordings into actionable insights using local AI'
        '</p>',
        unsafe_allow_html=True
    )
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/microphone.png", width=80)
        st.title("About")
        st.info(
            "This application uses **OpenAI Whisper** for speech-to-text transcription "
            "and **local LLM** (Mistral 7B via Ollama) for intelligent summarization. "
            "\n\nAll processing happens **locally** on your machine - no data is sent to external servers."
        )
        
        st.markdown("---")
        st.subheader("Supported Formats")
        st.write("✅ MP3")
        st.write("✅ WAV")
        st.write("✅ M4A")
        st.write("✅ OGG")
        st.write("✅ FLAC")
        
        st.markdown("---")
        st.subheader("Features")
        st.write("�️ Record Audio Live")
        st.write("📤 Upload Audio Files")
        st.write("�🎯 Executive Summary")
        st.write("🏷️ Topic Extraction")
        st.write("⚖️ Key Decisions")
        st.write("✅ Action Items")
        st.write("📄 Full Transcript")
        
        st.markdown("---")
        st.caption("Powered by OpenAI Whisper & Ollama")
    
    # Main content area
    st.markdown("---")
    
    # Tabs for upload or record
    tab1, tab2 = st.tabs(["📤 Upload Recording", "🎤 Record Meeting"])
    
    uploaded_file = None
    
    with tab1:
        # File upload section
        st.subheader("Upload Meeting Recording")
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['mp3', 'wav', 'm4a', 'ogg', 'flac'],
            help="Upload your meeting recording in any supported format",
            key="upload_file"
        )
    
    with tab2:
        # Audio recording section
        st.subheader("Record Meeting Audio")
        st.info("🎙️ Click the button below to start recording your meeting. Click stop when finished.")
        
        try:
            from st_audiorec import st_audiorec
            
            audio_bytes = st_audiorec()
            
            if audio_bytes:
                st.success("✅ Recording captured! Click 'Process Meeting' below to analyze.")
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_path = tmp_file.name
                
                # Store in session state
                st.session_state['recorded_audio_path'] = tmp_path
                
                # Create a pseudo uploaded file object
                class RecordedFile:
                    def __init__(self, path):
                        self.name = "recorded_meeting.wav"
                        self.size = os.path.getsize(path)
                    
                uploaded_file = RecordedFile(tmp_path)
        except ImportError:
            st.warning("⚠️ Audio recording feature requires 'streamlit-audiorec' package.")
            if st.button("📦 Install Package"):
                st.code("pip install streamlit-audiorec", language="bash")
            st.info("💡 For now, please use the 'Upload Recording' tab.")
    
    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size / 1024 / 1024:.2f} MB")
        with col3:
            st.metric("Format", uploaded_file.name.split('.')[-1].upper())
        
        # Process button
        if st.button("🚀 Process Meeting", type="primary", disabled=st.session_state.processing):
            # Check if this is a recorded file or uploaded file
            if hasattr(uploaded_file, 'getvalue'):
                # Regular uploaded file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
            else:
                # Recorded file - path already in session state
                tmp_path = st.session_state.get('recorded_audio_path')
            
            try:
                # Validate audio file
                is_valid, message = validate_audio_file(tmp_path)
                if not is_valid:
                    st.error(f"❌ Invalid audio file: {message}")
                else:
                    # Process the audio
                    result = process_audio(uploaded_file, tmp_path)
                    
                    if result:
                        st.success("✅ Meeting processed successfully!")
                        st.balloons()
            finally:
                # Clean up temp file only if it was an upload (not recorded)
                if hasattr(uploaded_file, 'getvalue') and os.path.exists(tmp_path):
                    os.remove(tmp_path)
    
    # Display results if available
    if st.session_state.results:
        st.markdown("---")
        st.markdown("## 📊 Results")
        display_results(st.session_state.results)
    
    # Instructions when no file uploaded
    if uploaded_file is None and st.session_state.results is None:
        st.markdown("---")
        st.markdown("### 🎬 Getting Started")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 1️⃣ Upload")
            st.write("Upload your meeting recording using the file uploader above")
        
        with col2:
            st.markdown("#### 2️⃣ Process")
            st.write("Click the 'Process Meeting' button to start AI analysis")
        
        with col3:
            st.markdown("#### 3️⃣ Review")
            st.write("Get your summary, action items, and full transcript")
        
        st.markdown("---")
        st.info("💡 **Tip:** First-time processing may take longer as AI models are loaded into memory.")

if __name__ == "__main__":
    main()
