import { Routes, Route } from 'react-router-dom';
import AppShell from './components/Layout/AppShell';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<Dashboard />} />
        <Route path="endpoints" element={<div>Endpoints Page (TODO)</div>} />
        <Route path="transfers" element={<div>Transfers Page (TODO)</div>} />
        <Route path="history" element={<div>History Page (TODO)</div>} />
        <Route path="templates" element={<div>Templates Page (TODO)</div>} />
        <Route path="logs" element={<div>Logs Page (TODO)</div>} />
        <Route path="settings" element={<div>Settings Page (TODO)</div>} />
      </Route>
    </Routes>
  );
}

export default App