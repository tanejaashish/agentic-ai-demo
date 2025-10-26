/**
 * Learning Statistics Component - COMPLETE
 * Display AI/ML model performance, training history, and improvement trends
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  FaChartLine,
  FaBrain,
  FaTrophy,
  FaSync,
  FaDownload,
  FaArrowUp,
  FaArrowDown,
  FaCheckCircle,
  FaRobot,
  FaLightbulb,
  FaDatabase
} from 'react-icons/fa';
import toast from 'react-hot-toast';
import './LearningStatistics.css';

const LearningStatistics = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState('all');
  const [timeRange, setTimeRange] = useState('30days');

  const getDemoStatistics = () => {
    const generateDataPoints = (baseValue, variance, count) => {
      const points = [];
      let value = baseValue;
      for (let i = 0; i < count; i++) {
        value += (Math.random() - 0.3) * variance; // Upward trend
        points.push({
          timestamp: new Date(Date.now() - (count - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          value: Math.max(0, Math.min(100, value))
        });
      }
      return points;
    };

    return {
      overall: {
        avgAccuracy: 91.1,
        totalTrainingHours: 847,
        modelVersions: 23,
        improvements: 34.2,
        trendsUp: true
      },
      agents: {
        rag: {
          name: 'RAG Agent',
          currentAccuracy: 94.7,
          previousAccuracy: 91.2,
          improvement: 3.5,
          totalQueries: 1847,
          successRate: 96.2,
          avgResponseTime: 342,
          trainingHistory: [
            { version: 'v2.1.0', accuracy: 94.7, date: '2025-10-24', trainTime: 42 },
            { version: 'v2.0.3', accuracy: 93.8, date: '2025-10-17', trainTime: 38 },
            { version: 'v2.0.2', accuracy: 92.5, date: '2025-10-10', trainTime: 36 },
            { version: 'v2.0.1', accuracy: 91.2, date: '2025-10-03', trainTime: 35 }
          ],
          accuracyTrend: generateDataPoints(85, 2, 30),
          metrics: {
            precision: 93.4,
            recall: 95.8,
            f1Score: 94.6,
            cacheHitRate: 78.5
          }
        },
        cag: {
          name: 'CAG Agent',
          currentAccuracy: 91.3,
          previousAccuracy: 87.8,
          improvement: 3.5,
          totalCoordinations: 523,
          successRate: 89.4,
          avgResolutionTime: 1847,
          trainingHistory: [
            { version: 'v1.8.2', accuracy: 91.3, date: '2025-10-23', trainTime: 56 },
            { version: 'v1.8.1', accuracy: 89.7, date: '2025-10-16', trainTime: 52 },
            { version: 'v1.8.0', accuracy: 88.5, date: '2025-10-09', trainTime: 48 },
            { version: 'v1.7.9', accuracy: 87.8, date: '2025-10-02', trainTime: 45 }
          ],
          accuracyTrend: generateDataPoints(82, 2, 30),
          metrics: {
            precision: 89.2,
            recall: 91.8,
            f1Score: 90.5,
            avgAgentsPerTask: 2.3
          }
        },
        predictor: {
          name: 'Predictor Agent',
          currentAccuracy: 87.2,
          previousAccuracy: 82.1,
          improvement: 5.1,
          totalPredictions: 892,
          successRate: 85.4,
          avgConfidence: 82.6,
          trainingHistory: [
            { version: 'v3.0.1', accuracy: 87.2, date: '2025-10-22', trainTime: 68 },
            { version: 'v3.0.0', accuracy: 85.4, date: '2025-10-15', trainTime: 64 },
            { version: 'v2.9.8', accuracy: 83.9, date: '2025-10-08', trainTime: 60 },
            { version: 'v2.9.7', accuracy: 82.1, date: '2025-10-01', trainTime: 58 }
          ],
          accuracyTrend: generateDataPoints(78, 2, 30),
          metrics: {
            precision: 85.8,
            recall: 89.1,
            f1Score: 87.4,
            falsePositiveRate: 3.8
          }
        }
      },
      recentImprovements: [
        {
          agent: 'RAG',
          improvement: 'Improved cache hit rate',
          metric: '+12.3%',
          date: '2025-10-24',
          impact: 'High'
        },
        {
          agent: 'Predictor',
          improvement: 'Reduced false positives',
          metric: '-2.1%',
          date: '2025-10-22',
          impact: 'High'
        },
        {
          agent: 'CAG',
          improvement: 'Faster coordination time',
          metric: '-245ms',
          date: '2025-10-23',
          impact: 'Medium'
        },
        {
          agent: 'RAG',
          improvement: 'Enhanced retrieval accuracy',
          metric: '+1.5%',
          date: '2025-10-20',
          impact: 'Medium'
        }
      ]
    };
  };

  const loadStatistics = useCallback(async () => {
    try {
      setLoading(true);
      await new Promise(resolve => setTimeout(resolve, 800));
      const data = getDemoStatistics();
      setStats(data);
    } catch (error) {
      toast.error('Failed to load statistics');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatistics();
  }, [loadStatistics]);

  const getAgentIcon = (agent) => {
    switch (agent.toLowerCase()) {
      case 'rag': return <FaDatabase />;
      case 'cag': return <FaRobot />;
      case 'predictor': return <FaLightbulb />;
      default: return <FaBrain />;
    }
  };

  const handleExport = () => {
    const data = {
      exportDate: new Date().toISOString(),
      timeRange,
      selectedAgent,
      statistics: stats
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `learning_stats_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast.success('Statistics exported successfully');
  };

  if (loading) {
    return (
      <div className="stats-loading">
        <FaChartLine className="loading-icon spinning" />
        <p>Loading learning statistics...</p>
      </div>
    );
  }

  const filteredAgents = selectedAgent === 'all' 
    ? Object.entries(stats.agents) 
    : [[selectedAgent, stats.agents[selectedAgent]]];

  return (
    <div className="learning-statistics">
      {/* Header */}
      <div className="stats-header">
        <div>
          <h1><FaChartLine /> Learning Statistics</h1>
          <p>AI/ML model performance and training analytics</p>
        </div>
        <div className="header-actions">
          <button onClick={loadStatistics} className="btn-refresh">
            <FaSync /> Refresh
          </button>
          <button onClick={handleExport} className="btn-export">
            <FaDownload /> Export
          </button>
        </div>
      </div>

      {/* Overall Stats */}
      <div className="overall-stats">
        <div className="stat-card-large">
          <div className="stat-icon" style={{ background: '#8b5cf6' }}>
            <FaTrophy />
          </div>
          <div className="stat-content">
            <h3>{stats.overall.avgAccuracy}%</h3>
            <p>Average Accuracy</p>
            <div className="stat-trend positive">
              <FaArrowUp /> +{stats.overall.improvements}% vs last month
            </div>
          </div>
        </div>

        <div className="stat-card-large">
          <div className="stat-icon" style={{ background: '#3b82f6' }}>
            <FaBrain />
          </div>
          <div className="stat-content">
            <h3>{stats.overall.totalTrainingHours}</h3>
            <p>Training Hours</p>
            <div className="stat-trend">
              Across all models
            </div>
          </div>
        </div>

        <div className="stat-card-large">
          <div className="stat-icon" style={{ background: '#10b981' }}>
            <FaCheckCircle />
          </div>
          <div className="stat-content">
            <h3>{stats.overall.modelVersions}</h3>
            <p>Model Versions</p>
            <div className="stat-trend">
              Continuous improvement
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="stats-filters">
        <div className="filter-group">
          <label>Agent:</label>
          <select value={selectedAgent} onChange={(e) => setSelectedAgent(e.target.value)}>
            <option value="all">All Agents</option>
            <option value="rag">RAG Agent</option>
            <option value="cag">CAG Agent</option>
            <option value="predictor">Predictor Agent</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Time Range:</label>
          <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
            <option value="7days">Last 7 Days</option>
            <option value="30days">Last 30 Days</option>
            <option value="90days">Last 90 Days</option>
            <option value="all">All Time</option>
          </select>
        </div>
      </div>

      {/* Agent Performance Cards */}
      <div className="agents-performance">
        {filteredAgents.map(([key, agent]) => (
          <div key={key} className="performance-card">
            <div className="performance-header">
              <div className="agent-identity">
                <div className={`agent-icon-large ${key}`}>
                  {getAgentIcon(key)}
                </div>
                <div>
                  <h2>{agent.name}</h2>
                  <p>Current Performance</p>
                </div>
              </div>
              <div className="accuracy-display">
                <div className="accuracy-value">{agent.currentAccuracy}%</div>
                <div className={`accuracy-change ${agent.improvement >= 0 ? 'positive' : 'negative'}`}>
                  {agent.improvement >= 0 ? <FaArrowUp /> : <FaArrowDown />}
                  {Math.abs(agent.improvement)}% from last version
                </div>
              </div>
            </div>

            <div className="performance-metrics">
              <div className="metric-item">
                <span className="metric-label">Precision</span>
                <div className="metric-bar-container">
                  <div 
                    className="metric-bar" 
                    style={{ width: `${agent.metrics.precision}%`, background: '#3b82f6' }}
                  />
                </div>
                <span className="metric-value">{agent.metrics.precision}%</span>
              </div>

              <div className="metric-item">
                <span className="metric-label">Recall</span>
                <div className="metric-bar-container">
                  <div 
                    className="metric-bar" 
                    style={{ width: `${agent.metrics.recall}%`, background: '#10b981' }}
                  />
                </div>
                <span className="metric-value">{agent.metrics.recall}%</span>
              </div>

              <div className="metric-item">
                <span className="metric-label">F1 Score</span>
                <div className="metric-bar-container">
                  <div 
                    className="metric-bar" 
                    style={{ width: `${agent.metrics.f1Score}%`, background: '#8b5cf6' }}
                  />
                </div>
                <span className="metric-value">{agent.metrics.f1Score}%</span>
              </div>
            </div>

            {/* Training History */}
            <div className="training-history">
              <h3>Training History</h3>
              <div className="history-list">
                {agent.trainingHistory.map((training, idx) => (
                  <div key={idx} className="history-item">
                    <div className="history-left">
                      <div className="version-badge">{training.version}</div>
                      <div className="history-details">
                        <div className="accuracy-small">{training.accuracy}%</div>
                        <div className="date-small">{training.date}</div>
                      </div>
                    </div>
                    <div className="train-time">{training.trainTime}min</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Accuracy Trend Chart */}
            <div className="trend-chart">
              <h3>30-Day Accuracy Trend</h3>
              <div className="chart-container">
                <svg className="line-chart" viewBox="0 0 600 200">
                  <defs>
                    <linearGradient id={`gradient-${key}`} x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3"/>
                      <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.05"/>
                    </linearGradient>
                  </defs>
                  
                  {/* Draw line */}
                  <polyline
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="3"
                    points={agent.accuracyTrend.map((point, i) => {
                      const x = (i / (agent.accuracyTrend.length - 1)) * 580 + 10;
                      const y = 190 - (point.value * 1.8);
                      return `${x},${y}`;
                    }).join(' ')}
                  />
                  
                  {/* Draw area */}
                  <polygon
                    fill={`url(#gradient-${key})`}
                    points={
                      agent.accuracyTrend.map((point, i) => {
                        const x = (i / (agent.accuracyTrend.length - 1)) * 580 + 10;
                        const y = 190 - (point.value * 1.8);
                        return `${x},${y}`;
                      }).join(' ') + ' 590,190 10,190'
                    }
                  />
                  
                  {/* Draw points */}
                  {agent.accuracyTrend.map((point, i) => {
                    if (i % 5 === 0 || i === agent.accuracyTrend.length - 1) {
                      const x = (i / (agent.accuracyTrend.length - 1)) * 580 + 10;
                      const y = 190 - (point.value * 1.8);
                      return (
                        <circle
                          key={i}
                          cx={x}
                          cy={y}
                          r="4"
                          fill="#3b82f6"
                          stroke="white"
                          strokeWidth="2"
                        />
                      );
                    }
                    return null;
                  })}
                </svg>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Improvements */}
      <div className="recent-improvements">
        <h2>Recent Improvements</h2>
        <div className="improvements-list">
          {stats.recentImprovements.map((improvement, idx) => (
            <div key={idx} className="improvement-item">
              <div className="improvement-left">
                <div className={`improvement-icon ${improvement.agent.toLowerCase()}`}>
                  {getAgentIcon(improvement.agent)}
                </div>
                <div className="improvement-info">
                  <h4>{improvement.improvement}</h4>
                  <p>{improvement.agent} Agent • {improvement.date}</p>
                </div>
              </div>
              <div className="improvement-right">
                <div className="metric-change">{improvement.metric}</div>
                <div className={`impact-badge ${improvement.impact.toLowerCase()}`}>
                  {improvement.impact} Impact
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LearningStatistics;
