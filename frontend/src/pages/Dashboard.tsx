import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import TransferList from '../components/TransferList';
import { Job } from '../types';

const Dashboard: React.FC = () => {
  const [activeJobs, setActiveJobs] = useState<Job[]>([]);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState({
    totalTransfers: 0,
    activeTransfers: 0,
    failedTransfers: 0,
    successRate: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [activeResponse, recentResponse, statsResponse] = await Promise.all([
        api.get('/jobs?status=running&limit=10'),
        api.get('/jobs?limit=10'),
        api.get('/stats')
      ]);

      setActiveJobs(activeResponse.data);
      setRecentJobs(recentResponse.data);
      setStats(statsResponse.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <Link to="/transfers" className="btn btn-primary">Create Transfer</Link>
      </div>

      <div className="stats-grid">
        <div className="card stat-card">
          <h3>Total Transfers</h3>
          <p className="stat-value">{stats.totalTransfers}</p>
        </div>
        <div className="card stat-card">
          <h3>Active Transfers</h3>
          <p className="stat-value">{stats.activeTransfers}</p>
        </div>
        <div className="card stat-card">
          <h3>Failed Transfers</h3>
          <p className="stat-value">{stats.failedTransfers}</p>
        </div>
        <div className="card stat-card">
          <h3>Success Rate</h3>
          <p className="stat-value">{stats.successRate.toFixed(1)}%</p>
        </div>
      </div>

      <div className="card">
        <h2>Active Transfers</h2>
        {activeJobs.length > 0 ? (
          <TransferList jobs={activeJobs} showProgress={true} onJobUpdated={fetchDashboardData} />
        ) : (
          <p>No active transfers</p>
        )}
      </div>

      <div className="card">
        <h2>10 Most Recent Transfers</h2>
        <TransferList jobs={recentJobs} onJobUpdated={fetchDashboardData} />
      </div>
    </div>
  );
};

export default Dashboard;