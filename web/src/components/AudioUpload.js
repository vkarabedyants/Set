import React, { useState } from 'react';
import axios from 'axios';

// API endpoint for file upload
const API_URL = 'http://127.0.0.1:8000';
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB in bytes

function AudioUpload() {
  // State management for component
  const [file, setFile] = useState(null);          // Selected file
  const [isLoading, setIsLoading] = useState(false); // Loading state during upload
  const [error, setError] = useState(null);        // Error messages
  const [success, setSuccess] = useState(null);     // Success messages
  const [dragOver, setDragOver] = useState(false); // Drag and drop visual feedback
  const [uploadResult, setUploadResult] = useState(null);

  /**
   * Validate file size before upload
   * @param {File} file - File to validate
   * @returns {boolean} - True if file size is valid, false otherwise
   */
  const validateFileSize = (file) => {
    if (file.size > MAX_FILE_SIZE) {
      setError(`Файл занадто великий. Максимальний розмір: 50MB. Розмір вашого файлу: ${(file.size / (1024 * 1024)).toFixed(2)}MB`);
      return false;
    }
    return true;
  };

  /**
   * Handle file selection from input
   * @param {Event} event - File input change event
   */
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      if (validateFileSize(selectedFile)) {
        validateAndSetFile(selectedFile);
      } else {
        setFile(null);
      }
    }
  };

  /**
   * Validate file type and set file state
   * @param {File} selectedFile - File to validate
   */
  const validateAndSetFile = (selectedFile) => {
    // List of accepted audio file types
    const validTypes = ['audio/mp3', 'audio/wav', 'audio/m4a', 'audio/ogg'];
    
    if (validTypes.includes(selectedFile.type)) {
      setFile(selectedFile);
      setError(null);
      setSuccess(null);
      setUploadResult(null);
    } else {
      setError('Будь ласка, виберіть аудіо файл (MP3, WAV, M4A, або OGG)');
      setFile(null);
    }
  };

  /**
   * Handle dragover event for drag and drop
   * @param {DragEvent} e - Drag event
   */
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true); // Visual feedback when file is dragged over
  };

  /**
   * Handle drag leave event
   * @param {DragEvent} e - Drag event
   */
  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false); // Remove visual feedback
  };

  /**
   * Handle file drop event
   * @param {DragEvent} e - Drop event
   */
  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (validateFileSize(droppedFile)) {
        validateAndSetFile(droppedFile);
      }
    }
  };

  /**
   * Handle file upload to server
   * Makes POST request to /transcribe/ endpoint
   */
  const handleUpload = async () => {
    if (!file) {
      setError('Будь ласка, виберіть файл');
      return;
    }

    if (!validateFileSize(file)) {
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/transcribe/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        validateStatus: function (status) {
          return status >= 200 && status < 500;
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log('Upload progress:', percentCompleted);
        }
      });

      if (response.status === 200) {
        console.log('Upload successful:', response.data);
        setSuccess('Файл успішно завантажено та оброблено');
        setUploadResult(response.data);
        setFile(null);
      } else {
        handleError(response);
      }
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleError = (error) => {
    if (error.code === 'ECONNABORTED') {
      setError('Час очікування минув. Спробуйте ще раз.');
    } else if (error.response?.status === 500) {
      setError('Помилка сервера. Спробуйте пізніше.');
    } else if (error.response?.status === 413) {
      setError('Файл занадто великий. Максимальний розмір: 50MB');
    } else if (error.response?.status === 415) {
      setError('Непідтримуваний формат файлу');
    } else {
      setError('Помилка завантаження: ' + (error.response?.data?.detail || 'Невідома помилка'));
    }
  };

  return (
    <section className="feature-section">
      <h2>🎤 Завантаження аудіо</h2>
      {!uploadResult ? (
        <>
          <div 
            className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="upload-content">
              <div className="upload-icon">🎵</div>
              <p>Перетягніть аудіо файл сюди або</p>
              <label className="file-input-label">
                Виберіть файл
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept="audio/mp3,audio/wav,audio/m4a,audio/ogg"
                  className="file-input"
                />
              </label>
              <p className="file-types">
                Підтримувані формати: MP3, WAV, M4A, OGG
                <br />
                <small>Максимальний розмір файлу: 50MB</small>
              </p>
            </div>
          </div>

          {file && (
            <div className="selected-file">
              <span>Вибрано: {file.name} ({(file.size / (1024 * 1024)).toFixed(2)}MB)</span>
              <button 
                className="upload-button"
                onClick={handleUpload}
                disabled={isLoading}
              >
                {isLoading ? 'Завантаження...' : 'Завантажити та обробити'}
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="upload-result">
          <div className="result-header">
            <h3>Інформація про запис</h3>
          </div>
          <div className="result-content">
            <div className="result-item">
              <strong>ID запису:</strong> {uploadResult.id}
            </div>
            <div className="result-item">
              <strong>Статус:</strong> {uploadResult.status || 'В обробці'}
            </div>
            {uploadResult.text && (
              <div className="result-item">
                <strong>Транскрипція:</strong>
                <p>{uploadResult.text}</p>
              </div>
            )}
            <button 
              className="upload-button"
              onClick={() => {
                setUploadResult(null);
                setFile(null);
                setSuccess(null);
                setError(null);
              }}
            >
              Завантажити та обробити ще один файл
            </button>
          </div>
        </div>
      )}

      {success && <div className="success-message">{success}</div>}
      {error && <div className="error-message">{error}</div>}
    </section>
  );
}

export default AudioUpload; 