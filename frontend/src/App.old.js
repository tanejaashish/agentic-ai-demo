import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

function App() {
  const [incident, setIncident] = useState({
    title: '',
    description: '',
    priority: 'Medium',
    category: 'General',
    error_message: '',
    affected_systems: []
  });

  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState({});
  const [wsConnected, setWsConnected] = useState(false);
  const [processingSteps, setProcessingSteps] = useState([]);
  const [selectedDemo, setSelectedDemo] = useState('');

  // Demo scenarios
  const demoScenarios = {
    database: {
      title: "Database connection pool exhausted",
      description: "Production database showing 'Connection pool exhausted' errors during peak hours. Response times have increased significantly.",
      priority: "High",
      category: "Database",
      error_message: "java.sql.SQLException: Cannot get a connection, pool exhausted",
      affected_systems: ["MySQL", "API Server", "Customer Portal"]
    },
    api: {
      title: "API Gateway returning 502 errors",
      description: "Multiple microservices behind the API Gateway are unreachable. Health checks failing intermittently.",
      priority: "Critical",
      category: "Network",
      error_message: "502 Bad Gateway - upstream connection failed",
      affected_systems: ["API Gateway", "Auth Service", "User Service"]
    },
    memory: {
      title: "Memory leak detected in payment service",
      description: "Payment processing service memory usage growing continuously. Service requires restart every 24 hours.",
      priority: "High",
      category: "Application",
      error_message: "java.lang.OutOfMemoryError: Java heap space",
      affected_systems: ["Payment Service", "Transaction Queue"]
    },
    vague: {
      title: "System is slow",
      description: "Users reporting slowness",
      priority: "Medium",
      category: "Performance",
      error_message: "",
      affected_systems: ["Unknown"]
    }
  };

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'metrics') {
        setMetrics(data.data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setIncident(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSystemsChange = (e) => {
    const systems = e.target.value.split(',').map(s => s.trim()).filter(s => s);
    setIncident(prev => ({
      ...prev,
      affected_systems: systems
    }));
  };

  const loadDemoScenario = (scenarioKey) => {
    if (scenarioKey && demoScenarios[scenarioKey]) {
      setIncident(demoScenarios[scenarioKey]);
      setSelectedDemo(scenarioKey);
    }
  };

  const processIncident = async () => {
    setLoading(true);
    setResponse(null);
    setProcessingSteps([]);

    try {
      // Add processing steps for visualization
      const steps = [
        { step: 'Analyzing incident...', status: 'processing' },
        { step: 'RAG: Retrieving similar incidents...', status: 'processing' },
        { step: 'RAG: Generating initial recommendations...', status: 'processing' },
        { step: 'Prediction: Analyzing severity and resolution time...', status: 'processing' },
        { step: 'CAG: Evaluating response quality...', status: 'processing' },
        { step: 'CAG: Refining recommendations...', status: 'processing' },
        { step: 'Finalizing response...', status: 'processing' }
      ];

      // Simulate progressive updates
      for (let i = 0; i < steps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 300));
        setProcessingSteps(prev => [...prev.slice(0, i), { ...steps[i], status: 'completed' }]);
      }

      // Make API call
      const result = await axios.post(`${API_URL}/api/process-incident`, {
        ...incident,
        id: `INC${Date.now()}`
      });

      setResponse(result.data);
      setProcessingSteps(steps.map(s => ({ ...s, status: 'completed' })));

    } catch (error) {
      console.error('Error processing incident:', error);
      setResponse({
        error: 'Failed to process incident. Please check if all services are running.'
      });
      setProcessingSteps(prev => 
        prev.map(s => s.status === 'processing' ? { ...s, status: 'failed' } : s)
      );
    } finally {
      setLoading(false);
    }
  };

  const submitFeedback = async (rating) => {
    if (!response) return;

    try {
      await axios.post(`${API_URL}/api/feedback`, {
        incident_id: response.incident_id,
        rating: rating,
        helpful: rating >= 3,
        comments: `User rated ${rating}/5`
      });
      alert('Thank you for your feedback!');
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 Predictive Agentic AI Demo</h1>
        <p>RAG + CAG for Intelligent Incident Management</p>
        <div className="status-bar">
          <span className={`status ${wsConnected ? 'connected' : 'disconnected'}`}>
            {wsConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </div>
      </header>

      <div className="container">
        <div className="demo-section">
          <h2>📝 Submit Incident</h2>
          
          <div className="demo-selector">
            <label>Quick Demo Scenarios:</label>
            <select 
              value={selectedDemo} 
              onChange={(e) => loadDemoScenario(e.target.value)}
            >
              <option value="">-- Select Demo --</option>
              <option value="database">Database Connection Issue (Good RAG)</option>
              <option value="api">API Gateway Error (Critical)</option>
              <option value="memory">Memory Leak (Complex)</option>
              <option value="vague">Vague Description (Tests CAG)</option>
            </select>
          </div>

          <div className="form-group">
            <label>Title:</label>
            <input
              type="text"
              name="title"
              value={incident.title}
              onChange={handleInputChange}
              placeholder="Brief incident title"
            />
          </div>

          <div className="form-group">
            <label>Description:</label>
            <textarea
              name="description"
              value={incident.description}
              onChange={handleInputChange}
              rows="4"
              placeholder="Detailed description of the issue"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Priority:</label>
              <select name="priority" value={incident.priority} onChange={handleInputChange}>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>

            <div className="form-group">
              <label>Category:</label>
              <select name="category" value={incident.category} onChange={handleInputChange}>
                <option value="General">General</option>
                <option value="Database">Database</option>
                <option value="Network">Network</option>
                <option value="Application">Application</option>
                <option value="Security">Security</option>
                <option value="Infrastructure">Infrastructure</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Error Message (optional):</label>
            <input
              type="text"
              name="error_message"
              value={incident.error_message}
              onChange={handleInputChange}
              placeholder="Any specific error message"
            />
          </div>

          <div className="form-group">
            <label>Affected Systems (comma-separated):</label>
            <input
              type="text"
              value={incident.affected_systems.join(', ')}
              onChange={handleSystemsChange}
              placeholder="e.g., Database, API, Frontend"
            />
          </div>

          <button 
            className="submit-btn" 
            onClick={processIncident} 
            disabled={loading || !incident.title}
          >
            {loading ? '🔄 Processing...' : '🚀 Process with Agentic AI'}
          </button>
        </div>

        {processingSteps.length > 0 && (
          <div className="processing-visualization">
            <h3>🔄 Processing Pipeline</h3>
            <div className="steps">
              {processingSteps.map((step, index) => (
                <div key={index} className={`step ${step.status}`}>
                  <span className="step-icon">
                    {step.status === 'completed' ? '✅' : 
                     step.status === 'failed' ? '❌' : '⏳'}
                  </span>
                  <span className="step-text">{step.step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {response && !response.error && (
          <div className="response-section">
            <h2>🎯 AI Response</h2>
            
            <div className="metrics-row">
              <div className="metric-card">
                <span className="metric-label">Confidence</span>
                <span className="metric-value">{(response.confidence * 100).toFixed(1)}%</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Severity</span>
                <span className={`metric-value severity-${response.severity}`}>
                  {response.severity}
                </span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Est. Resolution</span>
                <span className="metric-value">{response.estimated_resolution_time} min</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Team</span>
                <span className="metric-value">{response.assigned_team}</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">CAG Applied</span>
                <span className="metric-value">{response.cag_applied ? '✅ Yes' : '❌ No'}</span>
              </div>
            </div>

            <div className="recommendations">
              <h3>📋 Recommendations</h3>
              {response.recommendations && response.recommendations.map((rec, index) => (
                <div key={index} className="recommendation-card">
                  <div className="rec-header">
                    <span className="rec-type">{rec.type === 'primary' ? '🎯 Primary' : '🔄 Alternative'}</span>
                    <span className="rec-confidence">Confidence: {(rec.confidence * 100).toFixed(0)}%</span>
                  </div>
                  
                  {rec.solution_steps && (
                    <div className="rec-section">
                      <h4>Solution Steps:</h4>
                      <div className="solution-steps">
                        {Array.isArray(rec.solution_steps) ? 
                          rec.solution_steps.map((step, i) => (
                            <div key={i} className="step-item">{step}</div>
                          )) : 
                          <div>{rec.solution_steps}</div>
                        }
                      </div>
                    </div>
                  )}
                  
                  {rec.root_cause && (
                    <div className="rec-section">
                      <h4>Root Cause:</h4>
                      <p>{rec.root_cause}</p>
                    </div>
                  )}
                  
                  {rec.prevention && (
                    <div className="rec-section">
                      <h4>Prevention:</h4>
                      <p>{rec.prevention}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {response.rag_sources && response.rag_sources.length > 0 && (
              <div className="sources">
                <h3>📚 Knowledge Sources</h3>
                <div className="source-list">
                  {response.rag_sources.map((source, index) => (
                    <div key={index} className="source-item">
                      <span className="source-title">{source.title}</span>
                      <span className="source-score">Relevance: {(source.relevance_score * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="feedback-section">
              <h3>📝 Provide Feedback</h3>
              <p>How helpful was this response?</p>
              <div className="feedback-buttons">
                {[1, 2, 3, 4, 5].map(rating => (
                  <button
                    key={rating}
                    className="feedback-btn"
                    onClick={() => submitFeedback(rating)}
                  >
                    {rating} ⭐
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {response && response.error && (
          <div className="error-section">
            <h3>❌ Error</h3>
            <p>{response.error}</p>
          </div>
        )}
      </div>

      <footer className="App-footer">
        <p>Built with FastAPI, ChromaDB, Ollama, and React</p>
        <p>Demonstrating RAG + CAG for Predictive Incident Management</p>
      </footer>
    </div>
  );
}

export default App;