from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import tempfile
import os
import logging
from datetime import datetime
from app.db_operations_whisper import DatabaseOperations as WhisperDB
from app.db_operations_evaluation import DatabaseOperationsEvaluation as EvalDB
from app.fast_inference import evaluate_from_database
from app.whisper_transcribe import WhisperTranscriber
from app.data_retrieval import get_all_evaluations, get_evaluation_statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Voice Evaluation API",
    description="""
    API for voice transcription and evaluation system.
    
    ## Features
    * 🎤 Audio transcription using Whisper model
    * 📝 Evaluation of conversations
    * 📊 Statistics and analytics
    * 📋 Historical data retrieval
    
    ## Endpoints
    * `/transcribe/` - Upload and transcribe audio files
    * `/evaluation/{record_id}` - Get evaluation for specific record
    * `/evaluations/` - List all evaluations
    * `/statistics/` - Get evaluation statistics
    
    Features:
    * Upload audio files for transcription
    * Get transcription results
    * Get evaluation of transcribed text
    * Retrieve evaluation statistics
    * List all evaluations
    """,
    version="1.0.0",
    contact={
        "name": "Voice Evaluation API",
        "email": "psixvk@gmail.com",
    },
    license_info={
        "name": "Private License",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/transcribe/", response_model=Dict)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file (mp3, wav, m4a, ogg)")
):
    """
    Handle audio file upload and transcription.
    Uses WhisperDB for storing transcription results.
    """
    temp_path = None
    try:
        # Save uploaded file
        temp_path = await handle_file_upload(file)
        
        # Initialize transcriber and perform transcription
        transcriber = WhisperTranscriber()
        transcription = transcriber.process_audio(temp_path)
        
        if not transcription:
            raise HTTPException(status_code=500, detail="Transcription failed")
        
        # Store in database using WhisperDB
        db_ops = WhisperDB()
        success, record_id = db_ops.store_transcription({
            'text': transcription,
            'filename': file.filename,
            'file_type': os.path.splitext(file.filename)[1].lstrip('.'),
            'processed_at': datetime.now().isoformat()
        })

        if not success or record_id is None:
            raise HTTPException(status_code=500, detail="Failed to store transcription")

        return {
            'transcription': transcription,
            'evaluation_id': record_id
        }

    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

@app.post("/evaluate/{record_id}", response_model=Dict)
async def evaluate_speech(record_id: int):
    """
    Evaluate transcribed speech for given record ID.
    Uses EvalDB for storing evaluation results.
    """
    try:
        # Get evaluation result
        evaluation_result = evaluate_from_database(record_id)
        if not evaluation_result:
            raise HTTPException(
                status_code=500,
                detail="Evaluation failed"
            )

        # Prepare evaluation data
        evaluation_data = {
            'text': evaluation_result.get('evaluation', ''),
            'mark': evaluation_result.get('score', 0),
            'evaluated_at': datetime.now().isoformat()
        }

        # Store evaluation using EvalDB
        eval_db = EvalDB()
        success = eval_db.store_evaluation(record_id, evaluation_data)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to store evaluation results"
            )

        logger.info(f"Successfully evaluated record {record_id}")
        return evaluation_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/evaluation/{record_id}", response_model=Dict)
async def get_evaluation_result(record_id: int):
    """
    Retrieve or create evaluation results for given record ID.
    If status is 'pending', triggers new evaluation.
    
    Args:
        record_id: ID of the record to evaluate
        
    Returns:
        Dict: Evaluation results
    """
    try:
        # Get existing evaluation
        eval_db = EvalDB()
        result = eval_db.get_evaluation(record_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Record not found for ID: {record_id}"
            )

        # Check if evaluation is pending
        evaluation_data = result.get('evaluation', {})
        if isinstance(evaluation_data, dict) and evaluation_data.get('status') == 'pending':
            logger.info(f"Found pending evaluation for record {record_id}, triggering evaluation")
            
            # Perform evaluation
            evaluation_result = evaluate_from_database(record_id)
            if not evaluation_result:
                raise HTTPException(
                    status_code=500,
                    detail="Evaluation failed"
                )

            # Store evaluation results
            evaluation_data = {
                'text': evaluation_result.get('evaluation', ''),
                'mark': evaluation_result.get('score', 0),
                'evaluated_at': datetime.now().isoformat(),
                'status': 'completed'
            }

            # Update database with evaluation results
            success = eval_db.store_evaluation(record_id, evaluation_data)
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to store evaluation results"
                )

            # Get updated result
            result = eval_db.get_evaluation(record_id)
            
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_file_upload(file: UploadFile) -> str:
    """Helper function to handle file upload and validation"""
    # Validate file extension
    allowed_extensions = {'mp3', 'wav', 'm4a', 'ogg'}
    file_ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {', '.join(allowed_extensions)}"
        )

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_file:
        content = await file.read()
        temp_file.write(content)
        return temp_file.name

@app.get("/speech/{record_id}", response_model=Dict)
async def get_speech_data(record_id: int):
    """Get speech transcription data"""
    db_ops = WhisperDB()
    result = db_ops.get_transcription(record_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Speech record not found")
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/evaluations/", response_model=List[Dict])
async def list_evaluations():
    """Get all evaluations with their transcriptions"""
    return get_all_evaluations()

@app.get("/statistics/", response_model=Dict)
async def get_statistics():
    """Get evaluation statistics"""
    return get_evaluation_statistics()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1
    ) 