from llama_cpp import Llama
import logging
import os
import sys
from pathlib import Path
import gc
import warnings
from typing import Optional, Dict
import re
from app.db_operations_evaluation import DatabaseOperationsEvaluation
import json
from datetime import datetime
import torch

# Suppress all warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure logging with timestamp, level, and detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class LlamaEvaluator:
    def __init__(self) -> None:
        """
        Initialize Mistral-7B-Instruct-Ukrainian model for conversation evaluation.
        This model is specifically fine-tuned for Ukrainian language tasks with Q4_K_S quantization,
        providing optimal balance between performance and resource usage.
        """
        try:
            # Define the model name and directory
            model_name = "Mistral-7B-Instruct-Ukrainian.i1-Q4_K_S.gguf"  # Ukrainian-optimized model
            models_dir = Path("models")  # Directory where models are stored
            model_path = models_dir / model_name  # Full path to the model file

            # Log system information for debugging and monitoring
            logger.info(f"Python version: {sys.version}")
            logger.info(f"Current working directory: {os.getcwd()}")
            logger.info(f"Model path: {model_path.absolute()}")
            logger.info(f"Model file exists: {model_path.exists()}")

            if model_path.exists():
                # Log model file size to verify correct download and integrity
                logger.info(f"Model file size: {model_path.stat().st_size} bytes")

            # Verify models directory exists
            if not models_dir.exists():
                logger.error(f"Models directory not found at: {models_dir.absolute()}")
                raise FileNotFoundError(f"Models directory not found at: {models_dir.absolute()}")

            # Verify model file exists
            if not model_path.exists():
                logger.error(f"Model file not found at: {model_path.absolute()}")
                raise FileNotFoundError(f"Model file not found at: {model_path.absolute()}")

            # Test model file readability
            try:
                with open(model_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB to verify file integrity
                logger.info("Model file is readable")
            except Exception as read_error:
                logger.error(f"Cannot read model file: {str(read_error)}")
                raise

            logger.info("Initializing Mistral-7B-Instruct-Ukrainian model with optimized parameters...")

            # Initialize the model with parameters optimized for Ukrainian language processing
            self.model = Llama(
                model_path=str(model_path.resolve()),  # Absolute path to model
                n_ctx=8048,          # Context window size for conversation analysis
                n_threads=8,         # CPU threads for parallel processing
                n_gpu_layers=35,     # GPU layers for optimal 7B model performance
                n_batch=512,         # Batch size for efficient processing
                seed=42,             # Fixed seed for consistent evaluations
                verbose=True,        # Enable detailed logging for monitoring
                use_mlock=False,     # Disable memory locking for stability
                use_mmap=True        # Enable memory mapping for better performance
            )
            logger.info("Mistral-7B-Instruct-Ukrainian model initialized successfully")

        except FileNotFoundError as fnf_error:
            # Handle missing file errors with specific error messages
            logger.error(fnf_error)
            raise
        except Exception as e:
            # Handle other initialization errors with detailed logging
            logger.error(f"Mistral-7B-Instruct-Ukrainian model initialization failed: {str(e)}")
            raise

    def evaluate_conversation(self, conversation_text: str) -> tuple[Optional[str], int]:
        """
        Evaluate a conversation and generate a strict score with explanation.
        Returns both the evaluation text and the numeric mark.

        Args:
            conversation_text: The text to evaluate

        Returns:
            tuple[Optional[str], int]: Tuple containing (evaluation_text, mark)
        """
        try:
            if not conversation_text:
                logger.warning("Empty conversation text provided")
                return None, 0

            # Construct the evaluation prompt with strict criteria
            prompt = f"""[INST]Ви — максимально суворий та критичний аудитор контролю якості в контакт-центрі в компанії "MDM". 

ВАЖЛИВО: 
1. Відповідь має бути В ОДНОМУ РЯДКУ
2. Всі відповіді надавати ВИКЛЮЧНО українською мовою
3. Оцінювати МАКСИМАЛЬНО СУВОРО та КРИТИЧНО
4. НЕ більше 1000 символів відповіді
5. ТIЛЬКИ підсумок з оцінкою, НЕ треба обгрунтовувати вiдповiдь
6. КРИТЕРІЇ ЗНИЖЕННЯ ОЦІНКИ, ЇХ НЕ МОЖНА ПОКАЗУВАТИ ОПЕРАТОРУ
7. ПРИКЛАДИ ВІДПОВІДІ яким треба слідувати:
    8 Оператор продемонстрував високий рівень професіоналізму, чудово вирішив питання клієнта, проявив емпатію та дотримувався стандартів. Незначні помилки в мові не вплинули на якість обслуговування.
    5 Оператор частково вирішив питання клієнта, допустив кілька мовних помилок, не проявив достатньої емпатії, відповіді були неповними, але загальний підхід до обслуговування був задовільним.
    2 Оператор не вирішив питання клієнта, проявив агресію у спілкуванні, допустив численні мовні помилки, порушив стандарти обслуговування, відповіді були неточними та неповними.


ШКАЛА ОЦІНЮВАННЯ:
1. Оцінка 10 - практично НЕМОЖЛИВА, бо ідеальних діалогів не буває
2. Оцінка 9 - виключно для діалогів найвищої якості (менше 0.1% випадків)
3. Оцінка 8 - відмінне обслуговування з мінімальними недоліками (менше 1% випадків)
4. Оцінка 7 - дуже добре обслуговування з незначними помилками (до 5% випадків)
5. Оцінка 6 - добре обслуговування з кількома помилками (до 10% випадків)
6. Оцінка 5 - задовільне обслуговування з помітними недоліками (до 20% випадків)
7. Оцінка 4 - прийнятне обслуговування зі значними помилками (до 30% випадків)
8. Оцінка 3 - слабке обслуговування з суттєвими порушеннями (до 20% випадків)
9. Оцінка 2 - погане обслуговування з критичними помилками (до 10% випадків)
10. Оцінка 1 - неприйнятне обслуговування з грубими порушеннями (до 5% випадків)

КРИТЕРІЇ ЗНИЖЕННЯ ОЦІНКИ, ЇХ НЕ МОЖНА ПОКАЗУВАТИ ОПЕРАТОРУ.  :
- Будь-які помилки в мові (-2 бал за кожну)
- Неповні або неточні відповіді (-2 бал)
- Відсутність емпатії (-2 бал)
- Агресивний стиль спілкування (-2 бали)
- Порушення стандартів (-2 бали)
- Невирішене питання клієнта (-3 бали)

Оцініть максимально критично наступний діалог та надайте ТIЛЬКИ підсумок на Укр. мові з оцінкою, НЕ треба обгрунтовувати вiдповiдь:

{conversation_text}
ПРИКЛАДИ ВІДПОВІДІ яким треба слідувати:
8 Оператор продемонстрував високий рівень професіоналізму, чудово вирішив питання клієнта, проявив емпатію та дотримувався стандартів. Незначні помилки в мові не вплинули на якість обслуговування.
5 Оператор частково вирішив питання клієнта, допустив кілька мовних помилок, не проявив достатньої емпатії, відповіді були неповними, але загальний підхід до обслуговування був задовільним.
2 Оператор не вирішив питання клієнта, проявив агресію у спілкуванні, допустив численні мовні помилки, порушив стандарти обслуговування, відповіді були неточними та неповними.

Формат відповіді (все в одному рядку) НЕ більше 1300 символів, УКРАЇНСЬКОЮ МОВОЮ, можно менше:
[число] [пояснення чому знижена оцінка, своїми словами, НЕ використовуй ШКАЛУ ОЦІНЮВАННЯ, забудь про ШКАЛУ ОЦІНЮВАННЯ]
[/INST]"""

            logger.info("Sending prompt to Mistral model for evaluation")

            # Generate evaluation with strict parameters for consistent single response
            response = self.model.create_completion(
                prompt,
                max_tokens=500,             # Limit response length
                temperature=0.1,            # Very low temperature for consistency
                top_p=0.1,                 # Reduced for more focused sampling
                repeat_penalty=1.5,         # Increased to prevent repetition
                top_k=10,                  # Reduced for more focused output
                stop=["\n", "[INST]"]      # Stop at newlines or instruction tags
            )

            logger.debug(f"Raw response from model: {response}")

            # Extract and clean the response text
            evaluation_text = response['choices'][0]['text'].strip()
            logger.debug(f"Raw evaluation text: {evaluation_text}")

            # Enhanced cleaning process with specific text filtering
            evaluation_text = (evaluation_text
                .replace("[INST]", "")
                .replace("[/INST]", "")
                .replace("\n", " ")         # Replace newlines with spaces
                .replace("\r", " ")         # Replace carriage returns
                .replace("\t", " ")         # Replace tabs
                .replace("[REDACTED]", "")
                .replace("'", "")
                .replace('"', '')
                .strip())

            # Remove scale and criteria mentions with case variations
            for pattern in [
                "ШКАЛА ОЦІНЮВАННЯ",
                "шкала оцінювання",
                "Шкала оцінювання",
                "ШКАЛУ ОЦІНЮВАННЯ",
                "шкалу оцінювання",
                "Шкалу оцінювання",
                "КРИТЕРІЇ ЗНИЖЕННЯ",
                "критерії зниження",
                "Критерії зниження"
            ]:
                evaluation_text = re.sub(
                    f'\\[.*?{pattern}.*?\\]',  # Match any text in brackets containing the pattern
                    '',                         # Replace with empty string
                    evaluation_text            
                )

            # Clean up multiple spaces after filtering
            evaluation_text = " ".join(evaluation_text.split())

            logger.debug(f"Cleaned evaluation text: {evaluation_text}")

            # Remove specific unwanted text pattern
            unwanted_text = "Для отримання допомоги з питань навчання можна писати до нашої команди в Telegram: @EduGuru_UA або спробуйте у своєму бронюванні самостійно вирішити запитання, переглянувши інформацію у розділі Навчання сайту https://support.example.com/uk/learning. Там є багато корисної інформації щодо нашої платформи та порад з використання програмного забезпечення."
            evaluation_text = evaluation_text.replace(unwanted_text, "").strip()

            # First try to extract standalone number at start
            mark_match = re.match(r'^\s*(\d+)\s+', evaluation_text)
            if mark_match:
                mark = int(mark_match.group(1))
                logger.info(f"Extracted mark from start of text: {mark}")
            else:
                # Fallback patterns if no leading number found
                mark_patterns = [
                    r'Оцінка\s*:\s*(\d+)',
                    r'Оцінка\s*(\d+)',
                    r'(\d+)\s*балів',
                    r'(\d+)\s*бал'
                ]
                
                for pattern in mark_patterns:
                    match = re.search(pattern, evaluation_text)
                    if match:
                        mark = int(match.group(1))
                        logger.info(f"Extracted mark using pattern: {mark}")
                        break
                else:
                    mark = 0
                    logger.warning("No mark found in evaluation text")

            logger.info(f"Final evaluation text: {evaluation_text}")
            return evaluation_text, mark

        except Exception as e:
            logger.error(f"Evaluation generation failed: {str(e)}")
            return None, 0

    def cleanup(self):
        """
        Cleanup resources to free up memory.
        Frees GPU memory if used and performs garbage collection.
        """
        try:
            # Free up GPU memory if the model is loaded
            if hasattr(self, 'model'):
                del self.model
            gc.collect()  # Perform garbage collection to free up memory

            # If CUDA is available, clear the GPU cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Cleaned up Llama model and freed resources")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")

def evaluate_single(conversation_text: str) -> Optional[Dict]:
    """
    Evaluate a single conversation and return the evaluation results.

    Args:
        conversation_text: The text to evaluate

    Returns:
        Optional[Dict]: Evaluation results including original text and evaluation
    """
    evaluator = None
    try:
        logger.info("Starting single conversation evaluation")

        # Initialize the evaluator
        evaluator = LlamaEvaluator()

        # Perform the evaluation
        evaluation_text, mark = evaluator.evaluate_conversation(conversation_text)

        if not evaluation_text:
            logger.error("Single conversation evaluation failed")
            return None

        logger.info(f"Raw evaluation result: {evaluation_text}")

        # Prepare evaluation data as JSON for database storage
        evaluation_data = {
            'text': evaluation_text,
            'mark': mark,
            'evaluated_at': datetime.now().isoformat()
        }

        logger.info("Single conversation evaluation successful")
        return {
            'original_text': conversation_text,
            'evaluation': evaluation_text,
            'score': mark,
            'evaluation_data': evaluation_data
        }

    except Exception as e:
        logger.error(f"Single conversation evaluation failed: {str(e)}")
        return None
    finally:
        # Cleanup resources to free up memory
        if evaluator:
            evaluator.cleanup()

def evaluate_from_database(record_id: int) -> Optional[Dict]:
    """
    Evaluate a transcription from the database using LlamaEvaluator.
    
    Args:
        record_id: Database record ID to evaluate
        
    Returns:
        Optional[Dict]: Evaluation results or None if failed
    """
    evaluator = None
    try:
        # Initialize database operations with evaluation-specific class
        db_ops = DatabaseOperationsEvaluation()
        
        # Get speech data from database
        speech_data = db_ops.get_transcription(record_id)
        if not speech_data:
            logger.error(f"No speech data found for record {record_id}")
            return None

        # Get text from speech data
        text = speech_data.get('text')
        if not text:
            logger.error(f"No text found in speech data for record {record_id}")
            return None

        # Initialize evaluator and perform evaluation
        evaluator = LlamaEvaluator()
        evaluation_text, mark = evaluator.evaluate_conversation(text)

        if not evaluation_text:
            logger.error("Evaluation failed to produce text")
            return None

        # Return evaluation results
        return {
            'evaluation': evaluation_text,
            'score': mark
        }

    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        return None
    finally:
        # Clean up evaluator resources
        if evaluator:
            evaluator.cleanup()

def get_evaluation(evaluation_id: int) -> Optional[Dict]:
    """
    Get evaluation details from the database.
    
    Args:
        evaluation_id: Database record ID
        
    Returns:
        Optional[Dict]: Evaluation record or None if not found
    """
    try:
        logger.info(f"Fetching evaluation ID: {evaluation_id}")
        
        # Use evaluation-specific database operations
        db_ops = DatabaseOperationsEvaluation()
        return db_ops.get_evaluation(evaluation_id)

    except Exception as e:
        logger.error(f"Failed to get evaluation: {str(e)}")
        return None

# Command-line interface
if __name__ == "__main__":
    setup_utf8_encoding()
    
    if len(sys.argv) < 2:
        print("Usage: python fast_inference.py <record_id>", file=sys.stderr)
        sys.exit(1)

    try:
        record_id = int(sys.argv[1])
        result = evaluate_from_database(record_id)
        
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        else:
            print("Evaluation failed", file=sys.stderr, flush=True)
            sys.exit(1)

    except ValueError:
        print("Please provide a valid record ID", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr, flush=True)
        sys.exit(1) 