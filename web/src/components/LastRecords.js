import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

function LastRecords() {
  const [evaluations, setEvaluations] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const itemsPerPage = 5;

  const fetchEvaluations = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_URL}/evaluations/`, {
        timeout: 10000,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        withCredentials: false
      });
      
      if (response.data) {
        console.log('Evaluations data received:', response.data);
        setEvaluations(response.data);
        setError(null);
      }
    } catch (err) {
      console.error('Evaluations error details:', {
        message: err.message,
        code: err.code,
        response: err.response
      });
      setError('Помилка завантаження записів');
      setEvaluations([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEvaluations();
    const interval = setInterval(fetchEvaluations, 60000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'status-completed';
      case 'processing': return 'status-processing';
      case 'error': return 'status-error';
      default: return '';
    }
  };

  const getMarkColor = (mark) => {
    if (!mark) return '';
    const numMark = Number(mark);
    if (numMark >= 5) return 'mark-good';
    return 'mark-poor';
  };

  if (error) return <div className="error-message">{error}</div>;
  if (isLoading) return <div className="loading">Завантаження записів...</div>;
  if (!evaluations || evaluations.length === 0) return null;

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = evaluations.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(evaluations.length / itemsPerPage);

  return (
    <section className="feature-section">
      <h2>📋 Останні записи</h2>
      <div className="evaluations-content">
        {currentItems.map((evaluation) => (
          <div key={evaluation.id} className="evaluation-item">
            <div className="evaluation-header">
              <div className="header-left">
                <strong>ID запису: {evaluation.id}</strong>
                <span className={`status ${getStatusColor(evaluation.status)}`}>
                  {evaluation.status === 'completed' ? 'Завершено' :
                   evaluation.status === 'processing' ? 'В обробці' :
                   evaluation.status === 'error' ? 'Помилка' : 'Обробка...'}
                </span>
              </div>
              <span className="date">
                {new Date(evaluation.created_at).toLocaleString('uk-UA')}
              </span>
            </div>
            
            <div className="evaluation-body">
              <div className="transcription">
                <strong>Транскрипція:</strong>
                <p>{evaluation.transcription || 'Очікується транскрипція...'}</p>
              </div>
              
              {evaluation.evaluation ? (
                <div className="evaluation-details">
                  <div className={`mark ${getMarkColor(evaluation.evaluation.mark)}`}>
                    <strong>Оцінка:</strong> {evaluation.evaluation.mark}
                  </div>
                  
                  <div className="evaluation-text">
                    <strong>Оцінка розмови:</strong>
                    <p>{evaluation.evaluation.text || 'Текст оцінки відсутній'}</p>
                  </div>

                  {evaluation.evaluation.comment && (
                    <div className="comment">
                      <strong>Коментар:</strong> {evaluation.evaluation.comment}
                    </div>
                  )}
                  
                  {evaluation.evaluation.summary && (
                    <div className="summary">
                      <strong>Підсумок:</strong>
                      <p>{evaluation.evaluation.summary}</p>
                    </div>
                  )}
                  
                  {evaluation.evaluation.marks && (
                    <div className="detailed-marks">
                      <strong>Детальні оцінки:</strong>
                      <ul>
                        {Object.entries(evaluation.evaluation.marks).map(([key, value]) => (
                          <li key={key}>
                            <span className="mark-label">{key}:</span>
                            <span className={`mark-value ${getMarkColor(value)}`}>{value}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {evaluation.evaluation.evaluated_at && (
                    <div className="evaluation-date">
                      <strong>Дата оцінки:</strong> {new Date(evaluation.evaluation.evaluated_at).toLocaleString('uk-UA')}
                    </div>
                  )}
                </div>
              ) : (
                <div className="evaluation-pending">
                  <p>Оцінка в процесі...</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button 
            className="pagination-button"
            onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
          >
            ←
          </button>
          {[...Array(totalPages)].map((_, i) => (
            <button
              key={i + 1}
              className={`pagination-button ${currentPage === i + 1 ? 'active' : ''}`}
              onClick={() => setCurrentPage(i + 1)}
            >
              {i + 1}
            </button>
          ))}
          <button 
            className="pagination-button"
            onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
          >
            →
          </button>
        </div>
      )}
    </section>
  );
}

export default LastRecords; 