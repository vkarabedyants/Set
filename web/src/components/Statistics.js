import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

function Statistics() {
  const [statistics, setStatistics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchStatistics = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_URL}/statistics/`, {
        timeout: 10000, // Increased to 10 seconds
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        withCredentials: false // Added for CORS
      });
      
      if (response.data) {
        console.log('Statistics data received:', response.data);
        setStatistics(response.data);
        setError(null);
      }
    } catch (err) {
      console.error('Statistics error details:', {
        message: err.message,
        code: err.code,
        response: err.response
      });
      setError('Помилка завантаження статистики');
      setStatistics(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatistics();
    // Refresh every minute instead of 30 seconds
    const interval = setInterval(fetchStatistics, 60000);
    return () => clearInterval(interval);
  }, []);

  if (error) return <div className="error-message">{error}</div>;
  if (isLoading) return <div className="loading">Завантаження статистики...</div>;
  if (!statistics) return null;

  return (
    <section className="feature-section">
      <h2>📊 Статистика</h2>
      <div className="statistics-content">
        <div className="statistic-item">
          <strong>Всього записів:</strong>
          <span>{statistics.total_records}</span>
        </div>
        <div className="statistic-item">
          <strong>Оцінено записів:</strong>
          <span>{statistics.evaluated_records}</span>
        </div>
        <div className="statistic-item">
          <strong>Очікують оцінки:</strong>
          <span>{statistics.pending_evaluations}</span>
        </div>
        <div className="statistic-item">
          <strong>Середня оцінка:</strong>
          <span>{statistics.average_mark?.toFixed(2)}</span>
        </div>
        {statistics.marks_distribution && (
          <div className="statistic-item marks-distribution">
            <strong>Розподіл оцінок:</strong>
            <div className="marks-grid">
              {Object.entries(statistics.marks_distribution).map(([mark, count]) => (
                <div key={mark} className="mark-item">
                  <span className="mark">{mark}:</span>
                  <span className="count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

export default Statistics; 