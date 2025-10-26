/**
 * Main App Component - Enhanced Frontend with Routing
 * Production-Ready Agentic AI System v2.0
 * UPDATED: All new components linked
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Core Components
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import IncidentProcessor from './components/IncidentProcessor';
import MetricsDashboard from './components/MetricsDashboard';

// Agent Components
import AgentStatusPanel from './components/AgentStatusPanel';
import AgentManagement from './components/AgentManagement';

// Knowledge & Graph Components
import KnowledgeBaseManager from './components/KnowledgeBaseManager';
import KnowledgeGraphVisualizer from './components/KnowledgeGraphVisualizer';

// Monitoring & Search Components
import SystemHealthMonitor from './components/SystemHealthMonitor';
import AdvancedSearch from './components/AdvancedSearch';
import AuditTrailViewer from './components/AuditTrailViewer';															 
import LearningStatistics from './components/LearningStatistics';

// Placeholder components for pages not yet fully implemented
//import PlaceholderPage from './components/PlaceholderPage';

import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Navigation />

        <main className="main-content">
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />

          <Routes>
            {/* Main Pages */}
            <Route path="/" element={<Dashboard />} />
            <Route path="/incidents" element={<IncidentProcessor />} />
            <Route path="/process" element={<IncidentProcessor />} />
            <Route path="/metrics" element={<MetricsDashboard />} />
            
            {/* Agent Management - NEW! */}
            <Route path="/agents" element={<AgentManagement />} />
            
            {/* Knowledge Base - NEW! */}
            <Route path="/knowledge" element={<KnowledgeBaseManager />} />
            <Route path="/knowledge-base" element={<KnowledgeBaseManager />} />
            
            {/* Knowledge Graph - UPDATED! */}
            <Route path="/graph" element={<KnowledgeGraphVisualizer />} />
            <Route path="/knowledge-graph" element={<KnowledgeGraphVisualizer />} />
            
            {/* System Health - NEW! */}
            <Route path="/health" element={<SystemHealthMonitor />} />
            <Route path="/system-health" element={<SystemHealthMonitor />} />
            
            {/* Advanced Search - NEW! */}
            <Route path="/search" element={<AdvancedSearch />} />
            <Route path="/advanced-search" element={<AdvancedSearch />} />
            
            {/* Audit & Learning */}
            <Route path="/audit" element={<AuditTrailViewer />} />
            <Route path="/audit-trail" element={<AuditTrailViewer />} />
            <Route path="/learning" element={<LearningStatistics />} />
            <Route path="/learning-stats" element={<LearningStatistics />} />
            
            {/* 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

// 404 Not Found Component
const NotFound = () => (
  <div className="not-found">
    <h1>404 - Page Not Found</h1>
    <p>The page you're looking for doesn't exist.</p>
    <a href="/">Return to Dashboard</a>
  </div>
);

export default App;