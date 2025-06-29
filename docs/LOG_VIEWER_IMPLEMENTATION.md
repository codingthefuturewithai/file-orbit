# Log Viewer Implementation Guide

## Overview

The log viewer is essential for troubleshooting remote transfers without requiring SSH access to servers. This feature allows users to view and search through system logs directly from the web UI.

## Log Files to Support

1. **backend.log** - API requests, errors, job creation
2. **worker.log** - Transfer execution, rclone output, errors
3. **event-monitor.log** - File watching events, trigger activations
4. **scheduler.log** - Scheduled job executions (when enabled)
5. **frontend.log** - UI errors (if captured)

## Backend Implementation

### 1. Log Reader Service

```python
# File: mvp/backend/app/services/log_reader.py

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import re

class LogReader:
    """Service for reading and parsing log files"""
    
    def __init__(self):
        self.log_dir = Path("/Users/tkitchens/projects/ctf/rclone-poc/mvp/logs")
        self.allowed_files = [
            "backend.log", 
            "worker.log", 
            "event-monitor.log",
            "scheduler.log",
            "frontend.log"
        ]
    
    async def list_log_files(self) -> List[dict]:
        """List available log files with metadata"""
        files = []
        for filename in self.allowed_files:
            filepath = self.log_dir / filename
            if filepath.exists():
                stat = filepath.stat()
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "lines": self._count_lines(filepath)
                })
        return files
    
    async def read_log(
        self, 
        filename: str, 
        lines: int = 1000,
        offset: int = 0,
        level: Optional[str] = None,
        search: Optional[str] = None
    ) -> dict:
        """Read log file with filtering"""
        if filename not in self.allowed_files:
            raise ValueError(f"Access denied to {filename}")
            
        filepath = self.log_dir / filename
        if not filepath.exists():
            return {"lines": [], "total": 0, "filtered": 0}
        
        # Read file backwards for most recent entries first
        log_lines = []
        with open(filepath, 'r') as f:
            # Use deque for efficient line limiting
            from collections import deque
            all_lines = deque(f, maxlen=lines + offset)
            
            # Skip offset lines
            for _ in range(min(offset, len(all_lines))):
                all_lines.popleft()
            
            # Filter and collect lines
            for line in all_lines:
                if self._should_include_line(line, level, search):
                    log_lines.append(self._parse_log_line(line))
                    if len(log_lines) >= lines:
                        break
        
        return {
            "lines": log_lines,
            "total": self._count_lines(filepath),
            "filtered": len(log_lines)
        }
    
    def _parse_log_line(self, line: str) -> dict:
        """Parse log line into structured format"""
        # Example: 2025-06-29 08:15:20,401 - __main__ - INFO - Processing job
        pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (.*?) - (.*?) - (.*)$'
        match = re.match(pattern, line)
        
        if match:
            return {
                "timestamp": match.group(1),
                "module": match.group(2),
                "level": match.group(3),
                "message": match.group(4),
                "raw": line
            }
        else:
            return {
                "timestamp": None,
                "module": None,
                "level": None,
                "message": line.strip(),
                "raw": line
            }
    
    def _should_include_line(
        self, 
        line: str, 
        level: Optional[str], 
        search: Optional[str]
    ) -> bool:
        """Check if line matches filters"""
        if level:
            if level not in line:
                return False
        
        if search:
            if search.lower() not in line.lower():
                return False
                
        return True
    
    def _count_lines(self, filepath: Path) -> int:
        """Count total lines in file"""
        with open(filepath, 'r') as f:
            return sum(1 for _ in f)
```

### 2. Log API Endpoints

