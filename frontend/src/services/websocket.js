/**
 * WebSocket Service - Real-time communication
 * Handles WebSocket connections for live metrics and updates
 */

import { io } from 'socket.io-client';

const WS_URL = process.env.REACT_APP_WS_URL || 'http://localhost:8000';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.listeners = new Map();
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    if (this.socket && this.connected) {
      console.log('WebSocket already connected');
      return;
    }

    this.socket = io(WS_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.connected = true;
      this.emit('connection', { status: 'connected' });
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      this.connected = false;
      this.emit('connection', { status: 'disconnected' });
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.emit('connection', { status: 'error', error });
    });

    // Listen for metrics updates
    this.socket.on('metrics_update', (data) => {
      this.emit('metrics', data);
    });

    // Listen for agent status updates
    this.socket.on('agent_status', (data) => {
      this.emit('agent_status', data);
    });

    // Listen for incident updates
    this.socket.on('incident_update', (data) => {
      this.emit('incident_update', data);
    });

    // Listen for learning updates
    this.socket.on('learning_update', (data) => {
      this.emit('learning_update', data);
    });

    // Listen for alert notifications
    this.socket.on('alert', (data) => {
      this.emit('alert', data);
    });

    return this.socket;
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  /**
   * Subscribe to events
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    };
  }

  /**
   * Unsubscribe from events
   */
  off(event, callback) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * Emit event to listeners
   */
  emit(event, data) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Send message to server
   */
  send(event, data) {
    if (this.socket && this.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  /**
   * Request metrics update
   */
  requestMetrics() {
    this.send('request_metrics', {});
  }

  /**
   * Subscribe to specific incident updates
   */
  subscribeToIncident(incidentId) {
    this.send('subscribe_incident', { incident_id: incidentId });
  }

  /**
   * Unsubscribe from incident updates
   */
  unsubscribeFromIncident(incidentId) {
    this.send('unsubscribe_incident', { incident_id: incidentId });
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.connected;
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService;
