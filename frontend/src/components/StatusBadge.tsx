import React from 'react';

interface StatusBadgeProps {
  status: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getStatusClass = (status: string): string => {
    switch (status) {
      case 'running':
      case 'in_progress':
        return 'status-running';
      case 'completed':
        return 'status-completed';
      case 'failed':
        return 'status-failed';
      case 'pending':
      case 'queued':
        return 'status-pending';
      default:
        return '';
    }
  };

  return (
    <span className={`status-badge ${getStatusClass(status)}`}>
      {status.replace('_', ' ')}
    </span>
  );
};

export default StatusBadge;