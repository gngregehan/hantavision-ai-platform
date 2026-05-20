import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import StartupEvidenceLayer from './StartupEvidenceLayer.jsx';
import './styles.css';
import './startup-evidence.css';

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
    <StartupEvidenceLayer />
  </React.StrictMode>,
);
