import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import './Logs.css';

interface LogData {
  lines: string[];
  total: number;
  filtered: number;
  returned: number;
}

const Logs: React.FC = () => {
  const [selectedLogType, setSelectedLogType] = useState<string>('backend');
  const [lineCount, setLineCount] = useState<number>(100);
  const [filterText, setFilterText] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);
  const [logData, setLogData] = useState<LogData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const logTypes = [
    { value: 'backend', label: 'Backend' },
    { value: 'worker', label: 'Worker' },
    { value: 'event-monitor', label: 'Event Monitor' },
    { value: 'scheduler', label: 'Scheduler' }
  ];

  const lineOptions = [50, 100, 500, 1000];

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        lines: lineCount.toString()
      });
      
      if (filterText) {
        params.append('filter', filterText);
      }
      
      const response = await api.get(`/logs/${selectedLogType}?${params.toString()}`);
      setLogData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch logs');
      setLogData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedLogType, lineCount, filterText]);

  // Fetch logs on component mount and when dependencies change
  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Auto-refresh functionality
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchLogs();
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, fetchLogs]);

  const handleLogTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedLogType(e.target.value);
  };

  const handleLineCountChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLineCount(parseInt(e.target.value));
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterText(e.target.value);
  };

  const handleAutoRefreshToggle = () => {
    setAutoRefresh(!autoRefresh);
  };

  const handleRefresh = () => {
    fetchLogs();
  };

  const formatLogLine = (line: string, index: number) => {
    // Basic syntax highlighting for log levels
    let className = 'log-line';
    if (line.includes('ERROR') || line.includes('CRITICAL')) {
      className += ' log-error';
    } else if (line.includes('WARNING') || line.includes('WARN')) {
      className += ' log-warning';
    } else if (line.includes('INFO')) {
      className += ' log-info';
    } else if (line.includes('DEBUG')) {
      className += ' log-debug';
    }

    return (
      <div key={index} className={className}>
        <span className="log-line-number">{index + 1}</span>
        <span className="log-line-content">{line}</span>
      </div>
    );
  };

  return (
    <div className="logs-page">
      <h1>System Logs</h1>
      
      <div className="logs-controls">
        <div className="control-group">
          <label htmlFor="log-type">Log Type:</label>
          <select
            id="log-type"
            value={selectedLogType}
            onChange={handleLogTypeChange}
            className="form-control"
          >
            {logTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="line-count">Lines:</label>
          <select
            id="line-count"
            value={lineCount}
            onChange={handleLineCountChange}
            className="form-control"
          >
            {lineOptions.map(count => (
              <option key={count} value={count}>
                {count}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="filter">Filter:</label>
          <input
            id="filter"
            type="text"
            value={filterText}
            onChange={handleFilterChange}
            placeholder="Search logs..."
            className="form-control"
          />
        </div>

        <div className="control-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={handleAutoRefreshToggle}
            />
            Auto-refresh
          </label>
        </div>

        <button onClick={handleRefresh} className="btn btn-primary">
          Refresh
        </button>
      </div>

      {logData && (
        <div className="log-stats">
          <span>Total lines: {logData.total}</span>
          {filterText && <span> | Filtered: {logData.filtered}</span>}
          <span> | Showing: {logData.returned}</span>
        </div>
      )}

      <div className="log-viewer">
        {loading && <div className="loading">Loading logs...</div>}
        {error && <div className="error">Error: {error}</div>}
        {logData && !loading && (
          <div className="log-content">
            {logData.lines.length === 0 ? (
              <div className="no-logs">No logs found</div>
            ) : (
              logData.lines.map((line, index) => formatLogLine(line, index))
            )}
          </div>
        )}
      </div>

    </div>
  );
};

export default Logs;