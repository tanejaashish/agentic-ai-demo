/**
 * Enhanced Knowledge Graph Visualizer Component - 2D Version
 * Interactive 2D graph visualization with detailed insights
 * DEMO-READY: No external dependencies required
 */

import React, { useState, useEffect, useCallback } from 'react';
import { graphService } from '../services/api';
import { 
  FaProjectDiagram, 
  FaSync, 
  FaExpand, 
  FaCompress,
  FaDownload,
  FaInfoCircle,
  FaSearch,
  FaArrowRight
} from 'react-icons/fa';
import './KnowledgeGraphVisualizer.css';

const KnowledgeGraphVisualizer = () => {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [patterns, setPatterns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredNodes, setFilteredNodes] = useState([]);

  const loadGraphData = useCallback(async () => {
    try {
      setLoading(true);
      const [graphRes, patternsRes] = await Promise.all([
        graphService.getGraph(),
        graphService.getPatterns()
      ]);

      setGraphData({
        nodes: graphRes.nodes || [],
        edges: graphRes.edges || []
      });
      
      setPatterns(patternsRes.patterns || []);
      setFilteredNodes(graphRes.nodes || []);
    } catch (error) {
      console.error('Error loading graph:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  useEffect(() => {
    if (!searchQuery) {
      setFilteredNodes(graphData.nodes);
      return;
    }

    const filtered = graphData.nodes.filter(node =>
      node.label.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setFilteredNodes(filtered);
  }, [searchQuery, graphData.nodes]);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  const handleRefresh = () => {
    loadGraphData();
  };

  const handleExport = async () => {
    try {
      const data = await graphService.exportGraph();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `knowledge-graph-${Date.now()}.json`;
      a.click();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const getConnectedNodes = (nodeId) => {
    const connected = new Set();
    graphData.edges.forEach(edge => {
      if (edge.source === nodeId) {
        connected.add(edge.target);
      }
      if (edge.target === nodeId) {
        connected.add(edge.source);
      }
    });
    return Array.from(connected);
  };

  const getNodesByType = (type) => {
    return graphData.nodes.filter(n => n.type === type);
  };

  if (loading) {
    return (
      <div className="graph-loading">
        <FaProjectDiagram className="loading-icon spinning" />
        <p>Building Knowledge Graph...</p>
      </div>
    );
  }

  return (
    <div className={`knowledge-graph-container ${fullscreen ? 'fullscreen' : ''}`}>
      {/* Header */}
      <div className="graph-header">
        <div>
          <h1><FaProjectDiagram /> Knowledge Graph</h1>
          <p>Interactive visualization of incident relationships and patterns</p>
        </div>
        <div className="graph-actions">
          <div className="search-box">
            <FaSearch />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button onClick={handleRefresh} className="action-btn" title="Refresh">
            <FaSync />
          </button>
          <button onClick={handleExport} className="action-btn" title="Export">
            <FaDownload />
          </button>
          <button 
            onClick={() => setFullscreen(!fullscreen)} 
            className="action-btn"
            title={fullscreen ? "Exit Fullscreen" : "Fullscreen"}
          >
            {fullscreen ? <FaCompress /> : <FaExpand />}
          </button>
        </div>
      </div>

      <div className="graph-content">
        {/* Main Graph - Network Visualization */}
        <div className="graph-viewport">
          <div className="network-graph">
            {/* Categories Layer */}
            <div className="graph-layer categories">
              <h3 className="layer-title">Categories</h3>
              <div className="nodes-container">
                {getNodesByType('category').map(node => (
                  <div
                    key={node.id}
                    className={`graph-node category-node ${selectedNode?.id === node.id ? 'selected' : ''}`}
                    style={{ backgroundColor: node.color }}
                    onClick={() => handleNodeClick(node)}
                  >
                    <div className="node-label">{node.label}</div>
                    <div className="node-count">
                      {graphData.edges.filter(e => e.source === node.id).length} incidents
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Incidents Layer */}
            <div className="graph-layer incidents">
              <h3 className="layer-title">Incidents</h3>
              <div className="nodes-container">
                {getNodesByType('incident').map(node => (
                  <div
                    key={node.id}
                    className={`graph-node incident-node ${selectedNode?.id === node.id ? 'selected' : ''}`}
                    style={{ borderColor: node.color }}
                    onClick={() => handleNodeClick(node)}
                  >
                    <div className="node-label">{node.label}</div>
                    <div className="node-connections">
                      {getConnectedNodes(node.id).length} connections
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Solutions Layer */}
            <div className="graph-layer solutions">
              <h3 className="layer-title">Solutions</h3>
              <div className="nodes-container">
                {getNodesByType('solution').map(node => (
                  <div
                    key={node.id}
                    className={`graph-node solution-node ${selectedNode?.id === node.id ? 'selected' : ''}`}
                    style={{ backgroundColor: node.color }}
                    onClick={() => handleNodeClick(node)}
                  >
                    <div className="node-label">{node.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Systems Layer */}
            <div className="graph-layer systems">
              <h3 className="layer-title">Affected Systems</h3>
              <div className="nodes-container">
                {getNodesByType('system').map(node => (
                  <div
                    key={node.id}
                    className={`graph-node system-node ${selectedNode?.id === node.id ? 'selected' : ''}`}
                    style={{ backgroundColor: node.color }}
                    onClick={() => handleNodeClick(node)}
                  >
                    <div className="node-label">{node.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Connection Flow Diagram */}
          <div className="connection-flow">
            <div className="flow-arrow">
              <FaArrowRight /> Categories contain Incidents
            </div>
            <div className="flow-arrow">
              <FaArrowRight /> Incidents affect Systems
            </div>
            <div className="flow-arrow">
              <FaArrowRight /> Solutions resolve Incidents
            </div>
          </div>

          {/* Demo Notes Overlay */}
          <div className="demo-notes">
            <div className="note-badge">
              <FaInfoCircle /> Demo Features
            </div>
            <ul className="note-list">
              <li>🎯 Click nodes to explore relationships</li>
              <li>🔍 Search to filter specific patterns</li>
              <li>📊 View connection statistics</li>
              <li>🔗 Understand incident → solution flow</li>
              <li>💾 Export graph data as JSON</li>
            </ul>
          </div>
        </div>

        {/* Side Panel */}
        <div className="graph-sidebar">
          {/* Legend */}
          <div className="graph-card">
            <h3>Graph Legend</h3>
            <div className="legend-items">
              <div className="legend-item">
                <span className="legend-dot" style={{ backgroundColor: '#3b82f6' }}></span>
                <span>Categories ({getNodesByType('category').length})</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot" style={{ backgroundColor: '#ef4444' }}></span>
                <span>Incidents ({getNodesByType('incident').length})</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot" style={{ backgroundColor: '#8b5cf6' }}></span>
                <span>Solutions ({getNodesByType('solution').length})</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot" style={{ backgroundColor: '#ec4899' }}></span>
                <span>Systems ({getNodesByType('system').length})</span>
              </div>
            </div>
            
            <div className="legend-connections">
              <h4>Relationships</h4>
              <div className="relationship-types">
                <div className="relationship-item">
                  <span className="relationship-badge contains">Contains</span>
                  <span>Category → Incident</span>
                </div>
                <div className="relationship-item">
                  <span className="relationship-badge resolves">Resolves</span>
                  <span>Incident → Solution</span>
                </div>
                <div className="relationship-item">
                  <span className="relationship-badge affects">Affects</span>
                  <span>Incident → System</span>
                </div>
                <div className="relationship-item">
                  <span className="relationship-badge cooccurs">Co-occurs</span>
                  <span>Incident ↔ Incident</span>
                </div>
              </div>
            </div>
          </div>

          {/* Selected Node Info */}
          {selectedNode && (
            <div className="graph-card selected-node-card">
              <h3>Selected Node</h3>
              <div className="node-details">
                <div className="node-header">
                  <span 
                    className="node-type-badge"
                    style={{ backgroundColor: selectedNode.color }}
                  >
                    {selectedNode.type}
                  </span>
                  <h4>{selectedNode.label}</h4>
                </div>
                <div className="node-stats">
                  <div className="stat-item">
                    <span>ID:</span>
                    <strong>{selectedNode.id}</strong>
                  </div>
                  <div className="stat-item">
                    <span>Connections:</span>
                    <strong>{getConnectedNodes(selectedNode.id).length}</strong>
                  </div>
                  <div className="stat-item">
                    <span>Type:</span>
                    <strong>{selectedNode.type}</strong>
                  </div>
                </div>

                {/* Show connected nodes */}
                <div className="connected-nodes">
                  <h4>Connected To:</h4>
                  <div className="connected-list">
                    {getConnectedNodes(selectedNode.id).map(connId => {
                      const connNode = graphData.nodes.find(n => n.id === connId);
                      return connNode ? (
                        <div key={connId} className="connected-item">
                          <span 
                            className="connected-dot" 
                            style={{ backgroundColor: connNode.color }}
                          ></span>
                          <span>{connNode.label}</span>
                        </div>
                      ) : null;
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Patterns */}
          <div className="graph-card">
            <h3>Common Patterns</h3>
            <div className="patterns-list">
              {patterns.map(pattern => (
                <div key={pattern.id} className="pattern-item">
                  <h4>{pattern.name}</h4>
                  <div className="pattern-stats">
                    <span className="pattern-badge">
                      {pattern.frequency} occurrences
                    </span>
                    <span className="pattern-badge">
                      {Math.round(pattern.confidence * 100)}% confidence
                    </span>
                  </div>
                  <p className="pattern-incidents">
                    {pattern.incidents.join(' → ')}
                  </p>
                  <div className="pattern-metric">
                    Avg Resolution: {pattern.avg_resolution_time} mins
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Graph Statistics */}
          <div className="graph-card">
            <h3>Graph Statistics</h3>
            <div className="stats-grid">
              <div className="stat-box">
                <div className="stat-value">{graphData.nodes.length}</div>
                <div className="stat-label">Total Nodes</div>
              </div>
              <div className="stat-box">
                <div className="stat-value">{graphData.edges.length}</div>
                <div className="stat-label">Connections</div>
              </div>
              <div className="stat-box">
                <div className="stat-value">
                  {getNodesByType('incident').length}
                </div>
                <div className="stat-label">Incidents</div>
              </div>
              <div className="stat-box">
                <div className="stat-value">
                  {getNodesByType('solution').length}
                </div>
                <div className="stat-label">Solutions</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraphVisualizer;