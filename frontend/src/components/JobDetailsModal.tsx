import React, { useEffect, useState } from 'react';
import { Job, Transfer } from '../types';
import StatusBadge from './StatusBadge';
import ProgressBar from './ProgressBar';
import api from '../services/api';

interface JobDetailsModalProps {
  job: Job | null;
  show: boolean;
  onClose: () => void;
}

const JobDetailsModal: React.FC<JobDetailsModalProps> = ({ job, show, onClose }) => {
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (job && show) {
      fetchTransfers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job, show]);

  const fetchTransfers = async () => {
    if (!job) return;
    
    setLoading(true);
    try {
      const response = await api.get(`/transfers?job_id=${job.id}`);
      setTransfers(response.data);
    } catch (error) {
      console.error('Failed to fetch transfers:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string | undefined): string => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (start: string | undefined, end: string | undefined): string => {
    if (!start) return 'N/A';
    const startDate = new Date(start);
    const endDate = end ? new Date(end) : new Date();
    const durationMs = endDate.getTime() - startDate.getTime();
    
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  if (!show || !job) return null;

  return (
    <>
      <div className="modal-backdrop show" onClick={onClose}></div>
      <div className="modal show d-block" tabIndex={-1}>
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">Transfer Details - {job.name || `Job ${job.id.substring(0, 8)}`}</h5>
              <button type="button" className="btn-close" onClick={onClose}></button>
            </div>
            <div className="modal-body">
              {/* Job Information */}
              <div className="mb-4">
                <h6>Job Information</h6>
                <table className="table table-sm">
                  <tbody>
                    <tr>
                      <td><strong>ID:</strong></td>
                      <td>{job.id}</td>
                    </tr>
                    <tr>
                      <td><strong>Status:</strong></td>
                      <td><StatusBadge status={job.status} /></td>
                    </tr>
                    <tr>
                      <td><strong>Type:</strong></td>
                      <td>{job.type.replace('_', ' ')}</td>
                    </tr>
                    <tr>
                      <td><strong>Created:</strong></td>
                      <td>{formatDate(job.created_at)}</td>
                    </tr>
                    <tr>
                      <td><strong>Started:</strong></td>
                      <td>{formatDate(job.started_at)}</td>
                    </tr>
                    <tr>
                      <td><strong>Completed:</strong></td>
                      <td>{formatDate(job.completed_at)}</td>
                    </tr>
                    <tr>
                      <td><strong>Duration:</strong></td>
                      <td>{formatDuration(job.started_at, job.completed_at)}</td>
                    </tr>
                    <tr>
                      <td><strong>Total Runs:</strong></td>
                      <td>{job.total_runs}</td>
                    </tr>
                    <tr>
                      <td><strong>Successful/Failed:</strong></td>
                      <td>{job.successful_runs} / {job.failed_runs}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Transfer Configuration */}
              <div className="mb-4">
                <h6>Transfer Configuration</h6>
                <table className="table table-sm">
                  <tbody>
                    <tr>
                      <td><strong>Source:</strong></td>
                      <td>{job.source_path}</td>
                    </tr>
                    <tr>
                      <td><strong>Destination:</strong></td>
                      <td>{job.destination_path}</td>
                    </tr>
                    <tr>
                      <td><strong>File Pattern:</strong></td>
                      <td>{job.file_pattern || '*'}</td>
                    </tr>
                    <tr>
                      <td><strong>Delete Source:</strong></td>
                      <td>{job.delete_source_after_transfer ? 'Yes' : 'No'}</td>
                    </tr>
                    {job.schedule && (
                      <tr>
                        <td><strong>Schedule:</strong></td>
                        <td>{job.schedule}</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Progress */}
              {job.status === 'running' && (
                <div className="mb-4">
                  <h6>Progress</h6>
                  <ProgressBar percentage={job.progress_percentage} />
                  <div className="mt-2">
                    <small>
                      Files: {job.transferred_files} / {job.total_files} | 
                      Data: {formatBytes(job.transferred_bytes)} / {formatBytes(job.total_bytes)}
                    </small>
                  </div>
                </div>
              )}

              {/* Error Information */}
              {job.error_message && (
                <div className="mb-4">
                  <h6>Error Information</h6>
                  <div className="alert alert-danger">
                    {job.error_message}
                  </div>
                  <small>Retry Count: {job.retry_count}</small>
                </div>
              )}

              {/* Individual File Transfers */}
              <div className="mb-4">
                <h6>File Transfers ({transfers.length})</h6>
                {loading ? (
                  <p>Loading transfers...</p>
                ) : transfers.length > 0 ? (
                  <div className="table-responsive" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    <table className="table table-sm">
                      <thead>
                        <tr>
                          <th>File</th>
                          <th>Size</th>
                          <th>Status</th>
                          <th>Progress</th>
                        </tr>
                      </thead>
                      <tbody>
                        {transfers.map((transfer) => (
                          <tr key={transfer.id}>
                            <td>{transfer.file_name}</td>
                            <td>{formatBytes(transfer.file_size)}</td>
                            <td><StatusBadge status={transfer.status} /></td>
                            <td>
                              {transfer.status === 'in_progress' ? (
                                <ProgressBar percentage={transfer.progress_percentage} />
                              ) : (
                                `${transfer.progress_percentage.toFixed(0)}%`
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p>No file transfers found.</p>
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={onClose}>
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default JobDetailsModal;