from typing import Dict, Optional, Tuple, List
import logging
from datetime import datetime
from app.db_handler import DatabaseHandler
from psycopg2.extras import Json
import json

# Configure logging with UTF-8 support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

class DatabaseOperationsEvaluation:
    """
    Handle database operations specifically for LLM evaluations.
    Provides a clean interface for storing and retrieving evaluation data.
    """
    
    def __init__(self):
        """Initialize database handler for connection management"""
        self.db = DatabaseHandler()

    def close(self):
        """
        Close database connection.
        This method is required by evaluation components.
        """
        try:
            if self.db:
                self.db.close()
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")

    def store_evaluation(self, record_id: int, evaluation_data: Dict) -> bool:
        """
        Store evaluation results for an existing record.
        
        Args:
            record_id (int): Database record ID
            evaluation_data (Dict): Dictionary containing:
                - text: Evaluation text
                - mark: Numerical score
                - evaluated_at: ISO format timestamp
                - status: Evaluation status (e.g., 'completed')
                
        Returns:
            bool: True if storage successful, False otherwise
        """
        try:
            if not self.db.connect():
                logger.error("Database connection failed during store_evaluation")
                return False

            # Update evaluation fields using created_at instead of updated_at
            self.db.cursor.execute("""
                UPDATE voice_evaluations 
                SET evaluation = %s::jsonb,
                    mark = %s,
                    created_at = %s
                WHERE id = %s
                """, 
                (
                    Json(evaluation_data),         # Convert to JSONB
                    evaluation_data.get('mark', 0),# Get mark or default to 0
                    datetime.now(),                # Update timestamp
                    record_id
                )
            )
            
            if self.db.cursor.rowcount == 0:
                logger.error(f"No record found for ID: {record_id}")
                self.db.conn.rollback()
                return False

            self.db.conn.commit()
            logger.info(f"Successfully stored evaluation for ID: {record_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store evaluation: {str(e)}")
            if self.db.conn:
                self.db.conn.rollback()
            return False
        finally:
            self.db.close()

    def get_evaluation(self, record_id: int) -> Optional[Dict]:
        """
        Retrieve evaluation data by ID.
        
        Args:
            record_id (int): Database record ID
            
        Returns:
            Optional[Dict]: Evaluation data if found, including:
                - speech: Speech data dictionary
                - evaluation: Evaluation data dictionary
                - mark: Numeric score
                - created_at: Timestamp
        """
        try:
            if not self.db.connect():
                logger.error("Database connection failed during get_evaluation")
                return None

            self.db.cursor.execute("""
                SELECT speech, evaluation, mark, created_at 
                FROM voice_evaluations 
                WHERE id = %s
            """, (record_id,))
            
            result = self.db.cursor.fetchone()
            if not result:
                logger.info(f"No evaluation found for ID: {record_id}")
                return None

            # Convert datetime to ISO format string for JSON serialization
            created_at = result[3].isoformat() if result[3] else None
                
            return {
                'speech': result[0],
                'evaluation': result[1],
                'mark': result[2],
                'created_at': created_at
            }

        except Exception as e:
            logger.error(f"Failed to retrieve evaluation: {str(e)}")
            return None
        finally:
            self.db.close()

    def get_transcription(self, record_id: int) -> Optional[Dict]:
        """
        Retrieve transcription data by ID for evaluation.
        
        Args:
            record_id (int): Database record ID
            
        Returns:
            Optional[Dict]: Speech data if found
        """
        try:
            if not self.db.connect():
                logger.error("Database connection failed during get_transcription")
                return None

            self.db.cursor.execute("""
                SELECT speech 
                FROM voice_evaluations 
                WHERE id = %s
            """, (record_id,))
            
            result = self.db.cursor.fetchone()
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Failed to retrieve transcription: {str(e)}")
            return None
        finally:
            self.db.close()

    def get_all_transcriptions(self) -> List[Dict]:
        """
        Retrieve all transcription records from the database with evaluations.
        
        Returns:
            List[Dict]: List of transcription records, each containing:
                - id: Record ID
                - text: Transcribed text (from speech_data JSONB)
                - evaluation: Evaluation data (JSONB)
                - mark: Evaluation mark
                - created_at: Timestamp of creation
        """
        try:
            if not self.db.connect():
                logger.error("Database connection failed during get_all_transcriptions")
                return []

            # Query all records with JSONB fields properly extracted
            self.db.cursor.execute("""
                SELECT 
                    id,
                    speech_data->>'text' as text,
                    evaluation,
                    mark,
                    created_at
                FROM voice_evaluations 
                ORDER BY created_at DESC
            """)
            
            # Fetch all records
            records = self.db.cursor.fetchall()
            
            # Convert to list of dictionaries
            result = []
            for record in records:
                result.append({
                    'id': record[0],
                    'text': record[1],        # From speech_data JSONB
                    'evaluation': record[2],   # Already JSONB
                    'mark': record[3],
                    'created_at': record[4]
                })
                
            logger.info(f"Retrieved {len(result)} evaluation records")
            return result

        except Exception as e:
            logger.error(f"Failed to get transcriptions: {str(e)}")
            return []
        finally:
            self.db.close()

# Module execution check
if __name__ == "__main__":
    logger.info("Evaluation database operations module loaded") 