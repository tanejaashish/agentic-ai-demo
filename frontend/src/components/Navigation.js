/**
 * Navigation Component - Main navigation bar
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  FaHome,
  FaRobot,
  FaChartLine,
  FaDatabase,
  FaProjectDiagram,
  FaFileAlt,
  FaBrain,
  FaHeartbeat,
  FaSearch
} from 'react-icons/fa';
import './Navigation.css';

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <FaHome /> },
    { path: '/process', label: 'Process Incident', icon: <FaRobot /> },
    { path: '/metrics', label: 'Metrics', icon: <FaChartLine /> },
    { path: '/agents', label: 'Agents', icon: <FaBrain /> },
    { path: '/knowledge', label: 'Knowledge Base', icon: <FaDatabase /> },
    { path: '/graph', label: 'Knowledge Graph', icon: <FaProjectDiagram /> },
    { path: '/audit', label: 'Audit Trail', icon: <FaFileAlt /> },
    { path: '/learning', label: 'Learning', icon: <FaBrain /> },
    { path: '/health', label: 'Health', icon: <FaHeartbeat /> },
    { path: '/search', label: 'Search', icon: <FaSearch /> }
  ];

  return (
    <nav className="navigation">
      <div className="nav-header">
        <FaRobot className="nav-logo" />
        <h2>Agentic AI</h2>
      </div>

      <div className="nav-items">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </Link>
        ))}
      </div>

      <div className="nav-footer">
        <div className="version-info">
          <span>Version 2.0</span>
          <span>Production Ready</span>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
