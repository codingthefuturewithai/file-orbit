import React, { useState } from 'react';

const Settings: React.FC = () => {
  const [emailSettings, setEmailSettings] = useState({
    smtp_host: 'smtp.pbs.org',
    smtp_port: 587,
    smtp_from: 'noreply@pbs.org',
    smtp_tls: true,
    notification_email: ''
  });

  const [generalSettings, setGeneralSettings] = useState({
    default_max_concurrent: 5,
    throttle_check_interval: 1,
    job_retention_days: 30
  });

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Submit email settings
    console.log('Email settings:', emailSettings);
  };

  const handleGeneralSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Submit general settings
    console.log('General settings:', generalSettings);
  };

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
      </div>

      <div className="card">
        <h2>Email Notifications</h2>
        <form onSubmit={handleEmailSubmit}>
          <div className="form-group">
            <label>SMTP Host</label>
            <input 
              type="text" 
              className="form-control"
              value={emailSettings.smtp_host}
              onChange={(e) => setEmailSettings({...emailSettings, smtp_host: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label>SMTP Port</label>
            <input 
              type="number" 
              className="form-control"
              value={emailSettings.smtp_port}
              onChange={(e) => setEmailSettings({...emailSettings, smtp_port: parseInt(e.target.value)})}
            />
          </div>
          <div className="form-group">
            <label>From Address</label>
            <input 
              type="email" 
              className="form-control"
              value={emailSettings.smtp_from}
              onChange={(e) => setEmailSettings({...emailSettings, smtp_from: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label>Notification Email</label>
            <input 
              type="email" 
              className="form-control"
              placeholder="admin@pbs.org"
              value={emailSettings.notification_email}
              onChange={(e) => setEmailSettings({...emailSettings, notification_email: e.target.value})}
            />
          </div>
          <button type="submit" className="btn btn-primary">Save Email Settings</button>
        </form>
      </div>

      <div className="card">
        <h2>General Settings</h2>
        <form onSubmit={handleGeneralSubmit}>
          <div className="form-group">
            <label>Default Max Concurrent Transfers</label>
            <input 
              type="number" 
              className="form-control"
              value={generalSettings.default_max_concurrent}
              onChange={(e) => setGeneralSettings({...generalSettings, default_max_concurrent: parseInt(e.target.value)})}
            />
          </div>
          <div className="form-group">
            <label>Throttle Check Interval (seconds)</label>
            <input 
              type="number" 
              className="form-control"
              value={generalSettings.throttle_check_interval}
              onChange={(e) => setGeneralSettings({...generalSettings, throttle_check_interval: parseInt(e.target.value)})}
            />
          </div>
          <div className="form-group">
            <label>Job History Retention (days)</label>
            <input 
              type="number" 
              className="form-control"
              value={generalSettings.job_retention_days}
              onChange={(e) => setGeneralSettings({...generalSettings, job_retention_days: parseInt(e.target.value)})}
            />
          </div>
          <button type="submit" className="btn btn-primary">Save General Settings</button>
        </form>
      </div>
    </div>
  );
};

export default Settings;