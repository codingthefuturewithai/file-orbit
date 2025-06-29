import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CreateTransferForm from '../components/CreateTransferForm';
import { Job } from '../types';

const Transfers: React.FC = () => {
  const [showCreateForm, setShowCreateForm] = useState(true); // Show form by default
  const navigate = useNavigate();

  const handleTransferCreated = (job: Job) => {
    setShowCreateForm(false);
    // Redirect to dashboard after successful creation
    navigate('/');
  };

  return (
    <div className="transfers-page">
      <div className="page-header">
        <h1 className="page-title">Create Transfer</h1>
      </div>

      <div className="card">
        <h2>Manual Transfer</h2>
        <p>Create a one-time file transfer between endpoints.</p>
        
        {!showCreateForm ? (
          <button 
            className="btn btn-primary"
            onClick={() => setShowCreateForm(true)}
          >
            New Transfer
          </button>
        ) : (
          <CreateTransferForm 
            onSuccess={handleTransferCreated}
            onCancel={() => setShowCreateForm(false)}
          />
        )}
      </div>
    </div>
  );
};

export default Transfers;