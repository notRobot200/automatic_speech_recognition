import streamlit as st
import speech_recognition as sr
import os
import tempfile
from pathlib import Path
from typing import Optional
from core.audio_processor import AudioProcessor
from core.exceptions import AudioTranscriptionError
from config.settings import SUPPORTED_FORMATS, SUPPORTED_LANGUAGES
from utils.logger import logger


class StreamlitUI:
    def __init__(self):
        """Initialize StreamlitUI with AudioProcessor."""
        self.processor = AudioProcessor()
        self.setup_page_config()
        # Initialize session states
        if 'transcript' not in st.session_state:
            st.session_state.transcript = []
        if 'file_transcription' not in st.session_state:
            st.session_state.file_transcription = None

    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="Automatic Speech Recognition App",
            page_icon="🎤",
            initial_sidebar_state="collapsed"
        )
        st.title("🎤 Automatic Speech Recognition")
        st.subheader("Upload Audio or Use Microphone")

    def process_uploaded_file(self, uploaded_file) -> Optional[str]:
        """Process an uploaded audio file and return its transcription."""
        temp_file_path = None
        try:
            selected_language = st.session_state.get('language_code', 'en-US')

            # Create a temporary file
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_file_path = temp_file.name

            # Convert to WAV if needed
            if suffix.lower()[1:] in ['mp3', 'm4a']:
                wav_path = self.processor.convert_to_wav(temp_file_path)
                os.remove(temp_file_path)
                temp_file_path = wav_path

            # Display audio player
            st.audio(temp_file_path, format="audio/wav")

            with st.spinner("Processing transcription..."):
                return self.processor.transcribe_audio(temp_file_path, selected_language)

        except AudioTranscriptionError as e:
            st.error(str(e))
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            logger.error(f"Unexpected error: {e}")
            return None
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def handle_microphone_input(self):
        """Handle real-time speech recognition from the microphone."""
        recording = True
        selected_language = st.session_state.get('language_code', 'en-US')

        try:
            with sr.Microphone() as source:
                st.info("Please speak...")
                self.processor.recognizer.adjust_for_ambient_noise(source, duration=1)

                col1, col2 = st.columns([5, 1])
                with col2:
                    if st.button("🛑 Stop", use_container_width=True):
                        recording = False
                        return

                transcript_container = st.container()

                while recording:
                    with st.spinner("Listening..."):
                        try:
                            audio = self.processor.recognizer.listen(
                                source,
                                timeout=None,
                                phrase_time_limit=None
                            )
                            text = self.processor.recognizer.recognize_google(
                                audio,
                                language=selected_language
                            )
                            if text:
                                st.session_state.transcript.append(text)
                                with transcript_container:
                                    st.markdown("**Transcription:**")
                                    st.write(" ".join(st.session_state.transcript))
                        except sr.UnknownValueError:
                            continue
                        except sr.RequestError as e:
                            st.error(f"🚫 Google Speech Recognition service error: {str(e)}")
                            break

        except Exception as e:
            st.error(f"🚫 Microphone error: {str(e)}")
            logger.error(f"Microphone error: {e}")

    def render(self):
        """Render the main UI and handle user interactions."""
        selected_language = st.selectbox(
            "Select language:",
            options=list(SUPPORTED_LANGUAGES.keys()),
            index=0,
            help="Choose the language for automatic speech recognition"
        )
        st.session_state.language_code = SUPPORTED_LANGUAGES[selected_language]

        option = st.radio(
            "Select audio source:",
            ["Upload File", "Use Microphone (Real-time)"],
            key="audio_source"
        )

        if option == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload an audio file (MP3/WAV/M4A)",
                type=SUPPORTED_FORMATS,
                help="Select an audio file for transcription"
            )

            if uploaded_file:
                # Only process if we haven't processed this file before
                file_key = f"{uploaded_file.name}_{uploaded_file.size}"
                if 'current_file_key' not in st.session_state:
                    st.session_state.current_file_key = None

                if file_key != st.session_state.current_file_key:
                    st.session_state.current_file_key = file_key
                    transcription = self.process_uploaded_file(uploaded_file)
                    if transcription:
                        st.session_state.file_transcription = transcription

                # Display transcription if available
                if st.session_state.file_transcription:
                    st.success("**Transcription Result:**")
                    st.write(st.session_state.file_transcription)

                    # Add download button
                    st.divider()
                    original_filename = Path(uploaded_file.name).stem
                    download_filename = f"{original_filename}_transcription.txt"
                    self.create_download_button(st.session_state.file_transcription, download_filename)

        else:  # Microphone option
            st.write("Click the button to start recording")
            if st.button("🎙️ Start Recording", use_container_width=True):
                st.session_state.transcript = []
                self.handle_microphone_input()

            if st.session_state.transcript:
                full_transcript = " ".join(st.session_state.transcript)

                st.markdown("**Transcription Result:**")
                st.write(full_transcript)

                # Add download button
                st.divider()
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                download_filename = f"microphone_transcription_{timestamp}.txt"
                self.create_download_button(full_transcript, download_filename)

    def create_download_button(self, text: str, filename: str = "transcription.txt"):
        """Create download buttons for the transcription text."""
        try:
            col1, col2 = st.columns(2)

            # Basic text download
            with col1:
                st.download_button(
                    label="📥 Download as TXT",
                    data=text,
                    file_name=filename,
                    mime="text/plain",
                    use_container_width=True
                )

            # DOCX download
            with col2:
                from io import BytesIO
                from docx import Document

                doc = Document()
                doc.add_paragraph(text)

                docx_buffer = BytesIO()
                doc.save(docx_buffer)
                docx_buffer.seek(0)

                st.download_button(
                    label="📥 Download as DOCX",
                    data=docx_buffer,
                    file_name=filename.replace('.txt', '.docx'),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"Error creating download button: {str(e)}")
            logger.error(f"Download button error: {e}")