import React, { useState } from 'react';
import EvaluationDisplay from './components/EvaluationDisplay';
import QualityEvaluation from './components/QualityEvaluation';
import AudioUpload from './components/AudioUpload';
import Statistics from './components/Statistics';
import LastRecords from './components/LastRecords';
import logo from './images/logo_mdm.jpg';
import './App.css';

function App() {
  const [showQualityEvaluation, setShowQualityEvaluation] = useState(false);
  const [showAudioUpload, setShowAudioUpload] = useState(false);

  // Function to handle successful file upload
  const handleUploadSuccess = (data) => {
    console.log('Upload successful:', data);
    setShowAudioUpload(false); // Return to main page after successful upload
  };

  const handleBack = () => {
    setShowQualityEvaluation(false);
    setShowAudioUpload(false);
  };

  if (showAudioUpload) {
    return (
      <div className="App">
        <header className="App-header">
          <div className="header-content">
            <img src={logo} alt="MDM Logo" className="mdm-logo" />
            <h1>Система оцінювання</h1>
          </div>
        </header>
        <div className="evaluation-page">
          <button 
            className="back-button"
            onClick={handleBack}
          >
            ← Назад
          </button>
          <AudioUpload onUploadSuccess={handleUploadSuccess} />
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <img src={logo} alt="MDM Logo" className="mdm-logo" />
          <h1>Система оцінювання дзвінків. Оцінка здійснюється за шкалою від 1 до 10 </h1>
        </div>
      </header>

      {!showQualityEvaluation ? (
        <div className="main-content">
          {/* Audio Upload Button */}
          <section className="feature-section">
            <h2>🎤 Завантаження аудіо</h2>
            <p>Завантажити новий аудіо файл для оцінки</p>
            <button 
              className="upload-button"
              onClick={() => setShowAudioUpload(true)}
            >
              Завантажити аудіо
            </button>
          </section>

          {/* Quality Evaluation Button */}
          <section className="feature-section">
            <h2>📝 Оцінка якості</h2>
            <p>Отримати оцінку якості розмови за ID запису</p>
            <button 
              className="quality-evaluation-button"
              onClick={() => setShowQualityEvaluation(true)}
            >
              Оцінка якості розмови
            </button>
          </section>

          {/* Statistics Section */}
          <Statistics />

          {/* Last Records Section with Pagination */}
          <LastRecords />

          {/* Evaluation Display Section */}
          <EvaluationDisplay />
        </div>
      ) : (
        <div className="evaluation-page">
          <button 
            className="back-button"
            onClick={handleBack}
          >
            ← Назад
          </button>
          <QualityEvaluation />
        </div>
      )}
    </div>
  );
}

export default App;