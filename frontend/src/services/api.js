/**
 * API Service Layer - Centralized API communication
 * Handles all backend API endpoints
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ============================================
// INCIDENT ENDPOINTS
// ============================================

export const incidentService = {
  // Process a new incident (primary endpoint)
  processIncident: async (incidentData) => {
    const response = await api.post('/api/process-incident', incidentData);
    return response.data;
  },

  // List incidents with filters
  listIncidents: async (filters = {}) => {
    const response = await api.get('/api/incidents/', { params: filters });
    return response.data;
  },

  // Get specific incident
  getIncident: async (incidentId) => {
    const response = await api.get(`/api/incidents/${incidentId}`);
    return response.data;
  },

  // Search incidents
  searchIncidents: async (query) => {
    const response = await api.post('/api/incidents/search', { query });
    return response.data;
  },

  // Submit feedback for incident
  submitFeedback: async (incidentId, feedbackData) => {
    const response = await api.post(`/api/incidents/${incidentId}/feedback`, feedbackData);
    return response.data;
  },

  // Find similar incidents
  findSimilar: async (incidentId) => {
    const response = await api.get(`/api/incidents/${incidentId}/similar`);
    return response.data;
  },

  // Get incident statistics
  getStats: async () => {
    const response = await api.get('/api/incidents/stats/summary');
    return response.data;
  },
};

// ============================================
// KNOWLEDGE BASE ENDPOINTS
// ============================================

export const knowledgeService = {
  // List knowledge articles
  listArticles: async (filters = {}) => {
    const response = await api.get('/api/knowledge/articles', { params: filters });
    return response.data;
  },

  // Create article
  createArticle: async (articleData) => {
    const response = await api.post('/api/knowledge/articles', articleData);
    return response.data;
  },

  // Get article
  getArticle: async (articleId) => {
    const response = await api.get(`/api/knowledge/articles/${articleId}`);
    return response.data;
  },

  // Update article
  updateArticle: async (articleId, articleData) => {
    const response = await api.put(`/api/knowledge/articles/${articleId}`, articleData);
    return response.data;
  },

  // Delete article
  deleteArticle: async (articleId) => {
    const response = await api.delete(`/api/knowledge/articles/${articleId}`);
    return response.data;
  },

  // Search knowledge base
  search: async (query) => {
    const response = await api.get('/api/knowledge/search', { params: { query } });
    return response.data;
  },

  // Hybrid search (enhanced - NEW)
  hybridSearch: async (searchData) => {
    const response = await api.post('/api/knowledge/hybrid-search', searchData);
    return response.data;
  },

  // Get knowledge stats
  getStats: async () => {
    const response = await api.get('/api/knowledge/stats');
    return response.data;
  },

  // Sync with vector store
  sync: async () => {
    const response = await api.post('/api/knowledge/sync');
    return response.data;
  },
};

// ============================================
// ANALYTICS ENDPOINTS
// ============================================

export const analyticsService = {
  // Get current metrics
  getMetrics: async () => {
    const response = await api.get('/api/analytics/metrics');
    return response.data;
  },

  // Get trend data
  getTrends: async (days = 7) => {
    const response = await api.get('/api/analytics/trends', { params: { days } });
    return response.data;
  },

  // Get performance metrics
  getPerformance: async () => {
    const response = await api.get('/api/analytics/performance');
    return response.data;
  },

  // Get feedback stats
  getFeedbackStats: async () => {
    const response = await api.get('/api/analytics/feedback-stats');
    return response.data;
  },

  // Get resource usage
  getResourceUsage: async () => {
    const response = await api.get('/api/analytics/resource-usage');
    return response.data;
  },
};

// ============================================
// AGENT MANAGEMENT ENDPOINTS
// ============================================

export const agentService = {
  // Get all agents status
  getStatus: async () => {
    const response = await api.get('/api/agents/status');
    return response.data;
  },

  // Get RAG agent stats
  getRAGStats: async () => {
    const response = await api.get('/api/agents/rag/stats');
    return response.data;
  },

  // Get CAG agent stats
  getCAGStats: async () => {
    const response = await api.get('/api/agents/cag/stats');
    return response.data;
  },

  // Get enhanced CAG stats (NEW)
  getEnhancedCAGStats: async () => {
    const response = await api.get('/api/agents/cag/enhanced-stats');
    return response.data;
  },

  // Get predictor stats
  getPredictorStats: async () => {
    const response = await api.get('/api/agents/predictive/stats');
    return response.data;
  },

  // Manually trigger orchestration
  orchestrate: async (incidentData) => {
    const response = await api.post('/api/agents/orchestrate', incidentData);
    return response.data;
  },

  // Trigger agent training
  trainAgent: async (agentName) => {
    const response = await api.post(`/api/agents/train/${agentName}`);
    return response.data;
  },

  // Get agent configuration
  getConfig: async () => {
    const response = await api.get('/api/agents/config');
    return response.data;
  },
};

// ============================================
// SYSTEM ENDPOINTS
// ============================================

export const systemService = {
  // Get system information
  getInfo: async () => {
    const response = await api.get('/');
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  // Get Prometheus metrics
  getPrometheusMetrics: async () => {
    const response = await api.get('/metrics');
    return response.data;
  },
};

// ============================================
// LEARNING PIPELINE ENDPOINTS (NEW)
// ============================================

export const learningService = {
  // Get learning statistics
  getStats: async () => {
    const response = await api.get('/api/learning/stats');
    return response.data;
  },

  // Get adaptive parameters
  getParameters: async () => {
    const response = await api.get('/api/learning/parameters');
    return response.data;
  },

  // Get error patterns
  getErrorPatterns: async () => {
    const response = await api.get('/api/learning/error-patterns');
    return response.data;
  },
};

// ============================================
// KNOWLEDGE GRAPH ENDPOINTS (NEW)
// ============================================

export const graphService = {
  // Get knowledge graph data
  getGraph: async () => {
    const response = await api.get('/api/graph/data');
    return response.data;
  },

  // Get related incidents
  getRelatedIncidents: async (incidentId, depth = 2) => {
    const response = await api.get(`/api/graph/related/${incidentId}`, {
      params: { depth }
    });
    return response.data;
  },

  // Get system patterns
  getPatterns: async () => {
    const response = await api.get('/api/graph/patterns');
    return response.data;
  },

  // Export graph as JSON
  exportGraph: async () => {
    const response = await api.get('/api/graph/export');
    return response.data;
  },
};

// ============================================
// AUDIT TRAIL ENDPOINTS (NEW)
// ============================================

export const auditService = {
  // Query audit entries
  queryEntries: async (filters = {}) => {
    const response = await api.get('/api/audit/trail', { params: filters });
    return response.data;
  },

  // Get compliance report
  getReport: async (startDate, endDate) => {
    const response = await api.get('/api/audit/report', {
      params: { start_date: startDate, end_date: endDate }
    });
    return response.data;
  },

  // Verify audit integrity
  verifyIntegrity: async (entryId) => {
    const response = await api.get(`/api/audit/verify/${entryId}`);
    return response.data;
  },
};

// ============================================
// CIRCUIT BREAKER ENDPOINTS (NEW)
// ============================================

export const circuitBreakerService = {
  // Get circuit breaker status
  getStatus: async () => {
    const response = await api.get('/api/circuit-breakers/status');
    return response.data;
  },

  // Reset circuit breaker
  reset: async (breakerName) => {
    const response = await api.post(`/api/circuit-breakers/${breakerName}/reset`);
    return response.data;
  },
};

export default api;
