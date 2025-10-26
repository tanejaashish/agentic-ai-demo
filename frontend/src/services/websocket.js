/**
 * WebSocket Service - Disabled for demo
 * This version gracefully handles the lack of WebSocket connection
 * All functionality continues to work via REST API
 */

class WebSocketService {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.listeners = new Map();
    console.log('WebSocket service initialized (disabled mode - using REST API only)');
  }

  /**
   * Connect to WebSocket server (disabled - no-op)
   */
  connect() {
    console.log('WebSocket disabled - using REST API polling instead');
    // Don't actually connect, just return
    return null;
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    // No-op
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
   * Emit event to listeners (internal use)
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
   * Send message to server (disabled - no-op)
   */
  send(event, data) {
    // No-op - WebSocket disabled
    console.debug('WebSocket send skipped (disabled mode)');
  }

  /**
   * Request metrics update (disabled - no-op)
   */
  requestMetrics() {
    // No-op
  }

  /**
   * Subscribe to specific incident updates (disabled - no-op)
   */
  subscribeToIncident(incidentId) {
    // No-op
  }

  /**
   * Unsubscribe from incident updates (disabled - no-op)
   */
  unsubscribeFromIncident(incidentId) {
    // No-op
  }

  /**
   * Check if connected
   */
  isConnected() {
    return false;
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService;