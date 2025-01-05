from typing import List, Dict, Optional
import logging
from datetime import datetime
from app.db_operations_whisper import DatabaseOperations as WhisperDB
from app.db_operations_evaluation import DatabaseOperationsEvaluation as EvalDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def get_all_evaluations() -> List[Dict]:
    """
    Retrieve all evaluations with their transcriptions.
    Returns a list of records with both evaluation and transcription data.
    """
    try:
        whisper_db = WhisperDB()
        eval_db = EvalDB()
        
        # Get all transcriptions
        transcriptions = whisper_db.get_all_transcriptions()
        if not transcriptions:
            return []

        # Get evaluations for each transcription
        result = []
        for record in transcriptions:
            record_id = record.get('id')
            evaluation = eval_db.get_evaluation(record_id) if record_id else None
            
            # Combine transcription and evaluation data
            combined_data = {
                'id': record_id,
                'transcription': record.get('text', ''),
                'created_at': record.get('created_at', '').isoformat() if record.get('created_at') else None,
                'file_info': {
                    'filename': record.get('filename', ''),
                    'file_type': record.get('file_type', '')
                },
                'evaluation': evaluation.get('evaluation', {}) if evaluation else None,
                'mark': evaluation.get('mark') if evaluation else None,
                'evaluated_at': evaluation.get('evaluated_at') if evaluation else None
            }
            result.append(combined_data)

        return result

    except Exception as e:
        logger.error(f"Failed to retrieve evaluations: {str(e)}")
        return []

def get_evaluation_statistics() -> Dict:
    """
    Get statistics about evaluations.
    Returns counts and averages of evaluations.
    """
    try:
        eval_db = EvalDB()
        whisper_db = WhisperDB()
        
        # Get all records
        transcriptions = whisper_db.get_all_transcriptions()
        total_records = len(transcriptions) if transcriptions else 0
        
        # Calculate statistics
        total_evaluated = 0
        total_mark = 0
        marks_distribution = {i: 0 for i in range(1, 11)}
        
        for record in transcriptions:
            evaluation = eval_db.get_evaluation(record.get('id'))
            if evaluation and evaluation.get('mark'):
                total_evaluated += 1
                mark = evaluation['mark']
                total_mark += mark
                marks_distribution[mark] = marks_distribution.get(mark, 0) + 1
        
        return {
            'total_records': total_records,
            'evaluated_records': total_evaluated,
            'pending_evaluations': total_records - total_evaluated,
            'average_mark': round(total_mark / total_evaluated, 2) if total_evaluated > 0 else 0,
            'marks_distribution': marks_distribution
        }

    except Exception as e:
        logger.error(f"Failed to retrieve statistics: {str(e)}")
        return {
            'total_records': 0,
            'evaluated_records': 0,
            'pending_evaluations': 0,
            'average_mark': 0,
            'marks_distribution': {i: 0 for i in range(1, 11)}
        } 