```python
# File: mvp/backend/app/api/api_v1/endpoints/logs.py

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.log_reader import LogReader

router = APIRouter()
log_reader = LogReader()

@router.get("/")
async def list_logs():
    """List available log files"""
    return await log_reader.list_log_files()

@router.get("/{filename}")
async def read_log(
    filename: str,
    lines: int = Query(1000, description="Number of lines to return"),
    offset: int = Query(0, description="Number of lines to skip"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    search: Optional[str] = Query(None, description="Search text")
):
    """Read log file with filtering"""
    try:
        return await log_reader.read_log(filename, lines, offset, level, search)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error reading log: {str(e)}")

# Add to api.py router includes:
# api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
```

### 3. WebSocket for Real-time Logs

```python
# File: mvp/backend/app/api/api_v1/websockets/log_stream.py

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import aiofiles
from pathlib import Path

class LogStreamer:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, filename: str):
        await websocket.accept()
        if filename not in self.active_connections:
            self.active_connections[filename] = []
        self.active_connections[filename].append(websocket)
    
    def disconnect(self, websocket: WebSocket, filename: str):
        self.active_connections[filename].remove(websocket)
        if not self.active_connections[filename]:
            del self.active_connections[filename]
    
    async def stream_log(self, websocket: WebSocket, filename: str):
        """Stream log file updates to websocket"""
        filepath = Path(f"/Users/tkitchens/projects/ctf/rclone-poc/mvp/logs/{filename}")
        
        try:
            async with aiofiles.open(filepath, 'r') as f:
                # Go to end of file
                await f.seek(0, 2)
                
                while True:
                    line = await f.readline()
                    if line:
                        await websocket.send_text(line)
                    else:
                        await asyncio.sleep(0.5)
        except WebSocketDisconnect:
            self.disconnect(websocket, filename)

log_streamer = LogStreamer()

@router.websocket("/ws/logs/{filename}")
async def websocket_endpoint(websocket: WebSocket, filename: str):
    await log_streamer.connect(websocket, filename)
    try:
        await log_streamer.stream_log(websocket, filename)
    except WebSocketDisconnect:
        pass
```

## Frontend Implementation

### 1. Log Viewer Page Component

