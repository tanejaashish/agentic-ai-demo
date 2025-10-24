/**
 * MetricsDashboard Component - Comprehensive metrics visualization
 * Real-time charts and performance analytics
 */

import React, { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { FaChartLine, FaDownload, FaSync } from 'react-icons/fa';
import { analyticsService } from '../services/api';
import websocketService from '../services/websocket';
import './MetricsDashboard.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const MetricsDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);
  const [trends, setTrends] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [feedbackStats, setFeedbackStats] = useState(null);
  const [resourceUsage, setResourceUsage] = useState(null);
  const [timeRange, setTimeRange] = useState(7); // days

  useEffect(() => {
    loadMetrics();

    // Connect to WebSocket
    websocketService.connect();
    const unsubscribe = websocketService.on('metrics', (data) => {
      setMetrics(prev => ({ ...prev, ...data }));
    });

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      loadMetrics();
    }, 30000);

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, [timeRange]);

  const loadMetrics = async () => {
    try {
      setLoading(true);
      const [metricsRes, trendsRes, performanceRes, feedbackRes, resourceRes] = await Promise.all([
        analyticsService.getMetrics(),
        analyticsService.getTrends(timeRange),
        analyticsService.getPerformance(),
        analyticsService.getFeedbackStats(),
        analyticsService.getResourceUsage()
      ]);

      setMetrics(metricsRes);
      setTrends(trendsRes);
      setPerformance(performanceRes);
      setFeedbackStats(feedbackRes);
      setResourceUsage(resourceRes);
    } catch (error) {
      console.error('Error loading metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadMetrics();
  };

  const handleExport = () => {
    const data = {
      metrics,
      trends,
      performance,
      feedbackStats,
      resourceUsage,
      exported_at: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `metrics-${Date.now()}.json`;
    a.click();
  };

  // Chart configurations
  const trendChartData = {
    labels: trends?.labels || [],
    datasets: [
      {
        label: 'Incidents',
        data: trends?.incidents || [],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Resolved',
        data: trends?.resolved || [],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  const performanceChartData = {
    labels: ['RAG', 'CAG', 'Predictor', 'Overall'],
    datasets: [
      {
        label: 'Performance (%)',
        data: [
          performance?.rag_performance || 0,
          performance?.cag_performance || 0,
          performance?.predictor_performance || 0,
          performance?.overall_performance || 0
        ],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(139, 92, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)'
        ]
      }
    ]
  };

  const severityChartData = {
    labels: ['Low', 'Medium', 'High', 'Critical'],
    datasets: [
      {
        data: [
          metrics?.severity_distribution?.low || 0,
          metrics?.severity_distribution?.medium || 0,
          metrics?.severity_distribution?.high || 0,
          metrics?.severity_distribution?.critical || 0
        ],
        backgroundColor: [
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(239, 68, 68, 0.8)'
        ]
      }
    ]
  };

  const feedbackChartData = {
    labels: ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
    datasets: [
      {
        label: 'Feedback Distribution',
        data: [
          feedbackStats?.ratings_distribution?.[1] || 0,
          feedbackStats?.ratings_distribution?.[2] || 0,
          feedbackStats?.ratings_distribution?.[3] || 0,
          feedbackStats?.ratings_distribution?.[4] || 0,
          feedbackStats?.ratings_distribution?.[5] || 0
        ],
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(16, 185, 129, 0.8)'
        ]
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom'
      }
    }
  };

  if (loading && !metrics) {
    return (
      <div className="metrics-loading">
        <FaChartLine className="loading-icon" />
        <p>Loading Metrics...</p>
      </div>
    );
  }

  return (
    <div className="metrics-dashboard">
      <div className="metrics-header">
        <div>
          <h1>Metrics Dashboard</h1>
          <p>Comprehensive system analytics and performance monitoring</p>
        </div>
        <div className="metrics-actions">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="time-range-select"
          >
            <option value={1}>Last 24 Hours</option>
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
          <button onClick={handleRefresh} className="action-button">
            <FaSync /> Refresh
          </button>
          <button onClick={handleExport} className="action-button">
            <FaDownload /> Export
          </button>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <h3>Total Requests</h3>
          <div className="kpi-value">{metrics?.total_requests || 0}</div>
          <div className="kpi-change positive">+{metrics?.request_growth || 0}%</div>
        </div>

        <div className="kpi-card">
          <h3>Avg Response Time</h3>
          <div className="kpi-value">{metrics?.avg_response_time || 0}ms</div>
          <div className="kpi-change negative">-{metrics?.latency_improvement || 0}%</div>
        </div>

        <div className="kpi-card">
          <h3>Success Rate</h3>
          <div className="kpi-value">{metrics?.success_rate || 0}%</div>
          <div className="kpi-change positive">+{metrics?.success_improvement || 0}%</div>
        </div>

        <div className="kpi-card">
          <h3>Avg Confidence</h3>
          <div className="kpi-value">{metrics?.avg_confidence || 0}%</div>
          <div className="kpi-change positive">+{metrics?.confidence_improvement || 0}%</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        <div className="chart-card large">
          <h3>Incident Trends</h3>
          <div className="chart-container">
            <Line data={trendChartData} options={chartOptions} />
          </div>
        </div>

        <div className="chart-card">
          <h3>Agent Performance</h3>
          <div className="chart-container">
            <Bar data={performanceChartData} options={chartOptions} />
          </div>
        </div>

        <div className="chart-card">
          <h3>Severity Distribution</h3>
          <div className="chart-container">
            <Doughnut data={severityChartData} options={chartOptions} />
          </div>
        </div>

        <div className="chart-card">
          <h3>Feedback Ratings</h3>
          <div className="chart-container">
            <Bar data={feedbackChartData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Resource Usage */}
      <div className="resource-section">
        <h2>Resource Usage</h2>
        <div className="resource-grid">
          <div className="resource-card">
            <div className="resource-header">
              <span>CPU Usage</span>
              <span className="resource-value">{resourceUsage?.cpu_usage || 0}%</span>
            </div>
            <div className="resource-bar">
              <div
                className="resource-fill cpu"
                style={{ width: `${resourceUsage?.cpu_usage || 0}%` }}
              ></div>
            </div>
          </div>

          <div className="resource-card">
            <div className="resource-header">
              <span>Memory Usage</span>
              <span className="resource-value">{resourceUsage?.memory_usage || 0}%</span>
            </div>
            <div className="resource-bar">
              <div
                className="resource-fill memory"
                style={{ width: `${resourceUsage?.memory_usage || 0}%` }}
              ></div>
            </div>
          </div>

          <div className="resource-card">
            <div className="resource-header">
              <span>Storage Usage</span>
              <span className="resource-value">{resourceUsage?.storage_usage || 0}%</span>
            </div>
            <div className="resource-bar">
              <div
                className="resource-fill storage"
                style={{ width: `${resourceUsage?.storage_usage || 0}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics Table */}
      <div className="performance-section">
        <h2>Detailed Performance Metrics</h2>
        <div className="metrics-table">
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Current</th>
                <th>P50</th>
                <th>P95</th>
                <th>P99</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Response Time (ms)</td>
                <td>{performance?.response_time?.current || 0}</td>
                <td>{performance?.response_time?.p50 || 0}</td>
                <td>{performance?.response_time?.p95 || 0}</td>
                <td>{performance?.response_time?.p99 || 0}</td>
              </tr>
              <tr>
                <td>RAG Retrieval (ms)</td>
                <td>{performance?.rag_retrieval?.current || 0}</td>
                <td>{performance?.rag_retrieval?.p50 || 0}</td>
                <td>{performance?.rag_retrieval?.p95 || 0}</td>
                <td>{performance?.rag_retrieval?.p99 || 0}</td>
              </tr>
              <tr>
                <td>CAG Refinement (ms)</td>
                <td>{performance?.cag_refinement?.current || 0}</td>
                <td>{performance?.cag_refinement?.p50 || 0}</td>
                <td>{performance?.cag_refinement?.p95 || 0}</td>
                <td>{performance?.cag_refinement?.p99 || 0}</td>
              </tr>
              <tr>
                <td>Prediction (ms)</td>
                <td>{performance?.prediction?.current || 0}</td>
                <td>{performance?.prediction?.p50 || 0}</td>
                <td>{performance?.prediction?.p95 || 0}</td>
                <td>{performance?.prediction?.p99 || 0}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default MetricsDashboard;
