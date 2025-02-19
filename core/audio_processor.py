import whisper
import speech_recognition as sr
from pydub import AudioSegment
# import imageio_ffmpeg as ffmpeg
import ffmpeg
from pathlib import Path
# from utils.logger import logger
from core.exceptions import AudioTranscriptionError
from config.settings import WHISPER_MODEL_SIZE
import pydub

class AudioProcessor:
    def __init__(self):
        """Initialize AudioProcessor with necessary configurations."""
        # AudioSegment.converter = ffmpeg.get_ffmpeg_exe()
        self.model = whisper.load_model(WHISPER_MODEL_SIZE)
        self.recognizer = sr.Recognizer()

    def transcribe_audio(self, audio_path: str, language_code: str = 'en-US') -> str:
        """
        Transcribe audio using the Whisper model.

        Args:
            audio_path: Path to the audio file
            language_code: Language code for transcription (e.g., 'en-US', 'id-ID')

        Returns:
            Transcribed text

        Raises:
            AudioTranscriptionError: If transcription fails
        """
        try:
            whisper_language = language_code.split('-')[0]
            result = self.model.transcribe(audio_path, language=whisper_language)
            return result["text"]
        except Exception as e:
            # logger.error(f"Transcription error: {e}")
            raise AudioTranscriptionError(f"Failed to transcribe audio: {str(e)}")

    def convert_to_wav(self, input_path: str) -> str:
        """
        Convert an audio file to WAV format.

        Args:
            input_path: Path to the input audio file

        Returns:
            Path to the converted WAV file
        """
        try:
            audio = AudioSegment.from_file(input_path)
            wav_path = str(Path(input_path).with_suffix('.wav'))
            audio.export(wav_path, format="wav")
            return wav_path
        except Exception as e:
            # logger.error(f"Conversion error: {e}")
            raise AudioTranscriptionError(f"Failed to convert audio: {str(e)}")
