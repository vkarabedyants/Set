import psycopg2
from psycopg2.extras import Json
import logging
from typing import Optional, Dict, Tuple
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseHandler:
    """Database connection and basic operations handler"""
    
    def __init__(self):
        """Initialize database connection parameters"""
        self.conn = None
        self.cursor = None
        self.db_params = {
            'dbname': os.getenv('DB_NAME', 'voice'),
            'user': os.getenv('DB_USER', 'myadmin1'),
            'password': os.getenv('DB_PASSWORD', 'P@ssw0rd!!!'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }
        logger.info("Database handler initialized with updated connection parameters")

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.cursor = self.conn.cursor()
            logger.info("Successfully connected to PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False

    def get_transcription(self, record_id: int) -> Optional[Dict]:
        """
        Retrieve transcription by ID from database.
        
        Args:
            record_id: Database record ID
            
        Returns:
            Optional[Dict]: Transcription data if found
        """
        try:
            self.cursor.execute("""
                SELECT speech 
                FROM voice_evaluations 
                WHERE id = %s
            """, (record_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get transcription: {str(e)}")
            return None

    def get_evaluation(self, record_id: int) -> Optional[Dict]:
        """
        Retrieve evaluation by ID from database.
        
        Args:
            record_id: Database record ID
            
        Returns:
            Optional[Dict]: Evaluation data and mark if found
        """
        try:
            self.cursor.execute("""
                SELECT evaluation, mark 
                FROM voice_evaluations 
                WHERE id = %s
            """, (record_id,))
            result = self.cursor.fetchone()
            if result:
                return {
                    'evaluation': result[0],
                    'mark': result[1]
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get evaluation: {str(e)}")
            return None

    def store_transcription(self, speech_data: Dict) -> Tuple[bool, Optional[int]]:
        """
        Store new transcription in database.
        
        Args:
            speech_data: Dictionary with transcription data
            
        Returns:
            Tuple[bool, Optional[int]]: Success status and record ID
        """
        try:
            self.cursor.execute("""
                INSERT INTO voice_evaluations 
                (speech, evaluation, mark, created_at) 
                VALUES (%s::jsonb, %s::jsonb, %s, %s)
                RETURNING id;
                """, 
                (
                    Json(speech_data),
                    Json({'status': 'pending'}),
                    0,
                    datetime.now()
                )
            )
            record_id = self.cursor.fetchone()
            self.conn.commit()
            return True, record_id[0] if record_id else None
        except Exception as e:
            logger.error(f"Failed to store transcription: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False, None

    def store_evaluation(self, record_id: int, evaluation_data: Dict) -> bool:
        """
        Update existing record with evaluation data.
        
        Args:
            record_id: Database record ID
            evaluation_data: Dictionary with evaluation and mark
            
        Returns:
            bool: Success status
        """
        try:
            self.cursor.execute("""
                UPDATE voice_evaluations 
                SET evaluation = %s::jsonb,
                    mark = %s
                WHERE id = %s
                """, 
                (
                    Json(evaluation_data),
                    evaluation_data.get('mark', 0),
                    record_id
                )
            )
            if self.cursor.rowcount == 0:
                self.conn.rollback()
                return False
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store evaluation: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False

    def close(self):
        """Close database connection and cursor"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}") 