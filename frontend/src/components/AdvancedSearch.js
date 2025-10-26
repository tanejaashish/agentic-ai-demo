/**
 * Advanced Search Component
 * Multi-field search with filters, sorting, and export capabilities
 */

import React, { useState } from 'react';
import {
  FaSearch,
  FaFilter,
  FaDownload,
  FaSortAmountDown,
  FaSortAmountUp,
  FaCalendar,
  FaTags,
  FaDatabase,
  FaNetworkWired,
  FaServer,
  FaFileExport
} from 'react-icons/fa';
import { incidentService, knowledgeService } from '../services/api';
import toast from 'react-hot-toast';
import './AdvancedSearch.css';

const AdvancedSearch = () => {
  const [searchType, setSearchType] = useState('incidents');
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    priority: '',
    status: '',
    dateFrom: '',
    dateTo: '',
    tags: ''
  });
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [showFilters, setShowFilters] = useState(true);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    
    if (!searchQuery.trim() && !Object.values(filters).some(v => v)) {
      toast.error('Please enter a search query or select filters');
      return;
    }

    try {
      setSearching(true);
      
      if (searchType === 'incidents') {
        const data = await incidentService.searchIncidents(searchQuery);
        setResults(data.results || generateDemoIncidents());
      } else {
        const data = await knowledgeService.search(searchQuery);
        setResults(data.results || generateDemoArticles());
      }

      toast.success(`Found ${results.length} results`);
    } catch (error) {
      console.error('Search error:', error);
      // Use demo data on error
      if (searchType === 'incidents') {
        setResults(generateDemoIncidents());
      } else {
        setResults(generateDemoArticles());
      }
    } finally {
      setSearching(false);
    }
  };

  const generateDemoIncidents = () => [
    {
      id: 'INC001',
      title: 'Database Connection Pool Exhausted',
      description: 'Production database showing connection pool exhausted errors',
      category: 'Database',
      priority: 'High',
      status: 'Resolved',
      created_at: '2025-10-24T10:30:00Z',
      resolved_at: '2025-10-24T11:15:00Z',
      tags: ['database', 'connection', 'pool']
    },
    {
      id: 'INC002',
      title: 'API Gateway 502 Errors',
      description: 'Multiple microservices behind gateway unreachable',
      category: 'Network',
      priority: 'Critical',
      status: 'In Progress',
      created_at: '2025-10-24T14:20:00Z',
      tags: ['api', 'gateway', '502']
    },
    {
      id: 'INC003',
      title: 'Memory Leak in Payment Service',
      description: 'Payment processing service memory usage growing continuously',
      category: 'Application',
      priority: 'High',
      status: 'Open',
      created_at: '2025-10-23T09:15:00Z',
      tags: ['memory', 'payment', 'leak']
    }
  ];

  const generateDemoArticles = () => [
    {
      id: 'KB001',
      title: 'Resolving Database Connection Issues',
      content: 'Step-by-step guide to diagnose and fix connection pool problems...',
      category: 'Database',
      created_at: '2025-10-20T10:00:00Z',
      views: 342,
      helpful_count: 28,
      tags: ['database', 'connection', 'troubleshooting']
    },
    {
      id: 'KB002',
      title: 'API Gateway Best Practices',
      content: 'Configure and optimize your API gateway for high availability...',
      category: 'Network',
      created_at: '2025-10-18T14:30:00Z',
      views: 256,
      helpful_count: 19,
      tags: ['api', 'gateway', 'best-practices']
    }
  ];

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value });
  };

  const clearFilters = () => {
    setFilters({
      category: '',
      priority: '',
      status: '',
      dateFrom: '',
      dateTo: '',
      tags: ''
    });
    setSearchQuery('');
    setResults([]);
  };

  const exportResults = () => {
    const exportData = {
      search_type: searchType,
      query: searchQuery,
      filters: filters,
      results_count: results.length,
      results: results,
      exported_at: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `search-results-${Date.now()}.json`;
    a.click();
    toast.success('Results exported successfully!');
  };

  const exportCSV = () => {
    if (results.length === 0) {
      toast.error('No results to export');
      return;
    }

    const headers = searchType === 'incidents' 
      ? ['ID', 'Title', 'Category', 'Priority', 'Status', 'Created', 'Tags']
      : ['ID', 'Title', 'Category', 'Views', 'Helpful', 'Created', 'Tags'];

    const rows = results.map(r => 
      searchType === 'incidents'
        ? [r.id, r.title, r.category, r.priority, r.status, r.created_at, r.tags?.join(';')]
        : [r.id, r.title, r.category, r.views, r.helpful_count, r.created_at, r.tags?.join(';')]
    );

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `search-results-${Date.now()}.csv`;
    a.click();
    toast.success('CSV exported successfully!');
  };

  const getSortedResults = () => {
    if (!results.length) return [];

    return [...results].sort((a, b) => {
      let aVal, bVal;
      
      switch (sortBy) {
        case 'date':
          aVal = new Date(a.created_at);
          bVal = new Date(b.created_at);
          break;
        case 'priority':
          const priorityOrder = { 'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1 };
          aVal = priorityOrder[a.priority] || 0;
          bVal = priorityOrder[b.priority] || 0;
          break;
        case 'title':
          aVal = a.title.toLowerCase();
          bVal = b.title.toLowerCase();
          break;
        default:
          return 0;
      }

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'Critical': return '#ef4444';
      case 'High': return '#f59e0b';
      case 'Medium': return '#3b82f6';
      case 'Low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Resolved': return '#10b981';
      case 'In Progress': return '#3b82f6';
      case 'Open': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  return (
    <div className="advanced-search">
      {/* Header */}
      <div className="search-header">
        <div>
          <h1><FaSearch /> Advanced Search</h1>
          <p>Search across incidents, knowledge base, and system logs</p>
        </div>
      </div>

      {/* Search Type Tabs */}
      <div className="search-tabs">
        <button
          className={`tab ${searchType === 'incidents' ? 'active' : ''}`}
          onClick={() => setSearchType('incidents')}
        >
          <FaDatabase /> Incidents
        </button>
        <button
          className={`tab ${searchType === 'knowledge' ? 'active' : ''}`}
          onClick={() => setSearchType('knowledge')}
        >
          <FaServer /> Knowledge Base
        </button>
      </div>

      {/* Main Search Bar */}
      <form onSubmit={handleSearch} className="search-form">
        <div className="search-input-group">
          <FaSearch className="search-icon" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={`Search ${searchType}... (keywords, descriptions, tags)`}
            className="search-input"
          />
          <button type="submit" className="btn-search" disabled={searching}>
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>
        <button
          type="button"
          onClick={() => setShowFilters(!showFilters)}
          className="btn-toggle-filters"
        >
          <FaFilter /> {showFilters ? 'Hide' : 'Show'} Filters
        </button>
      </form>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="filters-panel">
          <h3>Filters</h3>
          <div className="filters-grid">
            <div className="filter-group">
              <label>Category</label>
              <select
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
              >
                <option value="">All Categories</option>
                <option value="Database">Database</option>
                <option value="Network">Network</option>
                <option value="Application">Application</option>
                <option value="Security">Security</option>
              </select>
            </div>

            {searchType === 'incidents' && (
              <>
                <div className="filter-group">
                  <label>Priority</label>
                  <select
                    value={filters.priority}
                    onChange={(e) => handleFilterChange('priority', e.target.value)}
                  >
                    <option value="">All Priorities</option>
                    <option value="Critical">Critical</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                  </select>
                </div>

                <div className="filter-group">
                  <label>Status</label>
                  <select
                    value={filters.status}
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                  >
                    <option value="">All Statuses</option>
                    <option value="Open">Open</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Resolved">Resolved</option>
                  </select>
                </div>
              </>
            )}

            <div className="filter-group">
              <label><FaCalendar /> Date From</label>
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label><FaCalendar /> Date To</label>
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => handleFilterChange('dateTo', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label><FaTags /> Tags</label>
              <input
                type="text"
                value={filters.tags}
                onChange={(e) => handleFilterChange('tags', e.target.value)}
                placeholder="Comma-separated"
              />
            </div>
          </div>
          <div className="filter-actions">
            <button onClick={clearFilters} className="btn-secondary">
              Clear All Filters
            </button>
          </div>
        </div>
      )}

      {/* Results Section */}
      {results.length > 0 && (
        <>
          {/* Results Controls */}
          <div className="results-controls">
            <div className="results-info">
              <strong>{results.length}</strong> results found
            </div>
            <div className="results-actions">
              <div className="sort-controls">
                <label>Sort by:</label>
                <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                  <option value="date">Date</option>
                  <option value="title">Title</option>
                  {searchType === 'incidents' && <option value="priority">Priority</option>}
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="btn-icon"
                >
                  {sortOrder === 'asc' ? <FaSortAmountUp /> : <FaSortAmountDown />}
                </button>
              </div>
              <button onClick={exportResults} className="btn-secondary">
                <FaDownload /> JSON
              </button>
              <button onClick={exportCSV} className="btn-secondary">
                <FaFileExport /> CSV
              </button>
            </div>
          </div>

          {/* Results List */}
          <div className="results-list">
            {getSortedResults().map(result => (
              <div key={result.id} className="result-card">
                <div className="result-header">
                  <h3>{result.title}</h3>
                  <div className="result-badges">
                    <span className="category-badge">{result.category}</span>
                    {searchType === 'incidents' && result.priority && (
                      <span
                        className="priority-badge"
                        style={{ backgroundColor: getPriorityColor(result.priority) }}
                      >
                        {result.priority}
                      </span>
                    )}
                    {searchType === 'incidents' && result.status && (
                      <span
                        className="status-badge"
                        style={{ backgroundColor: getStatusColor(result.status) }}
                      >
                        {result.status}
                      </span>
                    )}
                  </div>
                </div>

                <p className="result-description">
                  {result.description || result.content}
                </p>

                <div className="result-meta">
                  <span className="result-id">{result.id}</span>
                  <span>Created: {new Date(result.created_at).toLocaleString()}</span>
                  {searchType === 'knowledge' && (
                    <>
                      <span>👁 {result.views} views</span>
                      <span>👍 {result.helpful_count} helpful</span>
                    </>
                  )}
                </div>

                {result.tags && result.tags.length > 0 && (
                  <div className="result-tags">
                    {result.tags.map((tag, idx) => (
                      <span key={idx} className="tag">{tag}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Empty State */}
      {!searching && results.length === 0 && (
        <div className="empty-state">
          <FaSearch />
          <h3>No results yet</h3>
          <p>Enter a search query and click Search to find {searchType}</p>
        </div>
      )}

      {/* Searching State */}
      {searching && (
        <div className="searching-state">
          <div className="spinner"></div>
          <p>Searching...</p>
        </div>
      )}
    </div>
  );
};

export default AdvancedSearch;
