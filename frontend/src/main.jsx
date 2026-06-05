import React from 'react';
import ReactDOM from 'react-dom/client';
import EpiDashboard from './dashboard-v2/EpiDashboard.jsx';
import './dashboard-v2/index.css'; // Tailwind + Tremor (preflight)
import './styles/globals.css'; // estilos das páginas legadas (carrega depois para vencer o preflight)

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <EpiDashboard />
  </React.StrictMode>,
);
