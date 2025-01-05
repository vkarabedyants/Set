import numpy as np
import librosa
import soundfile as sf
import logging
import os
import noisereduce as nr
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WhisperNoiseReducer:
    def __init__(self):
        """
        Initialize noise reducer optimized for Whisper
        - Uses 16kHz sample rate (Whisper requirement)
        - Mono audio (Whisper requirement)
        """
        self.target_sr = 16000  # Whisper's required sample rate
        self.target_channels = 1  # Mono audio

    def process_audio(self, input_path, output_path=None):
        """
        Process audio file with noise reduction
        
        Args:
            input_path (str): Path to input audio file
            output_path (str, optional): Path for processed audio
        
        Returns:
            str: Path to processed audio file
        """
        try:
            logger.info(f"Processing audio file: {input_path}")

            # Generate output path if not provided
            if output_path is None:
                directory = os.path.dirname(input_path)
                filename = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(directory, f"{filename}_clean.wav")

            # Load audio file
            logger.info("Loading audio file...")
            audio, sr = librosa.load(
                input_path,
                sr=None,  # Keep original sample rate initially
                mono=True  # Convert to mono
            )

            # Process audio
            processed_audio = self._reduce_noise(audio, sr)
            
            # Save processed audio
            logger.info(f"Saving processed audio to: {output_path}")
            sf.write(
                output_path,
                processed_audio,
                self.target_sr,
                'PCM_16'  # 16-bit PCM format
            )

            return output_path

        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            return None

    def _reduce_noise(self, audio, original_sr):
        """
        Reduce noise in audio, optimized for Whisper
        
        Args:
            audio (np.array): Input audio data
            original_sr (int): Original sample rate
        
        Returns:
            np.array: Noise-reduced audio
        """
        try:
            # 1. Resample if necessary
            if original_sr != self.target_sr:
                logger.info(f"Resampling from {original_sr}Hz to {self.target_sr}Hz")
                audio = librosa.resample(
                    audio,
                    orig_sr=original_sr,
                    target_sr=self.target_sr
                )

            # 2. Apply noise reduction
            logger.info("Applying noise reduction...")
            # Use statistical noise reduction
            audio = nr.reduce_noise(
                y=audio,
                sr=self.target_sr,
                stationary=True,     # Assume stationary background noise
                prop_decrease=0.75,  # Less aggressive noise reduction
                n_fft=2048,         # FFT window size
                win_length=2048,     # Window length
                hop_length=512,      # Hop length
                n_std_thresh_stationary=1.2,  # Noise threshold
                n_jobs=1            # Single process
            )

            # 3. Normalize audio
            logger.info("Normalizing audio...")
            audio = librosa.util.normalize(audio)

            return audio

        except Exception as e:
            logger.error(f"Error in noise reduction: {str(e)}")
            raise

def process_audio_file(input_path, output_path=None):
    """
    Convenience function to process a single audio file
    
    Args:
        input_path (str): Path to input audio file
        output_path (str, optional): Path for output file
    
    Returns:
        str: Path to processed file
    """
    processor = WhisperNoiseReducer()
    return processor.process_audio(input_path, output_path)

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Reduce noise in audio file for Whisper'
    )
    parser.add_argument('input_file', help='Input audio file path')
    parser.add_argument('--output_file', help='Output audio file path (optional)')
    
    args = parser.parse_args()
    
    processed_file = process_audio_file(
        args.input_file,
        args.output_file
    )
    
    if processed_file:
        logger.info(f"Successfully processed audio file: {processed_file}")
    else:
        logger.error("Failed to process audio file") 