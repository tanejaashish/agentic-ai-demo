/**
 * PlaceholderPage Component - Placeholder for pages under development
 */

import React from 'react';
import { FaCog } from 'react-icons/fa';
import './PlaceholderPage.css';

const PlaceholderPage = ({ title, description }) => {
  return (
    <div className="placeholder-page">
      <FaCog className="placeholder-icon" />
      <h1>{title}</h1>
      <p>
        {description || 'This page is available in the backend API but the frontend UI is under development.'}
      </p>
      <div className="placeholder-info">
        <h3>Available Backend Endpoints:</h3>
        <ul>
          <li>All API endpoints are fully functional</li>
          <li>WebSocket connections for real-time updates</li>
          <li>Complete data models and validation</li>
        </ul>
        <p className="note">
          The UI for this feature will be completed in the next development phase.
          You can test the API directly using the Swagger docs at <code>/docs</code>
        </p>
      </div>
    </div>
  );
};

export default PlaceholderPage;
