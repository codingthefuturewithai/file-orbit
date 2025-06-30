from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Optional, List, Dict
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{log_type}")
async def get_logs(
    log_type: str,
    lines: int = Query(100, ge=1, le=1000),
    filter: Optional[str] = None
) -> Dict:
    """Get logs from the specified log file
    
    Args:
        log_type: Type of log to retrieve (backend, worker, event-monitor, scheduler)
        lines: Number of lines to return (default 100, max 1000)
        filter: Optional string to filter log lines
        
    Returns:
        Dictionary with log lines and metadata
    """
    allowed_logs = ["backend", "worker", "event-monitor", "scheduler"]
    if log_type not in allowed_logs:
        raise HTTPException(status_code=400, detail=f"Invalid log type. Must be one of: {', '.join(allowed_logs)}")
    
    # Construct log path - use absolute path for now
    # TODO: Make this configurable via environment variable
    log_path = Path(f"/Users/timkitchens/projects/consumer-apps/file-orbit/logs/{log_type}.log")
    
    # Check if log file exists
    if not log_path.exists():
        logger.warning(f"Log file not found: {log_path}")
        return {"lines": [], "total": 0, "filtered": 0}
    
    try:
        # Read the log file
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()
        
        # Apply filter if provided
        if filter:
            filter_lower = filter.lower()
            filtered_lines = [line for line in all_lines if filter_lower in line.lower()]
        else:
            filtered_lines = all_lines
        
        # Get the last N lines
        result_lines = filtered_lines[-lines:]
        
        # Strip newlines and prepare response
        result_lines = [line.rstrip('\n') for line in result_lines]
        
        return {
            "lines": result_lines,
            "total": len(all_lines),
            "filtered": len(filtered_lines),
            "returned": len(result_lines)
        }
        
    except Exception as e:
        logger.error(f"Error reading log file {log_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading log file: {str(e)}")

@router.get("/{log_type}/tail")
async def tail_logs(
    log_type: str,
    lines: int = Query(50, ge=1, le=500)
) -> Dict:
    """Get the tail of a log file (last N lines)
    
    This is a simplified version for real-time monitoring.
    For true real-time tailing, implement WebSocket endpoint.
    """
    return await get_logs(log_type=log_type, lines=lines, filter=None)