```typescript
// File: mvp/frontend/src/pages/LogViewer.tsx

import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';

interface LogLine {
  timestamp: string | null;
  module: string | null;
  level: string | null;
  message: string;
  raw: string;
}

interface LogFile {
  filename: string;
  size: number;
  modified: string;
  lines: number;
}

export default function LogViewer() {
  const [logFiles, setLogFiles] = useState<LogFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('worker.log');
  const [logLines, setLogLines] = useState<LogLine[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState({
    level: '',
    search: '',
    lines: 1000
  });
  
  const logContainerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    fetchLogFiles();
  }, []);

  useEffect(() => {
    if (selectedFile) {
      fetchLogContent();
      
      // Setup WebSocket for real-time updates
      if (wsRef.current) {
        wsRef.current.close();
      }
      
      const ws = new WebSocket(`ws://localhost:8000/ws/logs/${selectedFile}`);
      ws.onmessage = (event) => {
        const newLine = parseLogLine(event.data);
        setLogLines(prev => [...prev, newLine]);
        
        if (autoScroll && logContainerRef.current) {
          logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
      };
      
      wsRef.current = ws;
      
      return () => {
        ws.close();
      };
    }
  }, [selectedFile, filter]);

  const fetchLogFiles = async () => {
    try {
      const response = await api.get('/logs');
      setLogFiles(response.data);
    } catch (error) {
      console.error('Failed to fetch log files:', error);
    }
  };

  const fetchLogContent = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        lines: filter.lines.toString(),
        ...(filter.level && { level: filter.level }),
        ...(filter.search && { search: filter.search })
      });
      
      const response = await api.get(`/logs/${selectedFile}?${params}`);
      setLogLines(response.data.lines);
    } catch (error) {
      console.error('Failed to fetch log content:', error);
    }
    setLoading(false);
  };

  const parseLogLine = (line: string): LogLine => {
    // Simple parsing logic - backend does the heavy lifting
    return { 
      timestamp: null, 
      module: null, 
      level: null, 
      message: line, 
      raw: line 
    };
  };

  const getLevelColor = (level: string | null) => {
    switch (level) {
      case 'ERROR': return 'text-red-600';
      case 'WARNING': return 'text-yellow-600';
      case 'INFO': return 'text-blue-600';
      case 'DEBUG': return 'text-gray-600';
      default: return 'text-gray-800';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">System Logs</h1>
      
      {/* Controls */}
      <div className="bg-white shadow rounded-lg p-4 mb-4">
        <div className="grid grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Log File</label>
            <select
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            >
              {logFiles.map(file => (
                <option key={file.filename} value={file.filename}>
                  {file.filename} ({(file.size / 1024).toFixed(1)} KB)
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Level Filter</label>
            <select
              value={filter.level}
              onChange={(e) => setFilter({...filter, level: e.target.value})}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            >
              <option value="">All Levels</option>
              <option value="ERROR">ERROR</option>
              <option value="WARNING">WARNING</option>
              <option value="INFO">INFO</option>
              <option value="DEBUG">DEBUG</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Search</label>
            <input
              type="text"
              value={filter.search}
              onChange={(e) => setFilter({...filter, search: e.target.value})}
              placeholder="Search logs..."
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={fetchLogContent}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Refresh
            </button>
            <label className="ml-4 flex items-center">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded"
              />
              <span className="ml-2 text-sm">Auto-scroll</span>
            </label>
          </div>
        </div>
      </div>
      
      {/* Log Content */}
      <div className="bg-white shadow rounded-lg">
        <div 
          ref={logContainerRef}
          className="p-4 font-mono text-sm overflow-auto"
          style={{ height: '600px' }}
        >
          {loading ? (
            <div className="text-center text-gray-500">Loading logs...</div>
          ) : (
            <>
              {logLines.map((line, index) => (
                <div key={index} className="hover:bg-gray-50">
                  {line.timestamp && (
                    <span className="text-gray-500">{line.timestamp}</span>
                  )}
                  {line.level && (
                    <span className={`ml-2 font-semibold ${getLevelColor(line.level)}`}>
                      [{line.level}]
                    </span>
                  )}
                  {line.module && (
                    <span className="ml-2 text-purple-600">{line.module}:</span>
                  )}
                  <span className="ml-2">{line.message}</span>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
```

### 2. Add to Navigation

```typescript
// File: mvp/frontend/src/App.tsx
// Add to navigation:

<Link
  to="/logs"
  className={`${
    location.pathname === '/logs'
      ? 'bg-gray-900 text-white'
      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
  } px-3 py-2 rounded-md text-sm font-medium`}
>
  Logs
</Link>

// Add to routes:
<Route path="/logs" element={<LogViewer />} />
```

## Key Features

1. **File Selection**: Dropdown to choose which log file to view
2. **Level Filtering**: Filter by ERROR, WARNING, INFO, DEBUG
3. **Search**: Text search across log entries
4. **Real-time Updates**: WebSocket connection for live log tailing
5. **Auto-scroll**: Option to automatically scroll to bottom for new entries
6. **Syntax Highlighting**: Color-coded log levels for easy scanning

## Security Considerations

1. **Path Traversal Protection**: Only allow access to specific log files
2. **File Size Limits**: Implement pagination for large files
3. **Rate Limiting**: Prevent DoS through excessive log requests
4. **Authentication**: Ensure log viewer requires authentication in production

## Performance Optimizations

1. **Pagination**: Load logs in chunks rather than entire file
2. **Indexing**: Consider indexing logs in database for faster searching
3. **Compression**: Compress old logs and provide decompression on demand
4. **Caching**: Cache frequently accessed log segments

## Future Enhancements

1. **Download Logs**: Allow downloading filtered log segments
2. **Log Aggregation**: Combine logs from multiple services
3. **Pattern Detection**: Highlight common error patterns
4. **Export to CSV**: Export filtered logs for analysis
5. **Metrics Dashboard**: Show log statistics (errors/hour, etc.)