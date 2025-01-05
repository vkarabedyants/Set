import psycopg2
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """
    Initialize database and create required tables.
    For Windows environment with PostgreSQL running in Docker container.
    
    Steps:
    1. Connect to default postgres database
    2. Create voice database if not exists
    3. Create tables with JSONB type (built-in PostgreSQL type)
    4. Create necessary indexes for performance
    """
    
    # Connection parameters for Docker container
    initial_conn_params = {
        'user': 'myadmin1',
        'password': 'P@ssw0rd!!!',
        'host': 'localhost',  # Docker container host
        'port': '5432',      # Exposed Docker port
        'dbname': 'postgres' # Default database
    }

    # Connection parameters for voice database
    voice_conn_params = {
        'user': 'myadmin1',
        'password': 'P@ssw0rd!!!',
        'host': 'localhost',
        'port': '5432',
        'dbname': 'voice'
    }

    try:
        # Step 1: Connect to default postgres database
        logger.info("Connecting to PostgreSQL container...")
        conn = psycopg2.connect(**initial_conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Step 2: Create voice database if it doesn't exist
        logger.info("Checking if 'voice' database exists...")
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'voice'")
        if not cursor.fetchone():
            logger.info("Creating 'voice' database...")
            cursor.execute("CREATE DATABASE voice")
            logger.info("Database 'voice' created successfully")
        else:
            logger.info("Database 'voice' already exists")

        # Close initial connection
        cursor.close()
        conn.close()

        # Step 3: Connect to voice database
        logger.info("Connecting to 'voice' database...")
        conn = psycopg2.connect(**voice_conn_params)
        cursor = conn.cursor()

        # Step 4: Create voice_evaluations table with JSONB type
        logger.info("Creating voice_evaluations table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_evaluations (
                id SERIAL PRIMARY KEY,                    -- Auto-incrementing primary key
                speech JSONB NOT NULL,                    -- Speech data in JSONB format
                evaluation JSONB NOT NULL,                -- Evaluation data in JSONB format
                mark INTEGER NOT NULL                     -- Evaluation score
                    CHECK (mark >= 0 AND mark <= 10),    -- Score range constraint
                created_at TIMESTAMP WITH TIME ZONE       -- Creation timestamp
                    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Step 5: Create indexes for better query performance
        logger.info("Creating performance indexes...")
        cursor.execute("""
            -- Index for searching by mark
            CREATE INDEX IF NOT EXISTS idx_voice_eval_mark 
            ON voice_evaluations(mark);
            
            -- Index for timestamp-based queries
            CREATE INDEX IF NOT EXISTS idx_voice_eval_created 
            ON voice_evaluations(created_at);
            
            -- GIN index for efficient JSONB searches on speech data
            CREATE INDEX IF NOT EXISTS idx_voice_eval_speech 
            ON voice_evaluations USING GIN (speech jsonb_path_ops);
            
            -- GIN index for efficient JSONB searches on evaluation data
            CREATE INDEX IF NOT EXISTS idx_voice_eval_evaluation 
            ON voice_evaluations USING GIN (evaluation jsonb_path_ops);
        """)

        # Commit all changes
        conn.commit()
        logger.info("Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        # Clean up connections
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        logger.info("Database connections closed")

if __name__ == "__main__":
    logger.info("Starting database initialization for Docker environment...")
    init_database()
    logger.info("Database initialization script completed") 