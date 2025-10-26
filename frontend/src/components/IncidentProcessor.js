/**
 * IncidentProcessor Component - Main incident submission and processing form
 * This preserves the original App.js functionality
 */

import React, { useState } from 'react';
import { incidentService } from '../services/api';
import EnhancedCAGViewer from './EnhancedCAGViewer';
import toast from 'react-hot-toast';
import './IncidentProcessor.css';

const IncidentProcessor = () => {
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

  const demoScenarios = {
    database: {
      title: "Database connection pool exhausted",
      description: "Production database showing 'Connection pool exhausted' errors during peak hours.",
      priority: "High",
      category: "Database",
      error_message: "java.sql.SQLException: Cannot get a connection, pool exhausted",
      affected_systems: ["MySQL", "API Server", "Customer Portal"]
    },
    api: {
      title: "API Gateway returning 502 errors",
      description: "Multiple microservices behind the API Gateway are unreachable.",
      priority: "Critical",
      category: "Network",
      error_message: "502 Bad Gateway - upstream connection failed",
      affected_systems: ["API Gateway", "Auth Service", "User Service"]
    },
    memory: {
      title: "Memory leak detected in payment service",
      description: "Payment processing service memory usage growing continuously.",
      priority: "High",
      category: "Application",
      error_message: "java.lang.OutOfMemoryError: Java heap space",
      affected_systems: ["Payment Service", "Transaction Queue"]
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setIncident(prev => ({ ...prev, [name]: value }));
  };

  const handleSystemsChange = (e) => {
    const systems = e.target.value.split(',').map(s => s.trim()).filter(s => s);
    setIncident(prev => ({ ...prev, affected_systems: systems }));
  };

  const loadDemo = (demoKey) => {
    setIncident(demoScenarios[demoKey]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);

    try {
      const result = await incidentService.processIncident(incident);
      setResponse(result);
      toast.success('Incident processed successfully!');
    } catch (error) {
      toast.error('Failed to process incident: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  //const handleFeedback = async (rating) => {
  //  if (!response?.incident_id) return;

  //  try {
  //    await incidentService.submitFeedback(response.incident_id, { rating, helpful: rating >= 3 });
  //    toast.success('Thank you for your feedback!');
  //  } catch (error) {
  //    toast.error('Failed to submit feedback');
  //  }
  //};

  const handleFeedback = async (rating) => {
    if (!response?.incident_id) return;

    try {
      await incidentService.submitFeedback(response.incident_id, { 
        rating, 
        helpful: rating >= 3,
        comments: ""
      });
      toast.success('Thank you for your feedback!');
    } catch (error) {
      console.error('Feedback error:', error);
      toast.error('Failed to submit feedback');
    }
  };

  return (
    <div className="incident-processor">
      <div className="processor-header">
        <h1>Process New Incident</h1>
        <p>Submit an incident for AI-powered analysis and recommendations</p>
      </div>

      {/* Demo Scenarios */}
      <div className="demo-scenarios">
        <h3>Try a Demo Scenario:</h3>
        <div className="demo-buttons">
          <button onClick={() => loadDemo('database')} className="demo-btn">
            Database Issue
          </button>
          <button onClick={() => loadDemo('api')} className="demo-btn">
            API Gateway Error
          </button>
          <button onClick={() => loadDemo('memory')} className="demo-btn">
            Memory Leak
          </button>
        </div>
      </div>

      {/* Incident Form */}
      <form onSubmit={handleSubmit} className="incident-form">
        <div className="form-group">
          <label>Title *</label>
          <input
            type="text"
            name="title"
            value={incident.title}
            onChange={handleInputChange}
            required
            placeholder="Brief description of the incident"
          />
        </div>

        <div className="form-group">
          <label>Description *</label>
          <textarea
            name="description"
            value={incident.description}
            onChange={handleInputChange}
            required
            rows="4"
            placeholder="Detailed description of what happened"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Priority *</label>
            <select name="priority" value={incident.priority} onChange={handleInputChange}>
              <option>Low</option>
              <option>Medium</option>
              <option>High</option>
              <option>Critical</option>
            </select>
          </div>

          <div className="form-group">
            <label>Category *</label>
            <select name="category" value={incident.category} onChange={handleInputChange}>
              <option>General</option>
              <option>Database</option>
              <option>Network</option>
              <option>Application</option>
              <option>Security</option>
              <option>Performance</option>
              <option>Infrastructure</option>
              <option>Other</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label>Error Message</label>
          <textarea
            name="error_message"
            value={incident.error_message}
            onChange={handleInputChange}
            rows="2"
            placeholder="Any error messages or stack traces"
          />
        </div>

        <div className="form-group">
          <label>Affected Systems</label>
          <input
            type="text"
            value={incident.affected_systems.join(', ')}
            onChange={handleSystemsChange}
            placeholder="Comma-separated list of affected systems"
          />
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? 'Processing...' : 'Process Incident'}
        </button>
      </form>

      {/* Response Display */}
      {response && (
        <div className="response-section">
          <div className="response-metrics">
            <div className="metric">
              <span>Confidence</span>
              <strong>{response.confidence}%</strong>
            </div>
            <div className="metric">
              <span>Severity</span>
              <strong>{response.severity}</strong>
            </div>
            <div className="metric">
              <span>Est. Resolution</span>
              <strong>{response.estimated_resolution_time}</strong>
            </div>
            <div className="metric">
              <span>Team</span>
              <strong>{response.assigned_team}</strong>
            </div>
          </div>

          {/* Enhanced CAG Viewer */}
          {response.cag_data && <EnhancedCAGViewer cagData={response.cag_data} />}

          {/* Recommendations */}
          {response.recommendations && (
            <div className="recommendations">
              <h3>Recommendations</h3>
              {response.recommendations.map((rec, idx) => (
                <div key={idx} className="recommendation-card">
                  <h4>{rec.title}</h4>
                  <p>{rec.description}</p>
                  {rec.steps && (
                    <div className="steps">
                      <strong>Steps:</strong>
                      <ol>
                        {rec.steps.map((step, i) => (
                          <li key={i}>{step}</li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Feedback */}
          <div className="feedback-section">
            <h3>Was this helpful?</h3>
            <div className="feedback-buttons">
              {[1, 2, 3, 4, 5].map(rating => (
                <button
                  key={rating}
                  onClick={() => handleFeedback(rating)}
                  className="feedback-btn"
                >
                  {'⭐'.repeat(rating)}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IncidentProcessor;
