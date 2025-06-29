import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { TransferTemplate, Endpoint } from '../types';

interface TransferTemplateFormData {
  name: string;
  description?: string;
  event_type: 's3:ObjectCreated' | 'file:created' | 'file:modified' | 'manual';
  source_endpoint_id: string;
  destination_endpoint_id: string;
  destination_path_template: string;
  file_pattern: string;
  delete_source_after_transfer: boolean;
  is_active: boolean;
  source_config: Record<string, any>;
}

const TransferTemplates: React.FC = () => {
  const [transferTemplates, setTransferTemplates] = useState<TransferTemplate[]>([]);
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<TransferTemplate | null>(null);
  const [formData, setFormData] = useState<TransferTemplateFormData>({
    name: '',
    description: '',
    event_type: 'manual',
    source_endpoint_id: '',
    destination_endpoint_id: '',
    destination_path_template: '',
    file_pattern: '*',
    delete_source_after_transfer: false,
    is_active: true,
    source_config: {}
  });
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    fetchTransferTemplates();
    fetchEndpoints();
  }, []);


  const fetchTransferTemplates = async () => {
    try {
      const response = await api.get('/transfer-templates');
      setTransferTemplates(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching transfer templates:', error);
      setLoading(false);
    }
  };

  const fetchEndpoints = async () => {
    try {
      const response = await api.get('/endpoints');
      setEndpoints(response.data);
    } catch (error) {
      console.error('Error fetching endpoints:', error);
    }
  };

  const toggleTemplate = async (templateId: string, isActive: boolean) => {
    try {
      await api.put(`/transfer-templates/${templateId}`, { is_active: !isActive });
      fetchTransferTemplates();
    } catch (error) {
      console.error('Error toggling template:', error);
    }
  };

  const handleAdd = () => {
    setEditingTemplate(null);
    setFormData({
      name: '',
      description: '',
      event_type: 'manual',
      source_endpoint_id: '',
      destination_endpoint_id: '',
      destination_path_template: '',
      file_pattern: '*',
      delete_source_after_transfer: false,
      is_active: true,
      source_config: {}
    });
    setShowModal(true);
  };

  const handleEdit = (template: TransferTemplate) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      description: template.description || '',
      event_type: template.event_type,
      source_endpoint_id: template.source_endpoint_id,
      destination_endpoint_id: template.destination_endpoint_id,
      destination_path_template: template.destination_path_template,
      file_pattern: template.file_pattern,
      delete_source_after_transfer: template.delete_source_after_transfer,
      is_active: template.is_active,
      source_config: template.source_config || {}
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
      await api.delete(`/transfer-templates/${id}`);
      await fetchTransferTemplates();
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Error deleting transfer template:', error);
      alert('Failed to delete transfer template');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (editingTemplate) {
        await api.put(`/transfer-templates/${editingTemplate.id}`, formData);
      } else {
        await api.post('/transfer-templates', formData);
      }
      setShowModal(false);
      await fetchTransferTemplates();
    } catch (error) {
      console.error('Error saving transfer template:', error);
      alert('Failed to save transfer template');
    }
  };

  const getEndpointName = (endpointId: string) => {
    const endpoint = endpoints.find(e => e.id === endpointId);
    return endpoint ? endpoint.name : endpointId;
  };

  const updateSourceConfig = (key: string, value: string) => {
    setFormData({
      ...formData,
      source_config: { ...formData.source_config, [key]: value }
    });
  };

  const renderSourceConfigFields = () => {
    switch (formData.event_type) {
      case 's3:ObjectCreated':
        return (
          <>
            <div className="form-group">
              <label>S3 Bucket ARN</label>
              <input
                type="text"
                className="form-control"
                value={formData.source_config.bucket_arn || ''}
                onChange={(e) => updateSourceConfig('bucket_arn', e.target.value)}
                placeholder="arn:aws:s3:::bucket-name"
              />
            </div>
            <div className="form-group">
              <label>Event Prefix (optional)</label>
              <input
                type="text"
                className="form-control"
                value={formData.source_config.prefix || ''}
                onChange={(e) => updateSourceConfig('prefix', e.target.value)}
                placeholder="path/to/files/"
              />
            </div>
          </>
        );
      
      case 'file:created':
      case 'file:modified':
        return (
          <div className="form-group">
            <label>Watch Path</label>
            <input
              type="text"
              className="form-control"
              value={formData.source_config.watch_path || ''}
              onChange={(e) => updateSourceConfig('watch_path', e.target.value)}
              placeholder="/path/to/watch"
            />
          </div>
        );
      
      default:
        return null;
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="transfer-templates-page">
      <div className="page-header">
        <h1 className="page-title">Transfer Templates</h1>
        <button className="btn btn-primary" onClick={handleAdd}>Add Template</button>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Event Type</th>
              <th>Source</th>
              <th>Destination</th>
              <th>Status</th>
              <th>Triggers</th>
              <th>Success Rate</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {transferTemplates.map((template) => (
              <tr key={template.id}>
                <td>{template.name}</td>
                <td>{template.event_type}</td>
                <td>{getEndpointName(template.source_endpoint_id)}</td>
                <td>{getEndpointName(template.destination_endpoint_id)}</td>
                <td>
                  <button 
                    className={`btn btn-sm ${template.is_active ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => toggleTemplate(template.id, template.is_active)}
                  >
                    {template.is_active ? 'Active' : 'Inactive'}
                  </button>
                </td>
                <td>{template.total_triggers}</td>
                <td>
                  {template.total_triggers > 0 
                    ? `${((template.successful_transfers / template.total_triggers) * 100).toFixed(1)}%`
                    : 'N/A'
                  }
                </td>
                <td>
                  <button 
                    className="btn btn-secondary btn-sm" 
                    onClick={() => handleEdit(template)}
                  >
                    Edit
                  </button>
                  <button 
                    className={`btn ${deleteConfirm === template.id ? 'btn-warning' : 'btn-danger'} btn-sm`} 
                    style={{ marginLeft: '5px' }}
                    onClick={() => handleDelete(template.id)}
                  >
                    {deleteConfirm === template.id ? 'Confirm?' : 'Delete'}
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
              <h2>{editingTemplate ? 'Edit Transfer Template' : 'Add Transfer Template'}</h2>
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
                  <label>Description (optional)</label>
                  <textarea
                    className="form-control"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={2}
                  />
                </div>

                <div className="form-group">
                  <label>Event Type</label>
                  <select
                    className="form-control"
                    value={formData.event_type}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      event_type: e.target.value as any,
                      source_config: {} 
                    })}
                  >
                    <option value="manual">Manual</option>
                    <option value="s3:ObjectCreated">S3 Object Created</option>
                    <option value="file:created">File Created</option>
                    <option value="file:modified">File Modified</option>
                  </select>
                </div>

                {renderSourceConfigFields()}

                <div className="form-group">
                  <label>Source Endpoint</label>
                  <select
                    className="form-control"
                    value={formData.source_endpoint_id}
                    onChange={(e) => setFormData({ ...formData, source_endpoint_id: e.target.value })}
                    required
                  >
                    <option value="">Select endpoint...</option>
                    {endpoints.map(endpoint => (
                      <option key={endpoint.id} value={endpoint.id}>
                        {endpoint.name} ({endpoint.type.toUpperCase()})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Destination Endpoint</label>
                  <select
                    className="form-control"
                    value={formData.destination_endpoint_id}
                    onChange={(e) => setFormData({ ...formData, destination_endpoint_id: e.target.value })}
                    required
                  >
                    <option value="">Select endpoint...</option>
                    {endpoints.map(endpoint => (
                      <option key={endpoint.id} value={endpoint.id}>
                        {endpoint.name} ({endpoint.type.toUpperCase()})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Destination Path Template</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.destination_path_template}
                    onChange={(e) => setFormData({ ...formData, destination_path_template: e.target.value })}
                    placeholder="e.g., /dest/{year}/{month}/{day}/{filename}"
                    required
                  />
                  <small className="text-muted">
                    Variables: {'{filename}'}, {'{year}'}, {'{month}'}, {'{day}'}, {'{timestamp}'}
                  </small>
                </div>

                <div className="form-group">
                  <label>File Pattern</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.file_pattern}
                    onChange={(e) => setFormData({ ...formData, file_pattern: e.target.value })}
                    placeholder="e.g., *.csv, *.json"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.delete_source_after_transfer}
                      onChange={(e) => setFormData({ ...formData, delete_source_after_transfer: e.target.checked })}
                    />
                    {' '}Delete source files after transfer
                  </label>
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
                  {editingTemplate ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransferTemplates;