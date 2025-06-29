import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Job, Endpoint, TransferTemplate } from '../types';

interface CreateTransferFormProps {
  onSuccess: (job: Job) => void;
  onCancel: () => void;
}

const CreateTransferForm: React.FC<CreateTransferFormProps> = ({ onSuccess, onCancel }) => {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [templates, setTemplates] = useState<TransferTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
  const [useTemplate, setUseTemplate] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    type: 'manual' as 'manual' | 'scheduled' | 'event_triggered',
    source_endpoint_id: '',
    source_path: '',
    destination_endpoint_id: '',
    destination_path: '',
    file_pattern: '',
    delete_source_after_transfer: false,
    schedule: '',
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchEndpoints();
    fetchTemplates();
  }, []);

  const fetchEndpoints = async () => {
    try {
      const response = await api.get('/endpoints');
      setEndpoints(response.data.filter((ep: Endpoint) => ep.is_active));
    } catch (error) {
      console.error('Error fetching endpoints:', error);
      setError('Failed to load endpoints');
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/transfer-templates');
      setTemplates(response.data.filter((template: TransferTemplate) => template.is_active));
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplateId(templateId);
    
    if (templateId) {
      const template = templates.find(t => t.id === templateId);
      if (template) {
        setFormData({
          ...formData,
          source_endpoint_id: template.source_endpoint_id,
          source_path: '',  // Clear source path - user must enter it
          destination_endpoint_id: template.destination_endpoint_id,
          destination_path: template.destination_path_template,
          file_pattern: template.file_pattern,
          delete_source_after_transfer: template.delete_source_after_transfer
        });
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const jobData = {
        ...formData,
        name: formData.name || `Transfer from ${getEndpointName(formData.source_endpoint_id)} to ${getEndpointName(formData.destination_endpoint_id)}`,
        file_pattern: formData.file_pattern || null,  // Send null instead of empty string
        schedule: formData.type === 'scheduled' ? formData.schedule : null
      };

      const response = await api.post('/jobs', jobData);
      
      // If manual transfer, execute it immediately
      if (formData.type === 'manual') {
        try {
          await api.post(`/jobs/${response.data.id}/execute`, {});
          response.data.status = 'queued';
        } catch (execError) {
          console.error('Failed to execute job:', execError);
        }
      }
      
      onSuccess(response.data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to create transfer');
      setLoading(false);
    }
  };

  const getEndpointName = (id: string): string => {
    const endpoint = endpoints.find(ep => ep.id === id);
    return endpoint?.name || 'Unknown';
  };

  return (
    <form onSubmit={handleSubmit} className="transfer-form">
      {error && (
        <div className="alert alert-danger">{error}</div>
      )}
      
      <div className="form-group">
        <label>Start from:</label>
        <div style={{ marginBottom: '10px' }}>
          <label style={{ marginRight: '20px' }}>
            <input
              type="radio"
              name="templateChoice"
              checked={!useTemplate}
              onChange={() => {
                setUseTemplate(false);
                setSelectedTemplateId('');
              }}
              style={{ marginRight: '5px' }}
            />
            Scratch
          </label>
          <label>
            <input
              type="radio"
              name="templateChoice"
              checked={useTemplate}
              onChange={() => setUseTemplate(true)}
              style={{ marginRight: '5px' }}
            />
            Use a template
          </label>
        </div>
      </div>

      {useTemplate && (
        <div className="form-group">
          <label>Select Template</label>
          <select
            className="form-control"
            value={selectedTemplateId}
            onChange={(e) => handleTemplateSelect(e.target.value)}
          >
            <option value="">Select a template...</option>
            {templates.map(template => (
              <option key={template.id} value={template.id}>
                {template.name} ({template.event_type})
              </option>
            ))}
          </select>
        </div>
      )}
      
      <div className="form-group">
        <label>Transfer Name (optional)</label>
        <input 
          type="text" 
          className="form-control"
          placeholder="e.g., Daily backup to S3"
          value={formData.name}
          onChange={(e) => setFormData({...formData, name: e.target.value})}
        />
      </div>

      <div className="form-group">
        <label>Transfer Type</label>
        <select 
          className="form-control"
          value={formData.type}
          onChange={(e) => setFormData({...formData, type: e.target.value as any})}
        >
          <option value="manual">Manual (Run Once)</option>
          <option value="scheduled">Scheduled</option>
        </select>
      </div>

      {formData.type === 'scheduled' && (
        <div className="form-group">
          <label>Schedule</label>
          <select 
            className="form-control"
            value={formData.schedule}
            onChange={(e) => setFormData({...formData, schedule: e.target.value})}
            required
          >
            <option value="">Select schedule</option>
            <option value="@hourly">Hourly</option>
            <option value="@daily">Daily</option>
            <option value="@weekly">Weekly</option>
            <option value="@monthly">Monthly</option>
          </select>
        </div>
      )}
      
      <div className="form-group">
        <label>Source Endpoint</label>
        <select 
          className="form-control"
          value={formData.source_endpoint_id}
          onChange={(e) => setFormData({...formData, source_endpoint_id: e.target.value})}
          required
        >
          <option value="">Select source endpoint</option>
          {endpoints.map(endpoint => (
            <option key={endpoint.id} value={endpoint.id}>
              {endpoint.name} ({endpoint.type.toUpperCase()})
              {endpoint.max_concurrent_transfers <= 2 && ' (Throttled)'}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>Source Path {useTemplate && selectedTemplateId && <span className="text-warning">(Required - not provided by template)</span>}</label>
        <input 
          type="text" 
          className="form-control"
          placeholder="/path/to/source/files"
          value={formData.source_path}
          onChange={(e) => setFormData({...formData, source_path: e.target.value})}
          required
        />
        <small className="form-text">Full path to source directory or file</small>
      </div>

      <div className="form-group">
        <label>Destination Endpoint</label>
        <select 
          className="form-control"
          value={formData.destination_endpoint_id}
          onChange={(e) => setFormData({...formData, destination_endpoint_id: e.target.value})}
          required
        >
          <option value="">Select destination endpoint</option>
          {endpoints.map(endpoint => (
            <option key={endpoint.id} value={endpoint.id}>
              {endpoint.name} ({endpoint.type.toUpperCase()})
              {endpoint.max_concurrent_transfers <= 2 && ' (Throttled)'}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>Destination Path {useTemplate && selectedTemplateId && <span className="text-info">(From template - can be modified)</span>}</label>
        <input 
          type="text" 
          className="form-control"
          placeholder="/path/to/destination"
          value={formData.destination_path}
          onChange={(e) => setFormData({...formData, destination_path: e.target.value})}
          required
        />
        <small className="form-text">Full path to destination directory</small>
      </div>

      <div className="form-group">
        <label>File Pattern (optional) {useTemplate && selectedTemplateId && formData.file_pattern && <span className="text-info">(From template - can be modified)</span>}</label>
        <input 
          type="text" 
          className="form-control"
          placeholder="*.mp4 or leave empty for all files"
          value={formData.file_pattern}
          onChange={(e) => setFormData({...formData, file_pattern: e.target.value})}
        />
        <small className="form-text">Use * for all files, or patterns like *.mp4, *.mov</small>
      </div>

      <div className="form-group">
        <label>
          <input 
            type="checkbox"
            checked={formData.delete_source_after_transfer}
            onChange={(e) => setFormData({...formData, delete_source_after_transfer: e.target.checked})}
          />
          {' '}Delete source files after successful transfer
        </label>
      </div>

      <div className="form-actions">
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? 'Creating...' : (formData.type === 'manual' ? 'Create & Execute' : 'Create Transfer')}
        </button>
        <button 
          type="button" 
          className="btn btn-secondary"
          onClick={onCancel}
          disabled={loading}
        >
          Cancel
        </button>
      </div>
    </form>
  );
};

export default CreateTransferForm;