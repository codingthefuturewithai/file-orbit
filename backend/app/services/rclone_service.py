import httpx
import asyncio
import subprocess
import json
import tempfile
import os
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RcloneService:
    """Wrapper for Rclone RC (Remote Control) API and CLI"""
    
    def __init__(self):
        self.base_url = f"http://{settings.RCLONE_RC_ADDR}"
        self.auth = None
        if settings.RCLONE_RC_USER and settings.RCLONE_RC_PASS:
            self.auth = (settings.RCLONE_RC_USER, settings.RCLONE_RC_PASS)
        
        # Store temporary config file path
        self.config_file = None
        self.remotes_config = {}
    
    async def _request(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the Rclone RC API"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{endpoint}",
                    json=data or {},
                    auth=self.auth,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Rclone RC request failed: {e}")
                raise Exception(f"Failed to connect to Rclone: {str(e)}")
            except httpx.HTTPStatusError as e:
                logger.error(f"Rclone RC HTTP error: {e}")
                raise Exception(f"Rclone error: {str(e)}")
    
    async def configure_remote(self, name: str, config: Dict[str, Any]):
        """Configure a remote for use with rclone"""
        logger.info(f"configure_remote called for {name} with config: {config}")
        # Store config for later use
        self.remotes_config[name] = config
        
        # Create/update config file
        await self._update_config_file()
    
    async def _update_config_file(self):
        """Update the rclone config file with current remotes"""
        if not self.config_file:
            # Create temporary config file
            fd, self.config_file = tempfile.mkstemp(suffix='.conf', prefix='rclone_')
            os.close(fd)
        
        # Build config content
        config_content = ""
        logger.info(f"Updating config file with {len(self.remotes_config)} remotes: {list(self.remotes_config.keys())}")
        for name, config in self.remotes_config.items():
            logger.info(f"Processing remote {name} with type {config.get('type')}")
            if config['type'] == 'local':
                # Local doesn't need a section in config
                continue
                
            config_content += f"[{name}]\n"
            config_content += f"type = {config['type']}\n"
            
            if config['type'] == 's3':
                config_content += f"provider = AWS\n"
                config_content += f"access_key_id = {config.get('access_key_id', '')}\n"
                config_content += f"secret_access_key = {config.get('secret_access_key', '')}\n"
                config_content += f"region = {config.get('region', '')}\n"
                # Note: For S3, bucket is specified in the path, not in config
            elif config['type'] == 'smb':
                config_content += f"host = {config.get('host', '')}\n"
                config_content += f"user = {config.get('user', '')}\n"
                # Obscure password using rclone's method as the documentation requires
                password = config.get('password', config.get('pass', ''))
                logger.info(f"Processing SMB password for endpoint {config.get('name')}: {password[:3]}...{password[-3:]} (length: {len(password)})")
                if password:
                    # Use rclone obscure command to properly encode the password
                    try:
                        obscure_process = await asyncio.create_subprocess_exec(
                            "rclone", "obscure", password,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await obscure_process.communicate()
                        if obscure_process.returncode == 0:
                            obscured_password = stdout.decode().strip()
                            logger.info(f"Raw password input: '{password}'")
                            logger.info(f"Full obscured output: '{obscured_password}'")
                            logger.info(f"Successfully obscured password: {obscured_password[:10]}...")
                            config_content += f"pass = {obscured_password}\n"
                        else:
                            logger.error(f"Failed to obscure password: {stderr.decode()}")
                            config_content += f"pass = {password}\n"  # Fallback to plain text
                    except Exception as e:
                        logger.error(f"Error running rclone obscure: {e}")
                        config_content += f"pass = {password}\n"  # Fallback to plain text
                else:
                    config_content += f"pass = \n"
                config_content += f"domain = {config.get('domain', 'WORKGROUP')}\n"
                # Add share if specified (though typically share is in the path)
                if config.get('share'):
                    config_content += f"share = {config.get('share', '')}\n"
            elif config['type'] == 'sftp':
                config_content += f"host = {config.get('host', '')}\n"
                config_content += f"user = {config.get('user', '')}\n"
                config_content += f"port = {config.get('port', 22)}\n"
                
                # Support both password and key-based authentication
                if config.get('key_file'):
                    # Use SSH key authentication
                    config_content += f"key_file = {config.get('key_file', '')}\n"
                    if config.get('key_passphrase'):
                        config_content += f"key_file_pass = {config.get('key_passphrase', '')}\n"
                else:
                    # Use password authentication
                    config_content += f"pass = {config.get('pass', '')}\n"
                
                # Add known hosts file if specified
                if config.get('known_hosts_file'):
                    config_content += f"known_hosts_file = {config.get('known_hosts_file', '')}\n"
            
            config_content += "\n"
        
        # Write config file
        with open(self.config_file, 'w') as f:
            f.write(config_content)
    
    async def list_files(self, remote_name: str, path: str, pattern: str = "*") -> List[Dict[str, Any]]:
        """List files in a directory"""
        full_path = self._build_path(remote_name, path)
        cmd = [
            "rclone", "lsjson",
            "--config", self.config_file,
            "--include", pattern,
            full_path
        ]
        
        logger.info(f"Listing files: {' '.join(cmd)}")
        logger.info(f"Full path: {full_path}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"Rclone list failed: {error_msg}")
                raise Exception(f"Rclone list failed: {error_msg}")
            
            # Handle empty output
            if not stdout:
                logger.warning(f"No output from rclone list for path: {full_path}")
                return []
            
            files = json.loads(stdout.decode())
            # Transform to expected format
            return [
                {
                    'name': f['Name'],
                    'path': f.get('Path', f['Name']),  # Use Name if Path not present
                    'size': f.get('Size', 0),
                    'is_dir': f.get('IsDir', False)
                }
                for f in files
                if not f.get('IsDir', False)  # Only return files, not directories
            ]
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse rclone output: {stdout.decode()[:200]}...")
            return []
        except Exception as e:
            logger.error(f"Failed to list files at {full_path}: {e}")
            raise
    
    def _build_path(self, remote_name: str, path: str) -> str:
        """Build the path for rclone command"""
        remote_config = self.remotes_config.get(remote_name, {})
        if remote_config.get('type') == 'local':
            # For local paths, handle base path from config
            base_path = remote_config.get('path', '')
            
            # If no base path configured, use the path as-is
            if not base_path or base_path == '/':
                return path
            
            # If path is absolute, use it directly (ignoring base_path)
            if path.startswith('/'):
                return path
            
            # For relative paths, join with base path
            from pathlib import Path
            return str(Path(base_path) / path)
        elif remote_config.get('type') == 's3':
            # For S3, include bucket in the path
            bucket = remote_config.get('bucket', '')
            if bucket:
                # Remove leading slash from path if present
                clean_path = path.lstrip('/')
                return f"{remote_name}:{bucket}/{clean_path}"
            else:
                return f"{remote_name}:{path}"
        elif remote_config.get('type') == 'smb':
            # For SMB, path format is remote:share/path
            # The share name should be in the path, not in config
            clean_path = path.lstrip('/')
            return f"{remote_name}:{clean_path}"
        elif remote_config.get('type') == 'sftp':
            # For SFTP, path format is remote:/absolute/path or remote:relative/path
            # If path starts with /, it's absolute from root
            # Otherwise it's relative to user's home directory
            if path.startswith('/'):
                return f"{remote_name}:{path}"
            else:
                # Relative path (from home directory)
                return f"{remote_name}:{path}"
        else:
            # For other remotes, use remote:path format
            return f"{remote_name}:{path}"
    
    async def start_transfer(self, source: str, dest: str, delete_source: bool = False) -> asyncio.subprocess.Process:
        """Start a file transfer and return the process handle"""
        cmd = [
            "rclone", "copy",
            "--config", self.config_file,
            "--progress",
            "--stats", "1s",
            "--stats-one-line",  # Easier to parse
            "-v",  # Verbose for better debugging
            "--checksum",  # Enable checksum verification
            # Note: rclone uses temporary files by default (no --inplace flag)
            source,
            dest
        ]
        
        if delete_source:
            # Use move instead of copy
            cmd[1] = "move"
        
        # Add bandwidth limit if configured
        if hasattr(settings, 'RCLONE_BANDWIDTH_LIMIT'):
            cmd.extend(["--bwlimit", settings.RCLONE_BANDWIDTH_LIMIT])
        
        logger.info(f"Starting transfer: {' '.join(cmd)}")
        logger.info(f"Source: {source}")
        logger.info(f"Destination: {dest}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        return process
    
    async def get_transfer_progress(self, process: asyncio.subprocess.Process) -> Optional[Dict[str, Any]]:
        """Get progress from a running rclone process"""
        try:
            # Read a line from stdout (rclone outputs JSON progress)
            line = await asyncio.wait_for(process.stdout.readline(), timeout=0.1)
            if not line:
                return None
            
            # Parse JSON progress
            data = json.loads(line.decode().strip())
            
            # Extract progress info
            stats = data.get('stats', {})
            return {
                'bytes': stats.get('bytes', 0),
                'percentage': stats.get('progress', 0),
                'rate': stats.get('speed', 0),
                'eta': stats.get('eta', None)
            }
            
        except asyncio.TimeoutError:
            return None
        except json.JSONDecodeError:
            return None
        except Exception as e:
            logger.error(f"Error reading progress: {e}")
            return None
    
    async def test_remote_connection(self, name: str, config: Dict[str, Any]) -> bool:
        """Test if a remote configuration is valid"""
        # Temporarily configure the remote
        await self.configure_remote("test", config)
        
        # Try to list the root directory
        try:
            if config.get('type') == 'local':
                # For local, check if path exists
                # The path is in the root config, not nested under 'config'
                path = config.get('path', '/')
                exists = os.path.exists(path)
                logger.info(f"Testing local path {path}: {'exists' if exists else 'not found'}")
                return exists
            elif config.get('type') == 'smb':
                # For SMB, try to list the share root
                # SMB paths need to include the share name
                share = config.get('share', '')
                if share:
                    await self.list_files("test", share, "*")
                else:
                    # Try to list available shares
                    await self.list_files("test", "", "*")
                return True
            elif config.get('type') == 'sftp':
                # For SFTP, try to list home directory
                await self.list_files("test", ".", "*")
                return True
            else:
                # For other remotes, try to list root
                await self.list_files("test", "/", "*")
                return True
        except Exception as e:
            logger.error(f"Remote test failed: {e}")
            return False
        finally:
            # Remove test remote
            self.remotes_config.pop("test", None)
            await self._update_config_file()
    
    # Keep existing RC API methods for compatibility
    async def list_remotes(self) -> List[str]:
        """List all configured remotes"""
        result = await self._request("config/listremotes")
        return result.get("remotes", [])
    
    async def check_connection(self) -> bool:
        """Check if Rclone RC is accessible"""
        try:
            await self._request("rc/noop")
            return True
        except Exception:
            return False
    
    async def get_transfer_stats(self, job_id: int) -> Dict[str, Any]:
        """Get transfer statistics for monitoring (RC API)"""
        try:
            result = await self._request("core/stats", {"group": str(job_id)})
            stats = result
            
            # Extract relevant stats
            bytes_transferred = stats.get("bytes", 0)
            bytes_total = stats.get("totalBytes", 0)
            speed = stats.get("speed", 0)
            
            # Calculate percentage
            percentage = 0
            if bytes_total > 0:
                percentage = (bytes_transferred / bytes_total) * 100
            
            # Calculate ETA
            eta = None
            if speed > 0 and bytes_total > bytes_transferred:
                seconds_remaining = (bytes_total - bytes_transferred) / speed
                eta = datetime.utcnow().timestamp() + seconds_remaining
            
            return {
                "bytes_transferred": bytes_transferred,
                "bytes_total": bytes_total,
                "speed": speed,
                "eta": eta,
                "percentage": percentage,
                "files_transferred": stats.get("transfers", 0),
                "files_total": stats.get("totalTransfers", 0),
                "errors": stats.get("errors", 0),
                "error_messages": stats.get("lastError", "")
            }
        except Exception as e:
            logger.error(f"Failed to get transfer stats: {e}")
            return {}
    
    def __del__(self):
        """Cleanup temporary config file"""
        if self.config_file and os.path.exists(self.config_file):
            try:
                os.unlink(self.config_file)
            except Exception:
                pass


# Global instance
rclone_service = RcloneService()