from typing import Dict, Optional, Tuple, List
import logging
from datetime import datetime
from app.db_handler import DatabaseHandler
from psycopg2.extras import Json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

class DatabaseOperations:
    """
    Handle database operations specifically for Whisper transcriptions.
    Provides a clean interface for storing and retrieving transcription data.
    """
    
    def __init__(self):
        """Initialize database handler for connection management"""
        self.db = DatabaseHandler()

    def close(self):
        """
        Close database connection.
        This method is required by Whisper components.
        """
        try:
            if self.db:
                self.db.close()
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")

    def store_transcription(self, speech_data: Dict) -> Tuple[bool, Optional[int]]:
        """
        Store Whisper transcription data in the database.
        
        Args:
            speech_data (Dict): Dictionary containing:
                - text: Transcribed text
                - filename: Original audio filename
                - file_type: Audio file extension
                - processed_at: ISO format timestamp
            
        Returns:
            Tuple[bool, Optional[int]]: (success status, record ID if successful)
        """
        try:
            if not self.db.connect():
                logger.error("Database connection failed during store_transcription")
                return False, None

            # Store transcription with pending evaluation status
            self.db.cursor.execute("""
                INSERT INTO voice_evaluations 
                (speech, evaluation, mark, created_at) 
                VALUES (%s::jsonb, %s::jsonb, %s, %s)
                RETURNING id;
                """, 
                (
                    Json(speech_data),              # Speech data as JSONB
                    Json({'status': 'pending'}),    # Initial evaluation status
                    0,                              # Initial mark
                    datetime.now()                  # Creation timestamp
                )
            )
            
            record_id = self.db.cursor.fetchone()
            
            if not record_id:
                logger.error("Failed to get inserted record ID")
                self.db.conn.rollback()
                return False, None

            self.db.conn.commit()
            logger.info(f"Successfully stored transcription with ID: {record_id[0]}")
            
            return True, record_id[0]

        except Exception as e:
            logger.error(f"Database operation failed in store_transcription: {str(e)}")
            if self.db.conn:
                self.db.conn.rollback()
            return False, None
        finally:
            self.db.close()

    def get_transcription(self, record_id: int) -> Optional[Dict]:
        """
        Retrieve transcription data by ID.
        
        Args:
            record_id (int): Database record ID
            
        Returns:
            Optional[Dict]: Speech data if found, including:
                - text: Transcribed text
                - filename: Original audio filename
                - file_type: Audio file extension
                - processed_at: Processing timestamp
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
        Retrieve all transcription records from the database.
        
        Returns:
            List[Dict]: List of transcription records, each containing:
                - id: Record ID
                - text: Transcribed text (from speech JSONB)
                - filename: Original audio filename
                - file_type: Audio file type
                - created_at: Timestamp of creation
        """
        try:
            if not self.db.connect():
                logger.error("Database connection failed during get_all_transcriptions")
                return []

            # Query all records, extracting fields from JSONB speech column
            self.db.cursor.execute("""
                SELECT 
                    id,
                    speech->>'text' as text,
                    speech->>'source_file' as filename,
                    speech->>'file_type' as file_type,
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
                    'text': record[1],
                    'filename': record[2],
                    'file_type': record[3],
                    'created_at': record[4]
                })
            
            logger.info(f"Retrieved {len(result)} transcription records")
            return result

        except Exception as e:
            logger.error(f"Failed to get transcriptions: {str(e)}")
            return []
        finally:
            self.db.close()

# Module execution check
if __name__ == "__main__":
    logger.info("Whisper database operations module loaded") 