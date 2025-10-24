/**
 * Main App Component - Enhanced Frontend with Routing
 * Production-Ready Agentic AI System v2.0
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Components
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import IncidentProcessor from './components/IncidentProcessor';
import MetricsDashboard from './components/MetricsDashboard';
import AgentStatusPanel from './components/AgentStatusPanel';
import KnowledgeGraphVisualizer from './components/KnowledgeGraphVisualizer';

// Placeholder components for pages not yet fully implemented
import PlaceholderPage from './components/PlaceholderPage';

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
            <Route path="/" element={<Dashboard />} />
            <Route path="/process" element={<IncidentProcessor />} />
            <Route path="/metrics" element={<MetricsDashboard />} />
            <Route path="/agents" element={<AgentStatusPanel />} />
            <Route path="/knowledge" element={<PlaceholderPage title="Knowledge Base Manager" />} />
            <Route path="/graph" element={<KnowledgeGraphVisualizer />} />
            <Route path="/audit" element={<PlaceholderPage title="Audit Trail Viewer" />} />
            <Route path="/learning" element={<PlaceholderPage title="Learning Statistics" />} />
            <Route path="/health" element={<PlaceholderPage title="System Health Monitor" />} />
            <Route path="/search" element={<PlaceholderPage title="Advanced Search" />} />
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
