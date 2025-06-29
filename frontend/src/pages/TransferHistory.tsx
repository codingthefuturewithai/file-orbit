import React, { useState, useEffect } from 'react';
import api from '../services/api';
import TransferList from '../components/TransferList';
import { Job } from '../types';

const TransferHistory: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [dateRange, setDateRange] = useState({
    start: '',
    end: ''
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  useEffect(() => {
    fetchJobs();
  }, []);

  useEffect(() => {
    filterJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobs, statusFilter, typeFilter, searchTerm, dateRange]);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      // Fetch all jobs, not just recent ones
      const response = await api.get('/jobs?limit=1000');
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  // Helper to get date at start/end of day in local timezone
  const getDateBounds = (dateString: string, isEndOfDay: boolean = false) => {
    // The input date string is in YYYY-MM-DD format
    const [year, month, day] = dateString.split('-').map(Number);
    
    if (isEndOfDay) {
      // End of day: 23:59:59.999
      return new Date(year, month - 1, day, 23, 59, 59, 999);
    } else {
      // Start of day: 00:00:00.000
      return new Date(year, month - 1, day, 0, 0, 0, 0);
    }
  };

  const filterJobs = () => {
    let filtered = [...jobs];

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(job => job.status === statusFilter);
    }

    // Type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(job => job.type === typeFilter);
    }

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(job => 
        job.name.toLowerCase().includes(term) ||
        job.source_path.toLowerCase().includes(term) ||
        job.destination_path.toLowerCase().includes(term) ||
        job.id.toLowerCase().includes(term)
      );
    }

    // Date range filter
    if (dateRange.start) {
      const startDate = getDateBounds(dateRange.start, false);
      filtered = filtered.filter(job => {
        const jobDate = new Date(job.created_at);
        return jobDate >= startDate;
      });
    }
    if (dateRange.end) {
      const endDate = getDateBounds(dateRange.end, true);
      filtered = filtered.filter(job => {
        const jobDate = new Date(job.created_at);
        return jobDate <= endDate;
      });
    }

    setFilteredJobs(filtered);
    setCurrentPage(1); // Reset to first page when filters change
  };

  // Pagination
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredJobs.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredJobs.length / itemsPerPage);

  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  const getStatusCounts = () => {
    const counts: Record<string, number> = {
      all: jobs.length,
      completed: 0,
      failed: 0,
      running: 0,
      queued: 0,
      pending: 0,
      cancelled: 0
    };

    jobs.forEach(job => {
      counts[job.status] = (counts[job.status] || 0) + 1;
    });

    return counts;
  };

  const statusCounts = getStatusCounts();

  if (loading) {
    return <div>Loading transfer history...</div>;
  }

  return (
    <div className="transfer-history-page">
      <div className="page-header">
        <h1 className="page-title">Transfer History</h1>
      </div>

      {/* Filters */}
      <div className="card mb-4">
        <div className="card-body">
          <h5 className="mb-3">Filters</h5>
          
          <div className="row">
            {/* Search */}
            <div className="col-md-4 mb-3">
              <label className="form-label">Search</label>
              <input
                type="text"
                className="form-control"
                placeholder="Search by name, path, or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            {/* Status Filter */}
            <div className="col-md-2 mb-3">
              <label className="form-label">Status</label>
              <select 
                className="form-control"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All ({statusCounts.all})</option>
                <option value="completed">Completed ({statusCounts.completed})</option>
                <option value="failed">Failed ({statusCounts.failed})</option>
                <option value="running">Running ({statusCounts.running})</option>
                <option value="queued">Queued ({statusCounts.queued})</option>
                <option value="pending">Pending ({statusCounts.pending})</option>
                <option value="cancelled">Cancelled ({statusCounts.cancelled})</option>
              </select>
            </div>

            {/* Type Filter */}
            <div className="col-md-2 mb-3">
              <label className="form-label">Type</label>
              <select 
                className="form-control"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="all">All Types</option>
                <option value="manual">Manual</option>
                <option value="scheduled">Scheduled</option>
                <option value="event_triggered">Event Triggered</option>
                <option value="chained">Chained</option>
              </select>
            </div>

            {/* Date Range */}
            <div className="col-md-2 mb-3">
              <label className="form-label">Start Date</label>
              <input
                type="date"
                className="form-control"
                value={dateRange.start}
                onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
              />
            </div>

            <div className="col-md-2 mb-3">
              <label className="form-label">End Date</label>
              <input
                type="date"
                className="form-control"
                value={dateRange.end}
                onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
              />
            </div>
          </div>

          <div className="row">
            <div className="col-12">
              <button 
                className="btn btn-secondary btn-sm"
                onClick={() => {
                  setStatusFilter('all');
                  setTypeFilter('all');
                  setSearchTerm('');
                  setDateRange({ start: '', end: '' });
                }}
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="row mb-4">
        <div className="col-md-3">
          <div className="card stat-card">
            <div className="card-body">
              <h6>Total Transfers</h6>
              <h3>{filteredJobs.length}</h3>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card stat-card">
            <div className="card-body">
              <h6>Successful</h6>
              <h3 className="text-success">
                {filteredJobs.filter(j => j.status === 'completed').length}
              </h3>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card stat-card">
            <div className="card-body">
              <h6>Failed</h6>
              <h3 className="text-danger">
                {filteredJobs.filter(j => j.status === 'failed').length}
              </h3>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card stat-card">
            <div className="card-body">
              <h6>Success Rate</h6>
              <h3>
                {filteredJobs.length > 0 
                  ? ((filteredJobs.filter(j => j.status === 'completed').length / filteredJobs.length) * 100).toFixed(1)
                  : 0}%
              </h3>
            </div>
          </div>
        </div>
      </div>

      {/* Transfer List */}
      <div className="card">
        <div className="card-body">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5 className="mb-0">
              Transfer History ({filteredJobs.length} {filteredJobs.length === 1 ? 'transfer' : 'transfers'})
            </h5>
            <div className="d-flex align-items-center">
              <label className="me-2 mb-0">Items per page:</label>
              <select 
                className="form-control form-control-sm" 
                style={{ width: 'auto' }}
                value={itemsPerPage} 
                onChange={(e) => {
                  setItemsPerPage(Number(e.target.value));
                  setCurrentPage(1);
                }}
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>
          
          {currentItems.length > 0 ? (
            <>
              <TransferList 
                jobs={currentItems} 
                onJobUpdated={fetchJobs}
              />
              
              {/* Pagination */}
              {totalPages > 1 && (
                <nav className="mt-4">
                  <ul className="pagination justify-content-center">
                    <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
                      <button 
                        className="page-link" 
                        onClick={() => paginate(currentPage - 1)}
                        disabled={currentPage === 1}
                      >
                        Previous
                      </button>
                    </li>
                    
                    {/* First page */}
                    {currentPage > 3 && (
                      <>
                        <li className="page-item">
                          <button className="page-link" onClick={() => paginate(1)}>1</button>
                        </li>
                        {currentPage > 4 && (
                          <li className="page-item disabled">
                            <span className="page-link">...</span>
                          </li>
                        )}
                      </>
                    )}
                    
                    {/* Pages around current */}
                    {[...Array(totalPages)].map((_, index) => {
                      const pageNumber = index + 1;
                      if (
                        pageNumber === currentPage ||
                        pageNumber === currentPage - 1 ||
                        pageNumber === currentPage - 2 ||
                        pageNumber === currentPage + 1 ||
                        pageNumber === currentPage + 2
                      ) {
                        return (
                          <li key={pageNumber} className={`page-item ${currentPage === pageNumber ? 'active' : ''}`}>
                            <button className="page-link" onClick={() => paginate(pageNumber)}>
                              {pageNumber}
                            </button>
                          </li>
                        );
                      }
                      return null;
                    })}
                    
                    {/* Last page */}
                    {currentPage < totalPages - 2 && (
                      <>
                        {currentPage < totalPages - 3 && (
                          <li className="page-item disabled">
                            <span className="page-link">...</span>
                          </li>
                        )}
                        <li className="page-item">
                          <button className="page-link" onClick={() => paginate(totalPages)}>
                            {totalPages}
                          </button>
                        </li>
                      </>
                    )}
                    
                    <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
                      <button 
                        className="page-link" 
                        onClick={() => paginate(currentPage + 1)}
                        disabled={currentPage === totalPages}
                      >
                        Next
                      </button>
                    </li>
                  </ul>
                  <p className="text-center text-muted">
                    Showing {indexOfFirstItem + 1} - {Math.min(indexOfLastItem, filteredJobs.length)} of {filteredJobs.length} transfers
                  </p>
                </nav>
              )}
            </>
          ) : (
            <p>No transfers found matching your filters.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TransferHistory;