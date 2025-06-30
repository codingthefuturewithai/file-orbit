import React, { useState, useEffect } from 'react';
import { Job, Endpoint } from '../types';
import api from '../services/api';

interface EditJobModalProps {
  job: Job | null;
  show: boolean;
  onClose: () => void;
  onJobUpdated: () => void;
}

const EditJobModal: React.FC<EditJobModalProps> = ({ job, show, onClose, onJobUpdated }) => {
  const [formData, setFormData] = useState({
    name: '',
    source_endpoint_id: '',
    source_path: '',
    destination_endpoint_id: '',
    destination_path: '',
    file_pattern: '',
    delete_source_after_transfer: false,
  });
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executeAfterSave, setExecuteAfterSave] = useState(false);

  useEffect(() => {
    if (show) {
      fetchEndpoints();
      if (job) {
        setFormData({
          name: job.name,
          source_endpoint_id: job.source_endpoint_id,
          source_path: job.source_path,
          destination_endpoint_id: job.destination_endpoint_id,
          destination_path: job.destination_path,
          file_pattern: job.file_pattern || '',
          delete_source_after_transfer: job.delete_source_after_transfer,
        });
      }
    }
  }, [job, show]);

  const fetchEndpoints = async () => {
    setLoading(true);
    try {
      const response = await api.get('/endpoints');
      setEndpoints(response.data);
    } catch (error) {
      console.error('Failed to fetch endpoints:', error);
      setError('Failed to load endpoints');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!job) return;

    setSaving(true);
    setError(null);

    try {
      if (executeAfterSave) {
        // Use the update-and-execute endpoint
        await api.put(`/jobs/${job.id}/update-and-execute`, formData);
      } else {
        // Just update the job
        await api.put(`/jobs/${job.id}`, formData);
      }
      onJobUpdated();
      onClose();
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to update job');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    if (type === 'checkbox') {
      setFormData(prev => ({
        ...prev,
        [name]: (e.target as HTMLInputElement).checked
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  if (!show || !job) return null;

  return (
    <>
      <div className="modal-backdrop show" onClick={onClose}></div>
      <div className="modal show" tabIndex={-1} style={{ display: 'flex' }}>
        <div className="modal-dialog modal-dialog-centered modal-lg">
          <div className="modal-content">
            <form onSubmit={handleSubmit}>
              <div className="modal-header">
                <h5 className="modal-title">Edit Transfer - {job.name}</h5>
                <button type="button" className="btn-close" onClick={onClose}></button>
              </div>
              <div className="modal-body">
                {error && (
                  <div className="alert alert-danger alert-dismissible" role="alert">
                    {error}
                    <button 
                      type="button" 
                      className="btn-close" 
                      onClick={() => setError(null)}
                    ></button>
                  </div>
                )}

                <div className="mb-3">
                  <label className="form-label">Transfer Name</label>
                  <input
                    type="text"
                    className="form-control"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div className="row">
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Source Endpoint</label>
                      <select
                        className="form-select"
                        name="source_endpoint_id"
                        value={formData.source_endpoint_id}
                        onChange={handleChange}
                        required
                        disabled={loading}
                      >
                        <option value="">Select endpoint...</option>
                        {endpoints.map(endpoint => (
                          <option key={endpoint.id} value={endpoint.id}>
                            {endpoint.name} ({endpoint.type})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Source Path</label>
                      <input
                        type="text"
                        className="form-control"
                        name="source_path"
                        value={formData.source_path}
                        onChange={handleChange}
                        placeholder="/path/to/source"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div className="row">
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Destination Endpoint</label>
                      <select
                        className="form-select"
                        name="destination_endpoint_id"
                        value={formData.destination_endpoint_id}
                        onChange={handleChange}
                        required
                        disabled={loading}
                      >
                        <option value="">Select endpoint...</option>
                        {endpoints.map(endpoint => (
                          <option key={endpoint.id} value={endpoint.id}>
                            {endpoint.name} ({endpoint.type})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="mb-3">
                      <label className="form-label">Destination Path</label>
                      <input
                        type="text"
                        className="form-control"
                        name="destination_path"
                        value={formData.destination_path}
                        onChange={handleChange}
                        placeholder="/path/to/destination"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div className="mb-3">
                  <label className="form-label">File Pattern</label>
                  <input
                    type="text"
                    className="form-control"
                    name="file_pattern"
                    value={formData.file_pattern}
                    onChange={handleChange}
                    placeholder="*.mp4, *.mov (leave empty for all files)"
                  />
                  <small className="form-text text-muted">
                    Use wildcards: * matches any characters, ? matches single character
                  </small>
                </div>

                <div className="mb-3">
                  <div className="form-check">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      id="deleteSource"
                      name="delete_source_after_transfer"
                      checked={formData.delete_source_after_transfer}
                      onChange={handleChange}
                    />
                    <label className="form-check-label" htmlFor="deleteSource">
                      Delete source files after successful transfer
                    </label>
                  </div>
                </div>

                <div className="mb-3">
                  <div className="form-check">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      id="executeAfterSave"
                      checked={executeAfterSave}
                      onChange={(e) => setExecuteAfterSave(e.target.checked)}
                    />
                    <label className="form-check-label" htmlFor="executeAfterSave">
                      Execute transfer immediately after saving
                    </label>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={onClose}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : (executeAfterSave ? 'Save & Execute' : 'Save Changes')}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};

export default EditJobModal;