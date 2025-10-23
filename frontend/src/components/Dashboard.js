/**
 * Dashboard Component - Main system overview
 * Displays key metrics, recent incidents, and system health
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FaRobot,
  FaChartLine,
  FaBrain,
  FaDatabase,
  FaExclamationTriangle,
  FaCheckCircle,
  FaClock,
  FaArrowRight
} from 'react-icons/fa';
import { incidentService, analyticsService, agentService, systemService } from '../services/api';
import websocketService from '../services/websocket';
import './Dashboard.css';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [systemInfo, setSystemInfo] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [incidentStats, setIncidentStats] = useState(null);
  const [agentStatus, setAgentStatus] = useState(null);
  const [recentIncidents, setRecentIncidents] = useState([]);
  const [healthStatus, setHealthStatus] = useState('checking');

  useEffect(() => {
    loadDashboardData();

    // Connect to WebSocket for real-time updates
    websocketService.connect();

    const unsubscribeMetrics = websocketService.on('metrics', (data) => {
      setMetrics(data);
    });

    const unsubscribeAgent = websocketService.on('agent_status', (data) => {
      setAgentStatus(data);
    });

    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      loadDashboardData();
    }, 30000);

    return () => {
      clearInterval(interval);
      unsubscribeMetrics();
      unsubscribeAgent();
    };
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load all dashboard data in parallel
      const [
        systemInfoRes,
        metricsRes,
        incidentStatsRes,
        agentStatusRes,
        incidentsRes,
        healthRes
      ] = await Promise.all([
        systemService.getInfo().catch(() => null),
        analyticsService.getMetrics().catch(() => null),
        incidentService.getStats().catch(() => null),
        agentService.getStatus().catch(() => null),
        incidentService.listIncidents({ limit: 5 }).catch(() => []),
        systemService.healthCheck().catch(() => ({ status: 'unknown' }))
      ]);

      setSystemInfo(systemInfoRes);
      setMetrics(metricsRes);
      setIncidentStats(incidentStatsRes);
      setAgentStatus(agentStatusRes);
      setRecentIncidents(incidentsRes);
      setHealthStatus(healthRes?.status || 'unknown');
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (status) => {
    switch (status) {
      case 'healthy': return '#10b981';
      case 'degraded': return '#f59e0b';
      case 'unhealthy': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <FaRobot className="loading-icon" />
        <p>Loading Dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Agentic AI Dashboard</h1>
          <p>Production-Ready AI System with RAG, CAG, and Predictive Analytics</p>
        </div>
        <div className="health-indicator">
          <span
            className="health-dot"
            style={{ backgroundColor: getHealthColor(healthStatus) }}
          ></span>
          <span className="health-text">
            {healthStatus === 'healthy' ? 'All Systems Operational' :
             healthStatus === 'degraded' ? 'Degraded Performance' :
             healthStatus === 'unhealthy' ? 'System Issues Detected' :
             'Checking Status'}
          </span>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon" style={{ backgroundColor: '#3b82f6' }}>
            <FaExclamationTriangle />
          </div>
          <div className="metric-content">
            <h3>{incidentStats?.total_incidents || 0}</h3>
            <p>Total Incidents</p>
            <span className="metric-trend">
              {incidentStats?.trend || '+0%'} from last week
            </span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ backgroundColor: '#10b981' }}>
            <FaCheckCircle />
          </div>
          <div className="metric-content">
            <h3>{incidentStats?.resolved_incidents || 0}</h3>
            <p>Resolved</p>
            <span className="metric-trend">
              {incidentStats?.resolution_rate || '0'}% resolution rate
            </span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ backgroundColor: '#f59e0b' }}>
            <FaClock />
          </div>
          <div className="metric-content">
            <h3>{metrics?.avg_processing_time || '0'}s</h3>
            <p>Avg Processing Time</p>
            <span className="metric-trend">
              Response latency
            </span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ backgroundColor: '#8b5cf6' }}>
            <FaBrain />
          </div>
          <div className="metric-content">
            <h3>{metrics?.avg_confidence || '0'}%</h3>
            <p>Avg Confidence</p>
            <span className="metric-trend">
              AI accuracy score
            </span>
          </div>
        </div>
      </div>

      {/* Agent Status Section */}
      <div className="dashboard-section">
        <div className="section-header">
          <h2>
            <FaRobot /> Agent Status
          </h2>
          <Link to="/agents" className="view-all-link">
            View Details <FaArrowRight />
          </Link>
        </div>
        <div className="agent-status-grid">
          <div className="agent-card">
            <h3>RAG Agent</h3>
            <div className="agent-status">
              <span className="status-badge status-active">Active</span>
              <span className="agent-metric">
                {agentStatus?.rag?.queries_processed || 0} queries
              </span>
            </div>
            <div className="agent-performance">
              <div className="performance-bar">
                <div
                  className="performance-fill"
                  style={{ width: `${agentStatus?.rag?.performance || 0}%` }}
                ></div>
              </div>
              <span>{agentStatus?.rag?.performance || 0}% performance</span>
            </div>
          </div>

          <div className="agent-card">
            <h3>CAG Agent</h3>
            <div className="agent-status">
              <span className="status-badge status-active">Active</span>
              <span className="agent-metric">
                {agentStatus?.cag?.refinements || 0} refinements
              </span>
            </div>
            <div className="agent-performance">
              <div className="performance-bar">
                <div
                  className="performance-fill"
                  style={{ width: `${agentStatus?.cag?.performance || 0}%` }}
                ></div>
              </div>
              <span>{agentStatus?.cag?.performance || 0}% performance</span>
            </div>
          </div>

          <div className="agent-card">
            <h3>Predictor Agent</h3>
            <div className="agent-status">
              <span className="status-badge status-active">Active</span>
              <span className="agent-metric">
                {agentStatus?.predictor?.predictions || 0} predictions
              </span>
            </div>
            <div className="agent-performance">
              <div className="performance-bar">
                <div
                  className="performance-fill"
                  style={{ width: `${agentStatus?.predictor?.performance || 0}%` }}
                ></div>
              </div>
              <span>{agentStatus?.predictor?.performance || 0}% accuracy</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Incidents Section */}
      <div className="dashboard-section">
        <div className="section-header">
          <h2>
            <FaDatabase /> Recent Incidents
          </h2>
          <Link to="/incidents" className="view-all-link">
            View All <FaArrowRight />
          </Link>
        </div>
        <div className="incidents-list">
          {recentIncidents.length === 0 ? (
            <div className="no-data">
              <p>No incidents to display</p>
            </div>
          ) : (
            recentIncidents.map((incident, index) => (
              <div key={index} className="incident-item">
                <div className="incident-severity">
                  <span
                    className="severity-dot"
                    style={{ backgroundColor: getSeverityColor(incident.severity) }}
                  ></span>
                </div>
                <div className="incident-details">
                  <h4>{incident.title || 'Untitled Incident'}</h4>
                  <p>{incident.description?.substring(0, 100)}...</p>
                  <div className="incident-meta">
                    <span className="meta-item">
                      {incident.category || 'Uncategorized'}
                    </span>
                    <span className="meta-item">
                      {incident.priority || 'Medium'} Priority
                    </span>
                    <span className="meta-item">
                      {new Date(incident.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="incident-actions">
                  <Link to={`/incidents/${incident.id}`} className="action-btn">
                    View Details
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="dashboard-section">
        <div className="section-header">
          <h2>
            <FaChartLine /> Quick Actions
          </h2>
        </div>
        <div className="quick-actions-grid">
          <Link to="/process" className="action-card">
            <FaExclamationTriangle />
            <h3>Process Incident</h3>
            <p>Submit a new incident for AI analysis</p>
          </Link>

          <Link to="/metrics" className="action-card">
            <FaChartLine />
            <h3>View Metrics</h3>
            <p>Comprehensive system metrics and trends</p>
          </Link>

          <Link to="/knowledge" className="action-card">
            <FaDatabase />
            <h3>Knowledge Base</h3>
            <p>Manage knowledge articles and documentation</p>
          </Link>

          <Link to="/graph" className="action-card">
            <FaBrain />
            <h3>Knowledge Graph</h3>
            <p>Explore incident relationships and patterns</p>
          </Link>
        </div>
      </div>

      {/* System Information */}
      {systemInfo && (
        <div className="dashboard-section">
          <div className="section-header">
            <h2>System Information</h2>
          </div>
          <div className="system-info-grid">
            <div className="info-item">
              <span className="info-label">Version:</span>
              <span className="info-value">{systemInfo.version || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Uptime:</span>
              <span className="info-value">{systemInfo.uptime || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">LLM Service:</span>
              <span className="info-value">{systemInfo.llm_service || 'Ollama'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Vector DB:</span>
              <span className="info-value">{systemInfo.vector_db || 'ChromaDB'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
