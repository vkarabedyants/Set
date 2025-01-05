import React, { useState } from 'react';
import { getEvaluation } from '../services/evaluationService';
import EvaluationDisplay from './EvaluationDisplay';

function QualityEvaluation() {
  const [recordId, setRecordId] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleEvaluation = async () => {
    if (!recordId) {
      setError('Будь ласка, введіть ID запису');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const evaluationData = await getEvaluation(recordId);
      if (evaluationData) {
        setResult(evaluationData);
        setError(null);
      }
    } catch (err) {
      console.error('Evaluation error:', err);
      setError(err.message);
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="quality-evaluation-page">
      <h2>Оцінка якості розмови</h2>
      <div className="evaluation-description">
        Введіть ID запису для отримання оцінки
      </div>
      <div className="evaluation-input-group">
        <input
          type="number"
          value={recordId}
          onChange={(e) => setRecordId(e.target.value)}
          placeholder="Введіть ID запису"
          min="1"
        />
        <button 
          onClick={handleEvaluation}
          disabled={!recordId || isLoading}
        >
          {isLoading ? 'Завантаження...' : 'Отримати'}
        </button>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {result && (
        <div className="result-section">
          <EvaluationDisplay data={result} />
        </div>
      )}
    </div>
  );
}

export default QualityEvaluation; 