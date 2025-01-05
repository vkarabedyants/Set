import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

const EvaluationDisplay = ({ data }) => {
  const [evaluations, setEvaluations] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Function to fetch evaluations from the API
  const fetchEvaluations = async () => {
    try {
      const response = await axios.get(`${API_URL}/evaluations/`);
      console.log('Evaluations fetched:', response.data);
      setEvaluations(response.data);
    } catch (err) {
      console.error('Error fetching evaluations:', err);
      setError('Помилка завантаження оцінок');
    }
  };

  // Function to fetch statistics from the API
  const fetchStatistics = async () => {
    try {
      const response = await axios.get(`${API_URL}/statistics/`);
      console.log('Statistics fetched:', response.data);
      setStatistics(response.data);
    } catch (err) {
      console.error('Error fetching statistics:', err);
      setError('Помилка завантаження статистики');
    }
  };

  // Initial data fetch on component mount
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      await Promise.all([fetchEvaluations(), fetchStatistics()]);
      setIsLoading(false);
    };
    fetchData();
  }, []);

  if (isLoading) return <div className="loading">Завантаження...</div>;
  if (error) return <div className="error-message">{error}</div>;
  if (!data) return null;

  return (
    <div className="evaluation-content">
      {data.speech && (
        <>
          <div className="result-item">
            <strong>Текст розмови:</strong>
            <div className="text-content">{data.speech.text}</div>
          </div>
          <div className="result-item">
            <strong>Тип файлу:</strong> {data.speech.file_type}
          </div>
          <div className="result-item">
            <strong>Оброблено:</strong> {new Date(data.speech.processed_at).toLocaleString('uk-UA')}
          </div>
        </>
      )}
      
      {data.evaluation && (
        <>
          <div className="result-item">
            <strong>Оцінка:</strong> {data.evaluation.mark}
          </div>
          <div className="result-item">
            <strong>Коментар:</strong> {data.evaluation.text}
          </div>
          <div className="result-item">
            <strong>Статус:</strong> {data.evaluation.status === 'completed' ? 'Завершено' : 'В обробці'}
          </div>
          <div className="result-item">
            <strong>Оцінено:</strong> {new Date(data.evaluation.evaluated_at).toLocaleString('uk-UA')}
          </div>
        </>
      )}

      {/* Statistics Section */}
      {statistics && (
        <div className="statistics-section">
          <h3>Статистика</h3>
          <div className="statistics-content">
            <div className="stat-item">
              <strong>Всього записів:</strong> {statistics.total_records}
            </div>
            <div className="stat-item">
              <strong>Оцінено:</strong> {statistics.evaluated_records}
            </div>
            <div className="stat-item">
              <strong>Середня оцінка:</strong> {statistics.average_mark?.toFixed(2)}
            </div>
          </div>
        </div>
      )}

      {/* Evaluations Summary */}
      {evaluations && evaluations.length > 0 && (
        <div className="evaluations-summary">
          <h3>Останні оцінки</h3>
          <div className="evaluations-list">
            {evaluations.slice(0, 5).map((evaluation, index) => (
              <div key={index} className="evaluation-summary-item">
                <strong>ID {evaluation.id}:</strong> {evaluation.evaluation?.mark || 'В обробці'}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="result-item">
        <strong>Загальна оцінка:</strong> {data.mark}
      </div>
      
      {data.created_at && (
        <div className="result-item">
          <strong>Створено:</strong> {new Date(data.created_at).toLocaleString('uk-UA')}
        </div>
      )}
    </div>
  );
};

export default EvaluationDisplay; 