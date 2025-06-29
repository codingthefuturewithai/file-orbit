import React from 'react';

interface ProgressBarProps {
  percentage: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ percentage }) => {
  return (
    <div className="progress-bar">
      <div 
        className="progress-bar-fill" 
        style={{ width: `${percentage}%` }}
      >
        <span style={{ padding: '0 5px', fontSize: '12px' }}>{percentage}%</span>
      </div>
    </div>
  );
};

export default ProgressBar;