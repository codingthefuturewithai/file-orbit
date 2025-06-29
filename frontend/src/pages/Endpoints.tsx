import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Endpoint } from '../types';

interface EndpointFormData {
  name: string;
  type: 'local' | 's3' | 'smb' | 'sftp' | 'ftp' | 'webdav';
  config: Record<string, any>;
  max_concurrent_transfers: number;
  max_bandwidth?: string;
  is_active: boolean;
}

const Endpoints: React.FC = () => {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingEndpoint, setEditingEndpoint] = useState<Endpoint | null>(null);
  const [formData, setFormData] = useState<EndpointFormData>({
    name: '',
    type: 'local',
    config: {},
    max_concurrent_transfers: 5,
    max_bandwidth: '',
    is_active: true
  });
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    fetchEndpoints();
  }, []);

  const fetchEndpoints = async () => {
    try {
      const response = await api.get('/endpoints');
      setEndpoints(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching endpoints:', error);
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatBandwidth = (bytes: number | null): string => {
    if (!bytes) return '';
    
    const k = 1024;
    if (bytes < k) return bytes.toString();
    if (bytes < k * k) return Math.round(bytes / k) + 'K';
    if (bytes < k * k * k) return Math.round(bytes / (k * k)) + 'M';
    if (bytes < k * k * k * k) return Math.round(bytes / (k * k * k)) + 'G';
    return Math.round(bytes / (k * k * k * k)) + 'T';
  };

  const handleAdd = () => {
    setEditingEndpoint(null);
    setFormData({
      name: '',
      type: 'local',
      config: {},
      max_concurrent_transfers: 5,
      max_bandwidth: '',
      is_active: true
    });
    setShowModal(true);
  };

  const handleEdit = (endpoint: Endpoint) => {
    setEditingEndpoint(endpoint);
    setFormData({
      name: endpoint.name,
      type: endpoint.type,
      config: endpoint.config,
      max_concurrent_transfers: endpoint.max_concurrent_transfers,
      max_bandwidth: endpoint.max_bandwidth ? endpoint.max_bandwidth.toString() : '',
      is_active: endpoint.is_active
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (deleteConfirm !== id) {
      setDeleteConfirm(id);
      setTimeout(() => setDeleteConfirm(null), 3000);
      return;
    }

    try {
      await api.delete(`/endpoints/${id}`);
      await fetchEndpoints();
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Error deleting endpoint:', error);
      alert('Failed to delete endpoint');
    }
  };

  const parseBandwidth = (bandwidth: string): number | null => {
    if (!bandwidth) return null;
    
    // Parse bandwidth strings like "10M", "100M", "1G"
    const match = bandwidth.match(/^(\d+(?:\.\d+)?)\s*([KMGT]?)$/i);
    if (!match) {
      // Try parsing as a plain number (bytes)
      const num = parseInt(bandwidth);
      return isNaN(num) ? null : num;
    }
    
    const value = parseFloat(match[1]);
    const unit = match[2].toUpperCase();
    
    const multipliers: { [key: string]: number } = {
      '': 1,          // No unit = bytes
      'K': 1024,      // Kilobytes
      'M': 1024 * 1024,      // Megabytes
      'G': 1024 * 1024 * 1024,  // Gigabytes
      'T': 1024 * 1024 * 1024 * 1024  // Terabytes
    };
    
    return Math.floor(value * (multipliers[unit] || 1));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Prepare the data for submission
    const submitData = {
      ...formData,
      // Convert max_bandwidth to number or null
      max_bandwidth: parseBandwidth(formData.max_bandwidth || '')
    };
    
    try {
      if (editingEndpoint) {
        await api.put(`/endpoints/${editingEndpoint.id}`, submitData);
      } else {
        await api.post('/endpoints', submitData);
      }
      setShowModal(false);
      await fetchEndpoints();
    } catch (error: any) {
      console.error('Error saving endpoint:', error);
      console.error('Request data:', submitData);
      console.error('Response:', error.response?.data);
      
      // FastAPI returns validation errors in a specific format
      let errorMessage = 'Failed to save endpoint';
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          // Validation errors come as an array
          errorMessage = error.response.data.detail.map((err: any) => 
            `${err.loc.join('.')}: ${err.msg}`
          ).join('\n');
        }
      }
      alert(errorMessage);
    }
  };

  const updateConfig = (key: string, value: string) => {
    setFormData({
      ...formData,
      config: { ...formData.config, [key]: value }
    });
  };

  const renderConfigFields = () => {
    switch (formData.type) {
      case 'local':
        return (
          <div className="form-group">
            <label>Path</label>
            <input
              type="text"
              className="form-control"
              value={formData.config.path || ''}
              onChange={(e) => updateConfig('path', e.target.value)}
              placeholder="/path/to/directory"
              required
            />
          </div>
        );
      
      case 's3':
        return (
          <>
            <div className="form-group">
              <label>Bucket</label>
              <input
                type="text"
                className="form-control"
                value={formData.config.bucket || ''}
                onChange={(e) => updateConfig('bucket', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Region</label>
              <input
                type="text"
                className="form-control"
                value={formData.config.region || ''}
                onChange={(e) => updateConfig('region', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Access Key</label>
              <input
                type="text"
                className="form-control"
                value={formData.config.access_key || ''}
                onChange={(e) => updateConfig('access_key', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Secret Key</label>
              <input
                type="password"
                className="form-control"
                value={formData.config.secret_key || ''}
                onChange={(e) => updateConfig('secret_key', e.target.value)}
                required={!editingEndpoint}
              />
            </div>
          </>
        );
      
      case 'smb':
        return (
          <>
            <div className="form-group">
              <label>Host</label>
              <input
                type="text"
                className="form-control"
                value={formData.config.host || ''}
                onChange={(e) => updateConfig('host', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Share</label>
              <input
                type="text"
                className="form-control"
                value={formData.config.share || ''}
                onChange={(e) => updateConfig('share', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                className="form-control"
                value={formData.config.user || ''}
                onChange={(e) => updateConfig('user', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                className="form-control"
                value={formData.config.password || ''}
                onChange={(e) => updateConfig('password', e.target.value)}
                required={!editingEndpoint}
              />
            </div>
            <div className="form-group">
              <label>Domain</label>
              <input
                type="text"
                className="form-control"
                value={formData.config.domain || ''}
                onChange={(e) => updateConfig('domain', e.target.value)}
              />
            </div>
          </>
        );
      
      case 'sftp':
        return (
          <>
            <div className="form-group">
              <label>Host</label>
              <input
                type="text"
                className="form-control"
                value={formData.config.host || ''}
                onChange={(e) => updateConfig('host', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Port</label>
              <input
                type="number"
                className="form-control"
                value={formData.config.port || 22}
                onChange={(e) => updateConfig('port', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                className="form-control"
                value={formData.config.user || ''}
                onChange={(e) => updateConfig('user', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                className="form-control"
                value={formData.config.password || ''}
                onChange={(e) => updateConfig('password', e.target.value)}
                placeholder={editingEndpoint ? '(unchanged)' : ''}
              />
            </div>
          </>
        );
      
      default:
        return null;
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="endpoints-page">
      <div className="page-header">
        <h1 className="page-title">Endpoints</h1>
        <button className="btn btn-primary" onClick={handleAdd}>Add Endpoint</button>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Status</th>
              <th>Max Concurrent</th>
              <th>Total Transfers</th>
              <th>Data Transferred</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {endpoints.map((endpoint) => (
              <tr key={endpoint.id}>
                <td>{endpoint.name}</td>
                <td>{endpoint.type.toUpperCase()}</td>
                <td>
                  <span className={`status-badge ${endpoint.is_active ? 'status-completed' : 'status-failed'}`}>
                    {endpoint.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>{endpoint.max_concurrent_transfers}</td>
                <td>{endpoint.total_transfers}</td>
                <td>{formatBytes(endpoint.total_bytes_transferred)}</td>
                <td>
                  <button 
                    className="btn btn-secondary btn-sm" 
                    onClick={() => handleEdit(endpoint)}
                  >
                    Edit
                  </button>
                  <button 
                    className={`btn ${deleteConfirm === endpoint.id ? 'btn-warning' : 'btn-danger'} btn-sm`} 
                    style={{ marginLeft: '5px' }}
                    onClick={() => handleDelete(endpoint.id)}
                  >
                    {deleteConfirm === endpoint.id ? 'Confirm?' : 'Delete'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingEndpoint ? 'Edit Endpoint' : 'Add Endpoint'}</h2>
              <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Name</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Type</label>
                  <select
                    className="form-control"
                    value={formData.type}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      type: e.target.value as any,
                      config: {} 
                    })}
                    disabled={!!editingEndpoint}
                  >
                    <option value="local">Local</option>
                    <option value="s3">S3</option>
                    <option value="smb">SMB</option>
                    <option value="sftp">SFTP</option>
                  </select>
                </div>

                {renderConfigFields()}

                <div className="form-group">
                  <label>Max Concurrent Transfers</label>
                  <input
                    type="number"
                    className="form-control"
                    value={formData.max_concurrent_transfers}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      max_concurrent_transfers: parseInt(e.target.value) 
                    })}
                    min="1"
                    max="100"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Max Bandwidth (optional)</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.max_bandwidth}
                    onChange={(e) => setFormData({ ...formData, max_bandwidth: e.target.value })}
                    placeholder="e.g., 10M, 100M, 1G"
                  />
                </div>

                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                    {' '}Active
                  </label>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingEndpoint ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Endpoints;