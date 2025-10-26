/**
 * Audit Trail Viewer Component - COMPLETE
 * Track all system actions, user activities, and changes
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  FaHistory,
  FaUser,
  FaFilter,
  FaDownload,
  FaSearch,
  FaClock,
  FaCheckCircle,
  FaExclamationTriangle,
  FaInfoCircle,
  FaTrash,
  FaEdit,
  FaPlus,
  FaSync,
  FaDatabase,
  FaShieldAlt
} from 'react-icons/fa';
import toast from 'react-hot-toast';
import './AuditTrailViewer.css';

const AuditTrailViewer = () => {
  const [auditLogs, setAuditLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    searchQuery: '',
    actionType: 'all',
    dateRange: '7days',
    user: 'all'
  });
  const [stats, setStats] = useState({
    totalActions: 0,
    todayActions: 0,
    criticalEvents: 0,
    uniqueUsers: 0
  });

  // Demo data
  const getDemoAuditData = () => {
    const actions = ['create', 'update', 'delete', 'view', 'export', 'train', 'sync'];
    const entities = ['incident', 'knowledge_article', 'agent', 'user', 'configuration', 'model'];
    const users = ['admin@company.com', 'john.doe@company.com', 'jane.smith@company.com', 'ai.system@company.com'];
    const severities = ['info', 'warning', 'critical', 'success'];
    
    const logs = [];
    const now = new Date();
    
    for (let i = 0; i < 100; i++) {
      const hoursAgo = Math.floor(Math.random() * 168); // Last 7 days
      const timestamp = new Date(now - hoursAgo * 60 * 60 * 1000);
      
      const action = actions[Math.floor(Math.random() * actions.length)];
      const entity = entities[Math.floor(Math.random() * entities.length)];
      const severity = severities[Math.floor(Math.random() * severities.length)];
      
      logs.push({
        id: `audit_${i + 1}`,
        timestamp: timestamp.toISOString(),
        action,
        entity,
        entityId: `${entity}_${Math.floor(Math.random() * 1000)}`,
        user: users[Math.floor(Math.random() * users.length)],
        ipAddress: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
        severity,
        description: getActionDescription(action, entity),
        metadata: {
          duration: Math.floor(Math.random() * 5000),
          success: Math.random() > 0.1,
          changes: action === 'update' ? Math.floor(Math.random() * 10) + 1 : null
        }
      });
    }
    
    return logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  };

  const getActionDescription = (action, entity) => {
    const descriptions = {
      create: `Created new ${entity.replace('_', ' ')}`,
      update: `Updated ${entity.replace('_', ' ')} details`,
      delete: `Deleted ${entity.replace('_', ' ')}`,
      view: `Viewed ${entity.replace('_', ' ')} information`,
      export: `Exported ${entity.replace('_', ' ')} data`,
      train: `Trained ${entity.replace('_', ' ')} model`,
      sync: `Synchronized ${entity.replace('_', ' ')} data`
    };
    return descriptions[action] || `Performed ${action} on ${entity}`;
  };

  const loadAuditData = useCallback(async () => {
    try {
      setLoading(true);
      // Simulate API call - replace with actual API in production
      await new Promise(resolve => setTimeout(resolve, 800));
      
      const logs = getDemoAuditData();
      setAuditLogs(logs);
      setFilteredLogs(logs);
      
      // Calculate stats
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      setStats({
        totalActions: logs.length,
        todayActions: logs.filter(log => new Date(log.timestamp) >= today).length,
        criticalEvents: logs.filter(log => log.severity === 'critical').length,
        uniqueUsers: [...new Set(logs.map(log => log.user))].length
      });
    } catch (error) {
      toast.error('Failed to load audit logs');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAuditData();
  }, [loadAuditData]);

  useEffect(() => {
    applyFilters();
  }, [filters, auditLogs]);

  const applyFilters = () => {
    let filtered = [...auditLogs];

    // Search filter
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      filtered = filtered.filter(log =>
        log.description.toLowerCase().includes(query) ||
        log.user.toLowerCase().includes(query) ||
        log.entity.toLowerCase().includes(query)
      );
    }

    // Action type filter
    if (filters.actionType !== 'all') {
      filtered = filtered.filter(log => log.action === filters.actionType);
    }

    // Date range filter
    const now = new Date();
    const ranges = {
      '24hours': 24 * 60 * 60 * 1000,
      '7days': 7 * 24 * 60 * 60 * 1000,
      '30days': 30 * 24 * 60 * 60 * 1000,
      '90days': 90 * 24 * 60 * 60 * 1000
    };
    
    if (filters.dateRange !== 'all' && ranges[filters.dateRange]) {
      const cutoff = new Date(now - ranges[filters.dateRange]);
      filtered = filtered.filter(log => new Date(log.timestamp) >= cutoff);
    }

    // User filter
    if (filters.user !== 'all') {
      filtered = filtered.filter(log => log.user === filters.user);
    }

    setFilteredLogs(filtered);
  };

  const handleExport = () => {
    const csvContent = [
      ['Timestamp', 'Action', 'Entity', 'User', 'IP Address', 'Severity', 'Description'].join(','),
      ...filteredLogs.map(log =>
        [
          log.timestamp,
          log.action,
          log.entity,
          log.user,
          log.ipAddress,
          log.severity,
          `"${log.description}"`
        ].join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_trail_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast.success('Audit trail exported successfully');
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <FaExclamationTriangle />;
      case 'warning': return <FaExclamationTriangle />;
      case 'success': return <FaCheckCircle />;
      default: return <FaInfoCircle />;
    }
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'create': return <FaPlus />;
      case 'update': return <FaEdit />;
      case 'delete': return <FaTrash />;
      case 'sync': return <FaSync />;
      default: return <FaDatabase />;
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="audit-loading">
        <FaHistory className="loading-icon spinning" />
        <p>Loading audit trail...</p>
      </div>
    );
  }

  return (
    <div className="audit-trail-viewer">
      {/* Header */}
      <div className="audit-header">
        <div>
          <h1><FaHistory /> Audit Trail Viewer</h1>
          <p>Complete system activity and change log</p>
        </div>
        <button onClick={loadAuditData} className="btn-refresh">
          <FaSync /> Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="audit-stats">
        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#3b82f6' }}>
            <FaDatabase />
          </div>
          <div className="stat-content">
            <h3>{stats.totalActions.toLocaleString()}</h3>
            <p>Total Actions</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#10b981' }}>
            <FaClock />
          </div>
          <div className="stat-content">
            <h3>{stats.todayActions}</h3>
            <p>Today's Actions</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#ef4444' }}>
            <FaExclamationTriangle />
          </div>
          <div className="stat-content">
            <h3>{stats.criticalEvents}</h3>
            <p>Critical Events</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: '#8b5cf6' }}>
            <FaUser />
          </div>
          <div className="stat-content">
            <h3>{stats.uniqueUsers}</h3>
            <p>Active Users</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="audit-filters">
        <div className="filter-row">
          <div className="search-box">
            <FaSearch />
            <input
              type="text"
              placeholder="Search logs..."
              value={filters.searchQuery}
              onChange={(e) => setFilters({ ...filters, searchQuery: e.target.value })}
            />
          </div>

          <select
            value={filters.actionType}
            onChange={(e) => setFilters({ ...filters, actionType: e.target.value })}
          >
            <option value="all">All Actions</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="delete">Delete</option>
            <option value="view">View</option>
            <option value="export">Export</option>
            <option value="train">Train</option>
            <option value="sync">Sync</option>
          </select>

          <select
            value={filters.dateRange}
            onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
          >
            <option value="24hours">Last 24 Hours</option>
            <option value="7days">Last 7 Days</option>
            <option value="30days">Last 30 Days</option>
            <option value="90days">Last 90 Days</option>
            <option value="all">All Time</option>
          </select>

          <button onClick={handleExport} className="btn-export">
            <FaDownload /> Export CSV
          </button>
        </div>

        <div className="results-count">
          Showing {filteredLogs.length} of {auditLogs.length} events
        </div>
      </div>

      {/* Audit Log Timeline */}
      <div className="audit-timeline">
        {filteredLogs.length === 0 ? (
          <div className="no-logs">
            <FaHistory />
            <p>No audit logs found matching your filters</p>
          </div>
        ) : (
          filteredLogs.map((log) => (
            <div key={log.id} className={`audit-entry severity-${log.severity}`}>
              <div className="entry-header">
                <div className="entry-left">
                  <div className={`severity-indicator ${log.severity}`}>
                    {getSeverityIcon(log.severity)}
                  </div>
                  <div className="action-icon">
                    {getActionIcon(log.action)}
                  </div>
                  <div className="entry-info">
                    <h3>{log.description}</h3>
                    <div className="entry-meta">
                      <span className="meta-item">
                        <FaUser /> {log.user}
                      </span>
                      <span className="meta-item">
                        <FaClock /> {formatTimestamp(log.timestamp)}
                      </span>
                      <span className="meta-item">
                        <FaShieldAlt /> {log.ipAddress}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="entry-right">
                  <span className={`action-badge ${log.action}`}>
                    {log.action}
                  </span>
                  <span className="entity-badge">
                    {log.entity.replace('_', ' ')}
                  </span>
                </div>
              </div>
              
              {log.metadata && (
                <div className="entry-details">
                  <div className="detail-item">
                    <strong>Entity ID:</strong> {log.entityId}
                  </div>
                  {log.metadata.duration && (
                    <div className="detail-item">
                      <strong>Duration:</strong> {log.metadata.duration}ms
                    </div>
                  )}
                  {log.metadata.changes && (
                    <div className="detail-item">
                      <strong>Changes:</strong> {log.metadata.changes} fields modified
                    </div>
                  )}
                  <div className="detail-item">
                    <strong>Status:</strong>
                    <span className={log.metadata.success ? 'status-success' : 'status-failed'}>
                      {log.metadata.success ? 'Success' : 'Failed'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AuditTrailViewer;
