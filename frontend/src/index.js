import 'aframe';          // Loads and defines the global AFRAME object
import 'aframe-extras';   // Executes the AFRAME components that rely on the global AFRAME objectimport React from 'react';
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);