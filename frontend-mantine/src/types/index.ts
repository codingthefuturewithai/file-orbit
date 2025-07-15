export interface Job {
  id: string;
  name: string;
  type: 'manual' | 'event_triggered' | 'scheduled' | 'chained';
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'retrying';
  source_endpoint_id: string;
  source_path: string;
  destination_endpoint_id: string;
  destination_path: string;
  file_pattern: string;
  delete_source_after_transfer: boolean;
  schedule?: string;
  is_active: boolean;
  config?: Record<string, any>;
  total_files: number;
  transferred_files: number;
  total_bytes: number;
  transferred_bytes: number;
  progress_percentage: number;
  created_at: string;
  updated_at?: string;
  started_at?: string;
  completed_at?: string;
  last_run_at?: string;
  next_run_at?: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  error_message?: string;
  retry_count: number;
  created_by?: string;
}

export interface Transfer {
  id: string;
  job_id: string;
  file_name: string;
  file_path: string;
  file_size: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  bytes_transferred: number;
  progress_percentage: number;
  transfer_rate?: number;
  started_at?: string;
  completed_at?: string;
  eta?: string;
  error_message?: string;
}

export interface Endpoint {
  id: string;
  name: string;
  type: 'local' | 'smb' | 's3' | 'sftp' | 'ftp' | 'webdav';
  config: Record<string, any>;
  max_concurrent_transfers: number;
  max_bandwidth?: number;
  is_active: boolean;
  last_connected?: string;
  connection_status: string;
  created_at: string;
  total_transfers: number;
  failed_transfers: number;
  total_bytes_transferred: number;
}

export interface TransferTemplate {
  id: string;
  name: string;
  description?: string;
  event_type: 's3:ObjectCreated' | 'file:created' | 'file:modified' | 'manual';
  is_active: boolean;
  source_config: Record<string, any>;
  source_endpoint_id: string;
  destination_endpoint_id: string;
  destination_path_template: string;
  chain_rules?: Array<{
    endpoint_id: string;
    path_template: string;
  }>;
  file_pattern: string;
  delete_source_after_transfer: boolean;
  created_at: string;
  last_triggered?: string;
  total_triggers: number;
  successful_transfers: number;
  failed_transfers: number;
}