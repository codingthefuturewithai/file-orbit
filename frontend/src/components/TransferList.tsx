import React, { useState } from 'react';
import { Job } from '../types';
import ProgressBar from './ProgressBar';
import StatusBadge from './StatusBadge';
import JobDetailsModal from './JobDetailsModal';
import EditJobModal from './EditJobModal';
import api from '../services/api';

interface TransferListProps {
  jobs: Job[];
  showProgress?: boolean;
  onJobUpdated?: () => void;
}

const TransferList: React.FC<TransferListProps> = ({ jobs, showProgress = false, onJobUpdated }) => {
  const [retryingJobs, setRetryingJobs] = useState<Set<string>>(new Set());
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const handleRetry = async (jobId: string) => {
    setRetryingJobs(prev => {
      const newSet = new Set(prev);
      newSet.add(jobId);
      return newSet;
    });
    try {
      await api.post(`/jobs/${jobId}/execute`, {});
      if (onJobUpdated) {
        onJobUpdated();
      }
    } catch (error) {
      console.error('Failed to retry job:', error);
    } finally {
      setRetryingJobs(prev => {
        const newSet = new Set(prev);
        newSet.delete(jobId);
        return newSet;
      });
    }
  };

  const handleCancel = async (jobId: string) => {
    if (!window.confirm('Are you sure you want to cancel this transfer?')) {
      return;
    }
    
    try {
      await api.post(`/jobs/${jobId}/cancel`, {});
      if (onJobUpdated) {
        onJobUpdated();
      }
    } catch (error) {
      console.error('Failed to cancel job:', error);
      alert('Failed to cancel the transfer. Please try again.');
    }
  };

  return (
    <>
      <table className="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Source</th>
          <th>Destination</th>
          <th>Size</th>
          <th>Status</th>
          {showProgress && <th>Progress</th>}
          <th>Created</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {jobs.map((job) => (
          <tr key={job.id}>
            <td>{job.id.substring(0, 8)}</td>
            <td>{job.source_path}</td>
            <td>{job.destination_path}</td>
            <td>{formatBytes(job.total_bytes)}</td>
            <td><StatusBadge status={job.status} /></td>
            {showProgress && (
              <td style={{ width: '200px' }}>
                <ProgressBar percentage={job.progress_percentage} />
              </td>
            )}
            <td>{formatDate(job.created_at)}</td>
            <td>
              <button 
                className="btn btn-info btn-sm me-2"
                onClick={() => {
                  setSelectedJob(job);
                  setShowDetailsModal(true);
                }}
              >
                Details
              </button>
              {job.status !== 'running' && job.status !== 'queued' && (
                <button 
                  className="btn btn-secondary btn-sm me-2"
                  onClick={() => {
                    setSelectedJob(job);
                    setShowEditModal(true);
                  }}
                >
                  Edit
                </button>
              )}
              {job.status === 'running' && (
                <button 
                  className="btn btn-danger btn-sm"
                  onClick={() => handleCancel(job.id)}
                >
                  Cancel
                </button>
              )}
              {job.status === 'failed' && (
                <button 
                  className="btn btn-primary btn-sm"
                  onClick={() => handleRetry(job.id)}
                  disabled={retryingJobs.has(job.id)}
                >
                  {retryingJobs.has(job.id) ? 'Retrying...' : 'Retry'}
                </button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
      </table>
      
      <JobDetailsModal 
        job={selectedJob}
        show={showDetailsModal}
        onClose={() => {
          setShowDetailsModal(false);
          setSelectedJob(null);
        }}
      />
      
      <EditJobModal
        job={selectedJob}
        show={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedJob(null);
        }}
        onJobUpdated={() => {
          setShowEditModal(false);
          setSelectedJob(null);
          if (onJobUpdated) {
            onJobUpdated();
          }
        }}
      />
    </>
  );
};

export default TransferList;