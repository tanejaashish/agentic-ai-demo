/**
 * KnowledgeGraphVisualizer Component - Interactive knowledge graph visualization
 */

import React, { useState, useEffect, useRef } from 'react';
import { ForceGraph2D } from 'react-force-graph';
import { FaProjectDiagram, FaExpand } from 'react-icons/fa';
import { graphService } from '../services/api';
import './KnowledgeGraphVisualizer.css';

const KnowledgeGraphVisualizer = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const graphRef = useRef();

  useEffect(() => {
    loadGraphData();
  }, []);

  const loadGraphData = async () => {
    try {
      setLoading(true);
      const data = await graphService.getGraph();

      // Transform data for react-force-graph
      const nodes = data.nodes?.map(node => ({
        id: node.id,
        name: node.label,
        type: node.type,
        val: node.importance || 5,
        color: getNodeColor(node.type)
      })) || [];

      const links = data.edges?.map(edge => ({
        source: edge.from,
        target: edge.to,
        label: edge.relationship
      })) || [];

      setGraphData({ nodes, links });
    } catch (error) {
      console.error('Error loading graph:', error);
      // Create mock data for demo
      setGraphData({
        nodes: [
          { id: '1', name: 'Database Error', type: 'incident', val: 10, color: '#ef4444' },
          { id: '2', name: 'API Gateway', type: 'system', val: 8, color: '#3b82f6' },
          { id: '3', name: 'Connection Pool', type: 'component', val: 6, color: '#8b5cf6' },
        ],
        links: [
          { source: '1', target: '2', label: 'affects' },
          { source: '1', target: '3', label: 'causes' },
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const getNodeColor = (type) => {
    const colors = {
      incident: '#ef4444',
      system: '#3b82f6',
      component: '#8b5cf6',
      solution: '#10b981',
      team: '#f59e0b',
      error: '#f97316',
      default: '#6b7280'
    };
    return colors[type] || colors.default;
  };

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  if (loading) {
    return (
      <div className="graph-loading">
        <FaProjectDiagram className="loading-icon" />
        <p>Loading Knowledge Graph...</p>
      </div>
    );
  }

  return (
    <div className="knowledge-graph-visualizer">
      <div className="graph-header">
        <h1><FaProjectDiagram /> Knowledge Graph</h1>
        <button onClick={() => graphRef.current?.zoomToFit()} className="zoom-btn">
          <FaExpand /> Fit View
        </button>
      </div>

      <div className="graph-container">
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeLabel="name"
          nodeColor="color"
          nodeRelSize={6}
          linkLabel="label"
          linkDirectionalArrowLength={3.5}
          linkDirectionalArrowRelPos={1}
          onNodeClick={handleNodeClick}
          backgroundColor="#f9fafb"
          linkColor={() => '#d1d5db'}
          width={1200}
          height={600}
        />
      </div>

      {selectedNode && (
        <div className="node-details">
          <h3>Node Details</h3>
          <div className="detail-item">
            <span>Name:</span>
            <strong>{selectedNode.name}</strong>
          </div>
          <div className="detail-item">
            <span>Type:</span>
            <strong>{selectedNode.type}</strong>
          </div>
          <div className="detail-item">
            <span>ID:</span>
            <strong>{selectedNode.id}</strong>
          </div>
          <button onClick={() => setSelectedNode(null)} className="close-btn">
            Close
          </button>
        </div>
      )}

      <div className="graph-legend">
        <h4>Legend</h4>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#ef4444' }}></span>
            <span>Incident</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#3b82f6' }}></span>
            <span>System</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#8b5cf6' }}></span>
            <span>Component</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#10b981' }}></span>
            <span>Solution</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraphVisualizer;
