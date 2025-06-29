import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Transfers from './pages/Transfers';
import TransferHistory from './pages/TransferHistory';
import Endpoints from './pages/Endpoints';
import TransferTemplates from './pages/TransferTemplates';
import Settings from './pages/Settings';
import Logs from './pages/Logs';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="container">
            <h1 className="logo">PBS Rclone MVP</h1>
            <ul className="nav-links">
              <li><Link to="/">Dashboard</Link></li>
              <li><Link to="/transfers">Transfers</Link></li>
              <li><Link to="/history">History</Link></li>
              <li><Link to="/endpoints">Endpoints</Link></li>
              <li><Link to="/transfer-templates">Transfer Templates</Link></li>
              <li><Link to="/logs">Logs</Link></li>
              <li><Link to="/settings">Settings</Link></li>
            </ul>
          </div>
        </nav>
        
        <main className="main-content">
          <div className="container">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/transfers" element={<Transfers />} />
              <Route path="/history" element={<TransferHistory />} />
              <Route path="/endpoints" element={<Endpoints />} />
              <Route path="/transfer-templates" element={<TransferTemplates />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;