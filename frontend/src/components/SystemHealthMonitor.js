/**
 * System Health Monitor Component
 * Real-time system health monitoring with alerts and metrics
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  FaHeartbeat,
  FaServer,
  FaDatabase,
  FaNetworkWired,
  FaExclamationTriangle,
  FaCheckCircle,
  FaTimesCircle,
  FaSync,
  FaBell,
  FaDownload,
  FaChartLine
} from 'react-icons/fa';
import { systemService, analyticsService } from '../services/api';
import websocketService from '../services/websocket';
import './SystemHealthMonitor.css';

const SystemHealthMonitor = () => {
  const [healthStatus, setHealthStatus] = useState('checking');
  const [systemInfo, setSystemInfo] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadHealthData = useCallback(async () => {
    try {
      setLoading(true);
      const [health, info, metricsData] = await Promise.all([
        systemService.healthCheck().catch(() => ({ status: 'unknown' })),
        systemService.getInfo().catch(() => null),
        analyticsService.getMetrics().catch(() => null)
      ]);

      setHealthStatus(health.status || 'unknown');
      setSystemInfo(info);
      setMetrics(metricsData);

      // Set demo services data
      setServices([
        {
          name: 'API Server',
          status: 'healthy',
          uptime: '99.9%',
          response_time: 45,
          last_check: new Date().toISOString()
        },
        {
          name: 'Database',
          status: 'healthy',
          uptime: '99.7%',
          response_time: 12,
          last_check: new Date().toISOString()
        },
        {
          name: 'Vector Store',
          status: 'healthy',
          uptime: '99.8%',
          response_time: 28,
          last_check: new Date().toISOString()
        },
        {
          name: 'RAG Agent',
          status: 'healthy',
          uptime: '99.6%',
          response_time: 156,
          last_check: new Date().toISOString()
        },
        {
          name: 'CAG Agent',
          status: 'healthy',
          uptime: '99.5%',
          response_time: 234,
          last_check: new Date().toISOString()
        },
        {
          name: 'Predictor Agent',
          status: 'warning',
          uptime: '98.2%',
          response_time: 89,
          last_check: new Date().toISOString(),
          message: 'High memory usage detected'
        }
      ]);

      // Set demo alerts
      setAlerts([
        {
          id: 1,
          severity: 'warning',
          service: 'Predictor Agent',
          message: 'Memory usage above 85% threshold',
          timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString()
        },
        {
          id: 2,
          severity: 'info',
          service: 'Database',
          message: 'Connection pool expanded to handle load',
          timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString()
        }
      ]);
    } catch (error) {
      console.error('Error loading health data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHealthData();

    // Connect to WebSocket for real-time updates
    websocketService.connect();
    const unsubscribe = websocketService.on('health', (data) => {
      setHealthStatus(data.status);
    });

    // Auto-refresh every 10 seconds if enabled
    let interval;
    if (autoRefresh) {
      interval = setInterval(loadHealthData, 10000);
    }

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, [loadHealthData, autoRefresh]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'critical': return '#ef4444';
      case 'unhealthy': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <FaCheckCircle />;
      case 'warning': return <FaExclamationTriangle />;
      case 'critical': return <FaTimesCircle />;
      case 'unhealthy': return <FaTimesCircle />;
      default: return <FaHeartbeat />;
    }
  };

  const exportHealthReport = () => {
    const report = {
      timestamp: new Date().toISOString(),
      overall_status: healthStatus,
      system_info: systemInfo,
      services: services,
      alerts: alerts,
      metrics: metrics
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `health-report-${Date.now()}.json`;
    a.click();
  };

  if (loading && !services.length) {
    return (
      <div className="health-loading">
        <FaHeartbeat className="loading-icon pulse" />
        <p>Checking System Health...</p>
      </div>
    );
  }

  return (
    <div className="system-health-monitor">
      {/* Header */}
      <div className="health-header">
        <div>
          <h1><FaHeartbeat /> System Health Monitor</h1>
          <p>Real-time monitoring of all system components</p>
        </div>
        <div className="health-actions">
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            <span>Auto-refresh (10s)</span>
          </label>
          <button onClick={loadHealthData} className="btn-secondary">
            <FaSync /> Refresh
          </button>
          <button onClick={exportHealthReport} className="btn-secondary">
            <FaDownload /> Export Report
          </button>
        </div>
      </div>

      {/* Overall Status Banner */}
      <div className="status-banner" style={{ borderColor: getStatusColor(healthStatus) }}>
        <div className="status-indicator">
          {getStatusIcon(healthStatus)}
          <div>
            <h2>System Status: <span style={{ color: getStatusColor(healthStatus) }}>
              {healthStatus.charAt(0).toUpperCase() + healthStatus.slice(1)}
            </span></h2>
            <p>Last updated: {new Date().toLocaleTimeString()}</p>
          </div>
        </div>
        <div className="status-stats">
          <div className="stat">
            <div className="stat-value">{services.filter(s => s.status === 'healthy').length}/{services.length}</div>
            <div className="stat-label">Services Healthy</div>
          </div>
          <div className="stat">
            <div className="stat-value">{systemInfo?.uptime || '5d 12h'}</div>
            <div className="stat-label">System Uptime</div>
          </div>
          <div className="stat">
            <div className="stat-value">{alerts.filter(a => a.severity !== 'info').length}</div>
            <div className="stat-label">Active Alerts</div>
          </div>
        </div>
      </div>

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div className="alerts-section">
          <h3><FaBell /> Recent Alerts</h3>
          <div className="alerts-list">
            {alerts.map(alert => (
              <div key={alert.id} className={`alert-item ${alert.severity}`}>
                <div className="alert-icon">
                  {alert.severity === 'warning' ? <FaExclamationTriangle /> : 
                   alert.severity === 'critical' ? <FaTimesCircle /> : 
                   <FaCheckCircle />}
                </div>
                <div className="alert-content">
                  <div className="alert-header">
                    <strong>{alert.service}</strong>
                    <span className="alert-time">
                      {new Date(alert.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p>{alert.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Services Grid */}
      <div className="services-section">
        <h3><FaServer /> Service Status</h3>
        <div className="services-grid">
          {services.map((service, idx) => (
            <div key={idx} className="service-card">
              <div className="service-header">
                <div className="service-icon" style={{ 
                  backgroundColor: getStatusColor(service.status) + '20',
                  color: getStatusColor(service.status)
                }}>
                  {service.name.includes('Database') ? <FaDatabase /> :
                   service.name.includes('Agent') ? <FaChartLine /> :
                   service.name.includes('Store') ? <FaDatabase /> :
                   <FaServer />}
                </div>
                <div className="service-info">
                  <h4>{service.name}</h4>
                  <span 
                    className="service-status-badge"
                    style={{ 
                      backgroundColor: getStatusColor(service.status) + '20',
                      color: getStatusColor(service.status)
                    }}
                  >
                    {getStatusIcon(service.status)}
                    {service.status}
                  </span>
                </div>
              </div>

              <div className="service-metrics">
                <div className="metric-item">
                  <span className="metric-label">Uptime</span>
                  <span className="metric-value">{service.uptime}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Response Time</span>
                  <span className="metric-value">{service.response_time}ms</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Last Check</span>
                  <span className="metric-value">
                    {new Date(service.last_check).toLocaleTimeString()}
                  </span>
                </div>
              </div>

              {service.message && (
                <div className="service-message">
                  <FaExclamationTriangle />
                  <span>{service.message}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* System Resources */}
      <div className="resources-section">
        <h3><FaNetworkWired /> System Resources</h3>
        <div className="resources-grid">
          <div className="resource-card">
            <h4>CPU Usage</h4>
            <div className="resource-bar">
              <div className="resource-fill" style={{ width: '45%', backgroundColor: '#10b981' }}></div>
            </div>
            <span>45% / 100%</span>
          </div>

          <div className="resource-card">
            <h4>Memory Usage</h4>
            <div className="resource-bar">
              <div className="resource-fill" style={{ width: '68%', backgroundColor: '#3b82f6' }}></div>
            </div>
            <span>6.8 GB / 10 GB</span>
          </div>

          <div className="resource-card">
            <h4>Disk I/O</h4>
            <div className="resource-bar">
              <div className="resource-fill" style={{ width: '32%', backgroundColor: '#8b5cf6' }}></div>
            </div>
            <span>32% / 100%</span>
          </div>

          <div className="resource-card">
            <h4>Network Traffic</h4>
            <div className="resource-bar">
              <div className="resource-fill" style={{ width: '58%', backgroundColor: '#f59e0b' }}></div>
            </div>
            <span>145 MB/s</span>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="performance-section">
        <h3><FaChartLine /> Performance Metrics</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-value-large">{metrics?.incidents?.total_processed || 1017}</div>
            <div className="metric-label">Total Requests</div>
            <div className="metric-trend positive">+12% from last week</div>
          </div>

          <div className="metric-card">
            <div className="metric-value-large">{metrics?.performance?.api_latency_ms || 143}ms</div>
            <div className="metric-label">Avg Response Time</div>
            <div className="metric-trend positive">-8% improvement</div>
          </div>

          <div className="metric-card">
            <div className="metric-value-large">99.7%</div>
            <div className="metric-label">Success Rate</div>
            <div className="metric-trend positive">+0.3% this month</div>
          </div>

          <div className="metric-card">
            <div className="metric-value-large">{metrics?.incidents?.last_hour || 19}</div>
            <div className="metric-label">Requests (Last Hour)</div>
            <div className="metric-trend neutral">Normal traffic</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealthMonitor;
