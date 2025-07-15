import { Routes, Route } from 'react-router-dom';
import AppShell from './components/Layout/AppShell';
import Dashboard from './pages/Dashboard';
import EndpointsPage from './pages/Endpoints';
import TransfersPage from './pages/Transfers';
import HistoryPage from './pages/History';
import TemplatesPage from './pages/Templates';
import LogsPage from './pages/Logs';
import SettingsPage from './pages/Settings';

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<Dashboard />} />
        <Route path="endpoints" element={<EndpointsPage />} />
        <Route path="transfers" element={<TransfersPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="templates" element={<TemplatesPage />} />
        <Route path="logs" element={<LogsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}

export default App