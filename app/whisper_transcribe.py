import whisper
import sys
import torch
import numpy as np
from pydub import AudioSegment
import tempfile
import os
import logging
import warnings
import codecs
from app.db_operations_whisper import DatabaseOperations

# Suppress all warnings from whisper and torch for cleaner output
warnings.filterwarnings('ignore')
torch.set_warn_always(False)

# Configure logging to only show errors and use UTF-8 encoding
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# Set UTF-8 encoding for stdout to handle multilingual transcriptions
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

class WhisperTranscriber:
    def __init__(self, model_name="large-v3"):
        """
        Initialize the transcriber with specified model and database connection.
        
        Args:
            model_name (str): Name of the Whisper model to use (default: large-v3)
        """
        self.model_name = model_name
        self.model = None
        # Set device to CUDA if available for faster processing
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Initialize database connection using the new DatabaseOperations class
        self.db = DatabaseOperations()
        logger.info(f"Using device: {self.device}")

    def load_model(self):
        """Load and prepare the Whisper model for transcription"""
        try:
            logger.info(f"Loading {self.model_name} model...")
            self.model = whisper.load_model(self.model_name)
            self.model = self.model.to(self.device)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def detect_language(self, audio_path):
        """
        Detect language from audio file.
        Takes a sample from the middle for efficient detection.
        
        Args:
            audio_path (str): Path to the audio file
            
        Returns:
            str: Detected language code (defaults to 'en' if detection fails)
        """
        try:
            # Load a small segment for language detection
            audio = whisper.load_audio(audio_path)
            
            # Take a 30-second segment from the middle for efficient detection
            duration = len(audio)
            mid_point = duration // 2
            segment_size = min(480000, duration)  # 30 seconds or less
            start = max(0, mid_point - segment_size // 2)
            audio_segment = audio[start:start + segment_size]
            
            # Detect language using the model
            result = self.model.transcribe(
                audio_segment,
                task="translate",
                language=None,
                fp16=torch.cuda.is_available()
            )
            
            detected_lang = result.get("language", "en")
            return detected_lang
            
        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            return "en"  # Default to English on failure

    def chunk_audio(self, audio_path, chunk_duration=240):
        """
        Split audio into manageable chunks for processing.
        
        Args:
            audio_path (str): Path to audio file
            chunk_duration (int): Length of each chunk in seconds (default: 4 minutes)
            
        Returns:
            list: List of audio chunks as numpy arrays
        """
        try:
            logger.info("Loading audio file for chunking...")
            audio = whisper.load_audio(audio_path)
            total_duration = len(audio) / 16000  # Convert to seconds
            logger.info(f"Total audio duration: {total_duration:.2f} seconds")
            
            # Calculate chunk parameters
            sample_rate = 16000  # Whisper uses 16kHz
            chunk_length = chunk_duration * sample_rate
            overlap_length = 5 * sample_rate  # 5 second overlap
            
            # Split audio into chunks with overlap
            chunks = []
            for i in range(0, len(audio), chunk_length - overlap_length):
                chunk = audio[i:min(i + chunk_length, len(audio))]
                # Skip chunks that are too short (less than 0.1 seconds)
                if len(chunk) < 1600:
                    continue
                chunks.append(np.array(chunk))
            
            logger.info(f"Created {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Audio chunking failed: {str(e)}")
            return None

    def transcribe_chunk(self, chunk, language):
        """
        Transcribe a single chunk of audio.
        
        Args:
            chunk (np.ndarray): Audio data as numpy array
            language (str): Language code for transcription
            
        Returns:
            dict: Transcription result including text and metadata
        """
        try:
            # Ensure chunk is properly formatted
            if not isinstance(chunk, np.ndarray):
                chunk = np.array(chunk)
            
            # Configure transcription options for optimal results
            options = {
                "task": "transcribe",
                "language": language,
                "temperature": 0,      # Use greedy decoding
                "best_of": 5,          # Number of candidates to consider
                "condition_on_previous_text": False,  # Prevent hallucinations
                "fp16": torch.cuda.is_available()
            }
            
            # Perform transcription
            result = self.model.transcribe(chunk, **options)
            return result
        except Exception as e:
            logger.error(f"Chunk transcription failed: {str(e)}")
            return None

    def process_audio(self, audio_path):
        """
        Process the complete audio file and return transcription.
        
        Args:
            audio_path (str): Path to the audio file
            
        Returns:
            str: Cleaned transcription text
        """
        try:
            if self.model is None:
                self.load_model()
            
            # Detect language and chunk audio
            language = self.detect_language(audio_path)
            chunks = self.chunk_audio(audio_path)
            if not chunks:
                raise Exception("Failed to create audio chunks")
            
            # Process each chunk and combine results
            full_text = ""
            for chunk in chunks:
                result = self.transcribe_chunk(chunk, language)
                if result:
                    if full_text and result["text"]:
                        full_text += " "
                    full_text += result["text"].strip()
            
            # Clean up and return the text
            return self._clean_text(full_text)

        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            return None

    def _clean_text(self, text):
        """
        Clean up text by removing repetitions and formatting.
        Uses an aggressive approach to catch various types of repetitions.
        
        Args:
            text (str): Raw transcription text
            
        Returns:
            str: Cleaned text without repetitions
        """
        # Split into words for processing
        words = text.split()
        cleaned_words = []
        i = 0
        
        while i < len(words):
            current_word = words[i]
            should_add = True
            
            # Look back for repetitions (up to 4 words)
            look_back = min(4, len(cleaned_words))
            for j in range(1, look_back + 1):
                if i + j <= len(words) and [w.lower() for w in cleaned_words[-j:]] == [w.lower() for w in words[i:i+j]]:
                    should_add = False
                    i += j
                    break
            
            # Look ahead for repetitions (up to 4 words)
            if should_add and i + 1 < len(words):
                look_ahead = min(4, len(words) - i)
                for j in range(1, look_ahead):
                    if [w.lower() for w in words[i:i+j]] == [w.lower() for w in words[i+j:i+j*2]]:
                        should_add = False
                        i += j
                        break
            
            # Add word if it's not part of a repetition
            if should_add:
                if not cleaned_words or current_word.lower() != cleaned_words[-1].lower():
                    cleaned_words.append(current_word)
                i += 1
            
        # Join words maintaining original case
        result = ' '.join(cleaned_words)
        return result.strip()

def format_timestamp(seconds):
    """
    Convert seconds to HH:MM:SS format.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def main(audio_path):
    """
    Main execution function for command-line usage.
    
    Args:
        audio_path (str): Path to the audio file to transcribe
    """
    try:
        transcriber = WhisperTranscriber()
        result = transcriber.process_audio(audio_path)
        
        if not result:
            logger.error("Transcription failed")
            
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Please provide an audio file path")
        sys.exit(1)
    
    main(sys.argv[1])