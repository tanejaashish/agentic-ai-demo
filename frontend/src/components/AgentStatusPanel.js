/**
 * AgentStatusPanel Component - Detailed agent status and management
 */

import React, { useState, useEffect } from 'react';
import { FaRobot, FaSync, FaCog } from 'react-icons/fa';
import { agentService } from '../services/api';
import websocketService from '../services/websocket';
import './AgentStatusPanel.css';

const AgentStatusPanel = () => {
  const [agents, setAgents] = useState(null);
  const [ragStats, setRagStats] = useState(null);
  const [cagStats, setCagStats] = useState(null);
  const [predictorStats, setPredictorStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAgentData();
    websocketService.connect();

    const unsubscribe = websocketService.on('agent_status', (data) => {
      setAgents(prev => ({ ...prev, ...data }));
    });

    const interval = setInterval(loadAgentData, 30000);
    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, []);

  const loadAgentData = async () => {
    try {
      setLoading(true);
      const [status, rag, cag, predictor] = await Promise.all([
        agentService.getStatus(),
        agentService.getRAGStats(),
        agentService.getCAGStats(),
        agentService.getPredictorStats()
      ]);
      setAgents(status);
      setRagStats(rag);
      setCagStats(cag);
      setPredictorStats(predictor);
    } catch (error) {
      console.error('Error loading agent data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTrain = async (agentName) => {
    try {
      await agentService.trainAgent(agentName);
      alert(`Training initiated for ${agentName} agent`);
    } catch (error) {
      alert(`Failed to train ${agentName}: ${error.message}`);
    }
  };

  if (loading) {
    return <div className="agent-loading">Loading agent status...</div>;
  }

  return (
    <div className="agent-status-panel">
      <div className="panel-header">
        <h1><FaRobot /> Agent Status & Management</h1>
        <button onClick={loadAgentData} className="refresh-btn">
          <FaSync /> Refresh
        </button>
      </div>

      <div className="agents-grid">
        <div className="agent-detail-card">
          <h2>RAG Agent</h2>
          <div className="agent-stats">
            <div className="stat-item">
              <span>Queries Processed:</span>
              <strong>{ragStats?.total_queries || 0}</strong>
            </div>
            <div className="stat-item">
              <span>Avg Retrieval Time:</span>
              <strong>{ragStats?.avg_retrieval_time || 0}ms</strong>
            </div>
            <div className="stat-item">
              <span>Cache Hit Rate:</span>
              <strong>{ragStats?.cache_hit_rate || 0}%</strong>
            </div>
          </div>
          <button onClick={() => handleTrain('rag')} className="train-btn">
            <FaCog /> Train Model
          </button>
        </div>

        <div className="agent-detail-card">
          <h2>CAG Agent</h2>
          <div className="agent-stats">
            <div className="stat-item">
              <span>Refinements:</span>
              <strong>{cagStats?.total_refinements || 0}</strong>
            </div>
            <div className="stat-item">
              <span>Avg Improvement:</span>
              <strong>{cagStats?.avg_improvement || 0}%</strong>
            </div>
            <div className="stat-item">
              <span>Success Rate:</span>
              <strong>{cagStats?.success_rate || 0}%</strong>
            </div>
          </div>
          <button onClick={() => handleTrain('cag')} className="train-btn">
            <FaCog /> Train Model
          </button>
        </div>

        <div className="agent-detail-card">
          <h2>Predictor Agent</h2>
          <div className="agent-stats">
            <div className="stat-item">
              <span>Predictions:</span>
              <strong>{predictorStats?.total_predictions || 0}</strong>
            </div>
            <div className="stat-item">
              <span>Accuracy:</span>
              <strong>{predictorStats?.accuracy || 0}%</strong>
            </div>
            <div className="stat-item">
              <span>Avg Confidence:</span>
              <strong>{predictorStats?.avg_confidence || 0}%</strong>
            </div>
          </div>
          <button onClick={() => handleTrain('predictor')} className="train-btn">
            <FaCog /> Train Model
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentStatusPanel;
