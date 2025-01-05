import axios from 'axios';

// Define API URL with a default that matches your backend
const API_URL = 'http://127.0.0.1:8000';

/**
 * Format evaluation data to ensure all fields are strings
 * @param {Object} data - Raw evaluation data
 * @returns {Object} Formatted evaluation data
 */
const formatEvaluationData = (data) => {
  return {
    speech: {
      text: String(data.speech.text || ''),
      filename: String(data.speech.filename || ''),
      file_type: String(data.speech.file_type || ''),
      processed_at: String(data.speech.processed_at || '')
    },
    evaluation: {
      mark: Number(data.evaluation.mark || 0),
      text: String(data.evaluation.text || ''),
      status: String(data.evaluation.status || ''),
      evaluated_at: String(data.evaluation.evaluated_at || '')
    },
    mark: Number(data.mark || 0),
    created_at: String(data.created_at || '')
  };
};

/**
 * Get evaluation result for a specific record
 * @param {number} recordId - The ID of the record to evaluate
 * @returns {Promise<Object>} Evaluation data
 */
const getEvaluation = async (recordId) => {
  try {
    const response = await axios.get(`${API_URL}/evaluation/${recordId}`);
    return formatEvaluationData(response.data);
  } catch (error) {
    if (error.response?.status === 404) {
      throw new Error('Запису нема');
    }
    throw new Error(`Помилка отримання оцінки: ${error.message}`);
  }
};

export { getEvaluation }; 