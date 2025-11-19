import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getSessionDetail, getAiInsights, getColumnInfo, generateOnDemandCharts } from '../utils/api';
import { Sparkles, ArrowLeft, Table, BarChart, Download, ChevronRight, Loader, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import './Dashboard.css';

const Dashboard = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('charts');
  const [selectedChart, setSelectedChart] = useState(null);
  const [columnInfo, setColumnInfo] = useState(null);
  
  // On-demand chart generation states
  const [xAxis, setXAxis] = useState('');
  const [yAxis, setYAxis] = useState('');
  const [generating, setGenerating] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [successMessage, setSuccessMessage] = useState(null);
  const [availablePlots, setAvailablePlots] = useState([]);
  const [selectedPlots, setSelectedPlots] = useState([]);

  useEffect(() => {
    loadSessionData();
  }, [sessionId]);

  useEffect(() => {
    // Auto-select first chart when charts are loaded
    if (session?.charts && session.charts.length > 0 && !selectedChart) {
      setSelectedChart(session.charts[0]);
    }
  }, [session]);

  const loadSessionData = async () => {
    try {
      setLoading(true);
      const data = await getSessionDetail(sessionId);
      setSession(data);
      
      // Load column info
      try {
        const colInfo = await getColumnInfo(sessionId);
        setColumnInfo(colInfo);
      } catch (colErr) {
        console.warn('Could not load column info:', colErr);
      }
      
      // Load insights if they exist
      if (data.insights) {
        setInsights(data.insights);
      }
    } catch (err) {
      setError('Failed to load session data');
      console.error('Error loading session:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateInsights = async () => {
    try {
      setInsightsLoading(true);
      const data = await getAiInsights(sessionId);
      setInsights(data.insights);
      setActiveTab('insights');
    } catch (err) {
      setError('Failed to generate insights');
      console.error('Error generating insights:', err);
    } finally {
      setInsightsLoading(false);
    }
  };

  // Determine available plot types based on X and Y axis selection
  const updateAvailablePlots = (x, y) => {
    if (!x && !y) {
      setAvailablePlots([]);
      setSelectedPlots([]);
      return;
    }

    const xCol = columnInfo?.columns.find(c => c.name === x);
    const yCol = columnInfo?.columns.find(c => c.name === y);
    
    const xIsNumeric = xCol?.type === 'numeric';
    const yIsNumeric = yCol?.type === 'numeric';
    const xIsCategorical = xCol?.type === 'categorical';
    const yIsCategorical = yCol?.type === 'categorical';

    let plots = [];

    if (x && y) {
      // Both axes selected
      if (xIsNumeric && yIsNumeric) {
        // Numeric x Numeric: scatter, histogram (for both), distribution (for both)
        plots = [
          { id: 'scatter', name: '📈 Scatter Plot' },
          { id: 'histogram', name: '📊 Histogram' },
          { id: 'distribution', name: '📉 Distribution' }
        ];
      } else if (xIsCategorical && yIsNumeric) {
        // Categorical x Numeric: box plot, histogram (for y), distribution (for y)
        plots = [
          { id: 'box', name: '📦 Box Plot' },
          { id: 'histogram', name: '📊 Histogram' },
          { id: 'distribution', name: '📉 Distribution' }
        ];
      } else if (xIsNumeric && yIsCategorical) {
        // Numeric x Categorical: box plot, histogram (for x), distribution (for x)
        plots = [
          { id: 'box', name: '📦 Box Plot' },
          { id: 'histogram', name: '📊 Histogram' },
          { id: 'distribution', name: '� Distribution' }
        ];
      } else if (xIsCategorical && yIsCategorical) {
        // Categorical x Categorical: grouped bar only
        plots = [
          { id: 'grouped_bar', name: '📊 Grouped Bar' }
        ];
      }
    } else if (x || y) {
      // Single axis selected
      const col = xCol || yCol;
      if (col?.type === 'numeric') {
        // Single numeric: histogram, distribution
        plots = [
          { id: 'histogram', name: '📊 Histogram' },
          { id: 'distribution', name: '📉 Distribution' }
        ];
      } else if (col?.type === 'categorical') {
        // Single categorical: bar chart only
        plots = [
          { id: 'bar', name: '📊 Bar Chart' }
        ];
      }
    }

    setAvailablePlots(plots);
    setSelectedPlots(plots.map(p => p.id)); // Auto-select all available plots
  };

  const handleXAxisChange = (value) => {
    setXAxis(value);
    updateAvailablePlots(value, yAxis);
  };

  const handleYAxisChange = (value) => {
    setYAxis(value);
    updateAvailablePlots(xAxis, value);
  };

  const handlePlotToggle = (plotType) => {
    setSelectedPlots(prev => 
      prev.includes(plotType) 
        ? prev.filter(p => p !== plotType)
        : [...prev, plotType]
    );
  };

  useEffect(() => {
    // Initialize available plots when component mounts
    if (columnInfo) {
      updateAvailablePlots(xAxis, yAxis);
    }
  }, [columnInfo]);

  const handleGenerateCharts = async () => {
    if (!xAxis && !yAxis) {
      alert('Please select at least one axis (X or Y)');
      return;
    }

    if (selectedPlots.length === 0) {
      setError('Please select at least one plot type');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      setSuccessMessage(null);
      
      const result = await generateOnDemandCharts(
        sessionId,
        xAxis || null,
        yAxis || null,
        selectedPlots, // Pass selected plot types
        theme
      );

      if (result.charts_generated === false && result.message) {
        // All charts already exist
        setSuccessMessage(`📚 ${result.message} Check the Generated Charts section below.`);
        setTimeout(() => setSuccessMessage(null), 5000);
        return;
      }

      if (result.charts_generated && result.charts.length > 0) {
        // Reload session to get updated charts list
        await loadSessionData();
        
        setActiveTab('charts');
        
        // Show appropriate message based on what was generated
        if (result.newly_generated === 0) {
          setSuccessMessage('📚 These plots are already in your library!');
        } else if (result.message) {
          setSuccessMessage(`✓ ${result.message}`);
        } else {
          setSuccessMessage(`✓ Generated ${result.charts.length} chart(s): ${selectedPlots.join(', ')}`);
        }
        
        // Auto-hide success message after 5 seconds
        setTimeout(() => setSuccessMessage(null), 5000);
      } else {
        setError('No charts were generated. Try different axis selections.');
      }
    } catch (err) {
      setError('Failed to generate charts: ' + (err.response?.data?.error || err.message));
      console.error('Error generating charts:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteChart = async (chartId) => {
    if (!confirm('Are you sure you want to delete this chart?')) {
      return;
    }

    try {
      // Call delete API (you'll need to add this endpoint)
      // For now, we'll just reload and filter it out locally
      const updatedCharts = session.charts.filter(c => c.id !== chartId);
      setSession({ ...session, charts: updatedCharts });
      
      if (selectedChart?.id === chartId) {
        setSelectedChart(updatedCharts[0] || null);
      }
      
      setSuccessMessage('✓ Chart deleted successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to delete chart: ' + err.message);
      console.error('Error deleting chart:', err);
    }
  };

  const handleDownloadChart = async (chart) => {
    try {
      const chartUrl = getChartUrl(chart);
      const response = await fetch(chartUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${chart.chart_type}_${chart.column_name || 'chart'}.png`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error downloading chart:', err);
      setError('Failed to download chart');
    }
  };

  // Helper to get chart URL from path
  const getChartUrl = (chart) => {
    if (chart.chart_url) return chart.chart_url;
    if (chart.chart_path) {
      // chart_path format: "eda_outputs/session-id/chart.png"
      return `http://localhost:8000/${chart.chart_path}`;
    }
    return '';
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p className="loading-text">Loading EDA results...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate('/')} className="btn btn-primary">
          <ArrowLeft size={20} />
          Back to Home
        </button>
      </div>
    );
  }

  if (!session) {
    return null;
  }

  return (
    <div className="dashboard-page">
      <div className="container-fluid">
        {/* Header */}
        <div className="dashboard-header">
          <button onClick={() => navigate('/')} className="back-btn">
            <ArrowLeft size={20} />
            Back
          </button>
          <div className="header-info">
            <h1 className="dashboard-title">{session.filename}</h1>
            <div className="dataset-stats">
              <div className="stat">
                <Table size={18} />
                <span>{session.row_count} rows</span>
              </div>
              <div className="stat">
                <BarChart size={18} />
                <span>{session.column_count} columns</span>
              </div>
              <div className="stat">
                <span>📊 {session.charts?.length || 0} charts</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content with Sidebar */}
        <div className="dashboard-layout">
          {/* Sidebar */}
          <div className="sidebar">
            {/* Chart Generator Section */}
            {columnInfo && (
              <div className="sidebar-generator">
                <h3 className="generator-title">📊 Generate Charts</h3>
                <div className="generator-controls-vertical">
                  <div className="axis-selector">
                    <label htmlFor="x-axis-select">X-Axis:</label>
                    <select
                      id="x-axis-select"
                      value={xAxis}
                      onChange={(e) => handleXAxisChange(e.target.value)}
                      className="axis-select"
                      disabled={generating}
                    >
                      <option value="">-- None --</option>
                      {columnInfo.columns.map((col) => (
                        <option key={col.name} value={col.name}>
                          {col.name} ({col.type})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="axis-selector">
                    <label htmlFor="y-axis-select">Y-Axis:</label>
                    <select
                      id="y-axis-select"
                      value={yAxis}
                      onChange={(e) => handleYAxisChange(e.target.value)}
                      className="axis-select"
                      disabled={generating}
                    >
                      <option value="">-- None --</option>
                      {columnInfo.columns.map((col) => (
                        <option key={col.name} value={col.name}>
                          {col.name} ({col.type})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Available Plot Types */}
                  {availablePlots.length > 0 && (
                    <div className="plot-type-selector">
                      <label className="plot-selector-label">Available Plots:</label>
                      <div className="plot-checkboxes">
                        {availablePlots.map(plot => (
                          <label 
                            key={plot.id} 
                            className="plot-checkbox-label"
                          >
                            <input
                              type="checkbox"
                              checked={selectedPlots.includes(plot.id)}
                              onChange={() => handlePlotToggle(plot.id)}
                              disabled={generating}
                            />
                            <span className="plot-type-name">
                              {plot.name}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  <button
                    onClick={handleGenerateCharts}
                    className="btn btn-primary generate-btn-vertical"
                    disabled={generating || (!xAxis && !yAxis)}
                  >
                    {generating ? (
                      <>
                        <Loader size={18} className="spinner" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <BarChart size={18} />
                        Generate
                      </>
                    )}
                  </button>
                  
                  {error && (
                    <div className="generator-error-small">
                      ⚠️ {error}
                    </div>
                  )}
                  
                  {successMessage && (
                    <div className="generator-success-small">
                      {successMessage}
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="sidebar-divider"></div>
            
            <div className="sidebar-section">
              <button
                className={`sidebar-item ${activeTab === 'insights' ? 'active' : ''}`}
                onClick={() => {
                  if (insights) {
                    setActiveTab('insights');
                  } else {
                    handleGenerateInsights();
                  }
                }}
                disabled={insightsLoading}
              >
                <Sparkles size={20} />
                <span>AI Insights</span>
                {insightsLoading && <div className="spinner-tiny"></div>}
              </button>
            </div>

            <div className="sidebar-divider"></div>

            <div className="sidebar-section">
              <div className="sidebar-section-header-static">
                <BarChart size={16} />
                <span className="sidebar-section-title">Generated Charts</span>
                <span className="sidebar-section-count">{session.charts?.length || 0}</span>
              </div>
              
              <div className="sidebar-section-content">
                {session.charts && session.charts.length > 0 ? (
                  session.charts.map((chart) => (
                    <button
                      key={chart.id}
                      className={`sidebar-item ${activeTab === 'charts' && selectedChart?.id === chart.id ? 'active' : ''}`}
                      onClick={() => {
                        setActiveTab('charts');
                        setSelectedChart(chart);
                      }}
                    >
                      <BarChart size={18} />
                      <span className="sidebar-item-text">
                        {formatChartTitle(chart.chart_type, chart.column_name)}
                      </span>
                      <ChevronRight size={16} className="sidebar-item-arrow" />
                    </button>
                  ))
                ) : (
                  <div className="sidebar-empty">
                    <p>No charts generated yet</p>
                    <p style={{ fontSize: '12px', marginTop: '8px', opacity: 0.7 }}>
                      Use the generator above to create charts
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="main-content">
            {activeTab === 'charts' && selectedChart && (
              <div className="chart-view fade-in">
                <div className="chart-view-header">
                  <h2>{formatChartTitle(selectedChart.chart_type, selectedChart.column_name)}</h2>
                  <div className="chart-actions">
                    <button
                      onClick={() => handleDeleteChart(selectedChart.id)}
                      className="btn btn-danger"
                      title="Delete Chart"
                    >
                      <Trash2 size={18} />
                      Delete
                    </button>
                    <button
                      onClick={() => handleDownloadChart(selectedChart)}
                      className="btn btn-secondary"
                      title="Download Chart"
                    >
                      <Download size={18} />
                      Download
                    </button>
                  </div>
                </div>
                <div className="chart-view-body">
                  <img
                    src={getChartUrl(selectedChart)}
                    alt={selectedChart.chart_type}
                    className="chart-view-image"
                    onError={(e) => {
                      console.error('Failed to load chart:', getChartUrl(selectedChart));
                      e.target.alt = 'Failed to load chart';
                    }}
                  />
                </div>
              </div>
            )}

            {activeTab === 'insights' && (
              <div className="insights-view fade-in">
                {insights ? (
                  <div className="insights-card">
                    <div className="insights-header">
                      <Sparkles size={24} />
                      <h2>AI-Powered Analysis</h2>
                    </div>
                    <div className="insights-content">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeRaw]}
                        components={{
                          img: ({node, ...props}) => (
                            <img
                              {...props}
                              src={props.src?.startsWith('http') ? props.src : `http://localhost:8000${props.src}`}
                              style={{maxWidth: '100%', height: 'auto', margin: '20px 0', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)'}}
                              alt={props.alt || 'Chart visualization'}
                            />
                          )
                        }}
                      >
                        {insights}
                      </ReactMarkdown>
                    </div>
                  </div>
                ) : (
                  <div className="empty-state">
                    <Sparkles size={64} />
                    <p>Generating AI insights...</p>
                    <div className="loading-spinner"></div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'charts' && !selectedChart && (
              <div className="empty-state">
                <BarChart size={64} />
                <p>Select a chart from the sidebar</p>
                {session.charts && session.charts.length === 0 && (
                  <button onClick={() => navigate('/')} className="btn btn-primary">
                    <ArrowLeft size={18} />
                    Back to Home
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function to format chart titles
const formatChartTitle = (chartType, columnName) => {
  const typeMap = {
    histogram: 'Histogram',
    bar: 'Bar Chart',
    correlation: 'Correlation Heatmap',
    pairplot: 'Pair Plot',
    boxplot: 'Box Plot',
    missing: 'Missing Values',
    scatter: 'Scatter Plot',
    distribution: 'Distribution Plot',
  };

  const title = typeMap[chartType] || chartType;
  return columnName ? `${title}: ${columnName}` : title;
};

export default Dashboard;
