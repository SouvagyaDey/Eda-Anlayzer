import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import { uploadCSV } from '../utils/api';
import { Sparkles, TrendingUp, BarChart2, PieChart } from 'lucide-react';
import './Home.css';

const Home = ({ darkMode }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleUpload = async (file) => {
    setIsUploading(true);
    setError(null);

    try {
      const theme = darkMode ? 'dark' : 'light';
      const response = await uploadCSV(file, theme);
      
      // Navigate to dashboard with session ID
      navigate(`/dashboard/${response.session.session_id}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload file. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="home-page">
      <div className="container">
        <div className="hero-section fade-in">
          <div className="hero-header">
            <Sparkles className="sparkle-icon" size={40} />
            <h1 className="hero-title">Master EDA: AI Agent for Charts & Insights</h1>
            <p className="hero-subtitle">
              Upload your CSV file and get instant AI-powered exploratory data analysis with 
              beautiful visualizations and actionable insights
            </p>
          </div>

          <div className="upload-section">
            <FileUpload onUpload={handleUpload} isUploading={isUploading} />
            
            {error && (
              <div className="error-message fade-in">
                <strong>Error:</strong> {error}
              </div>
            )}
          </div>
        </div>

        <div className="features-section">
          <h2 className="features-title">Powerful Features</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <BarChart2 size={32} />
              </div>
              <h3>Automatic Visualizations</h3>
              <p>
                Generate histograms, box plots, correlation heatmaps, pair plots, and more 
                automatically from your data
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <Sparkles size={32} />
              </div>
              <h3>AI-Powered Insights</h3>
              <p>
                Get intelligent analysis from Google Gemini 2.0 Flash that identifies patterns, 
                trends, and anomalies in your data
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <TrendingUp size={32} />
              </div>
              <h3>Statistical Analysis</h3>
              <p>
                Comprehensive statistical summaries including mean, median, standard deviation, 
                and outlier detection
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <PieChart size={32} />
              </div>
              <h3>Data Quality Checks</h3>
              <p>
                Automatic detection of missing values, duplicates, and data type inference 
                with cleaning suggestions
              </p>
            </div>
          </div>
        </div>

        <div className="how-it-works">
          <h2 className="section-title">How It Works</h2>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <h3>Upload CSV</h3>
              <p>Drag and drop or select your CSV file</p>
            </div>
            <div className="step-arrow">→</div>
            <div className="step">
              <div className="step-number">2</div>
              <h3>Auto Analysis</h3>
              <p>Charts and stats generated automatically</p>
            </div>
            <div className="step-arrow">→</div>
            <div className="step">
              <div className="step-number">3</div>
              <h3>AI Insights</h3>
              <p>Get intelligent recommendations from AI</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
