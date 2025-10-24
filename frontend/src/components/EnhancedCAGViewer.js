/**
 * EnhancedCAGViewer Component - Multi-stage CAG with Critic Evaluations
 * Displays detailed critic analysis and refinement stages
 */

import React from 'react';
import { FaBrain, FaCheckCircle, FaExclamationCircle, FaLightbulb } from 'react-icons/fa';
import './EnhancedCAGViewer.css';

const EnhancedCAGViewer = ({ cagData }) => {
  if (!cagData || !cagData.critics) {
    return null;
  }

  const { critics, refinements, confidence_progression, final_confidence } = cagData;

  const getCriticIcon = (criticName) => {
    switch (criticName.toLowerCase()) {
      case 'technical': return <FaBrain />;
      case 'completeness': return <FaCheckCircle />;
      case 'safety': return <FaExclamationCircle />;
      case 'clarity': return <FaLightbulb />;
      default: return <FaBrain />;
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return '#10b981';
    if (score >= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="enhanced-cag-viewer">
      <div className="cag-header">
        <h2>
          <FaBrain /> Enhanced CAG Analysis
        </h2>
        <div className="confidence-badge" style={{ backgroundColor: getScoreColor(final_confidence / 100) }}>
          Final Confidence: {final_confidence}%
        </div>
      </div>

      {/* Confidence Progression */}
      {confidence_progression && (
        <div className="confidence-progression">
          <h3>Confidence Progression</h3>
          <div className="progression-track">
            {confidence_progression.map((conf, index) => (
              <div key={index} className="progression-point">
                <div className="point-marker" style={{ backgroundColor: getScoreColor(conf / 100) }}>
                  {conf}%
                </div>
                <span>Stage {index + 1}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Critic Evaluations */}
      <div className="critics-section">
        <h3>Critic Evaluations</h3>
        <div className="critics-grid">
          {Object.entries(critics).map(([criticName, evaluation]) => (
            <div key={criticName} className="critic-card">
              <div className="critic-header">
                <span className="critic-icon">{getCriticIcon(criticName)}</span>
                <div>
                  <h4>{criticName.charAt(0).toUpperCase() + criticName.slice(1)} Critic</h4>
                  <div className="critic-score">
                    Score: <span style={{ color: getScoreColor(evaluation.score) }}>
                      {(evaluation.score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              {evaluation.issues && evaluation.issues.length > 0 && (
                <div className="critic-issues">
                  <strong>Issues Identified:</strong>
                  <ul>
                    {evaluation.issues.map((issue, idx) => (
                      <li key={idx}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}

              {evaluation.suggestions && evaluation.suggestions.length > 0 && (
                <div className="critic-suggestions">
                  <strong>Suggestions:</strong>
                  <ul>
                    {evaluation.suggestions.map((suggestion, idx) => (
                      <li key={idx}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Refinement Stages */}
      {refinements && refinements.length > 0 && (
        <div className="refinements-section">
          <h3>Refinement Stages</h3>
          <div className="refinements-timeline">
            {refinements.map((refinement, index) => (
              <div key={index} className="refinement-stage">
                <div className="stage-marker">{index + 1}</div>
                <div className="stage-content">
                  <h4>Stage {index + 1} - {refinement.type}</h4>
                  <p>{refinement.description}</p>
                  {refinement.improvements && (
                    <div className="improvements-list">
                      <strong>Improvements:</strong>
                      <ul>
                        {refinement.improvements.map((imp, idx) => (
                          <li key={idx}>{imp}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedCAGViewer;
