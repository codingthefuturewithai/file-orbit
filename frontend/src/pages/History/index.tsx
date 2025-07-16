import { useState, useEffect } from 'react';
import { Container, Title, Paper, Table, Badge, Group, TextInput, Select, Button, Stack, Pagination, Text, ActionIcon, Tooltip } from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { IconSearch, IconEye, IconRefresh, IconLink } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import type { Job } from '../../types';
import { useApi } from '../../hooks/useApi';
import { formatBytes } from '../../utils/format';
import JobDetailsModal from '../../components/JobDetailsModal';

const statusColors: Record<string, string> = {
  pending: 'gray',
  queued: 'blue',
  running: 'cyan',
  completed: 'green',
  failed: 'red',
  cancelled: 'orange',
  retrying: 'yellow',
};

const typeColors: Record<string, string> = {
  manual: 'blue',
  scheduled: 'violet',
  event_triggered: 'grape',
  chained: 'indigo',
};

export default function History() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [page, setPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  
  const { callApi, loading } = useApi();

  useEffect(() => {
    fetchJobs();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [jobs, statusFilter, typeFilter, searchTerm, dateRange]);

  const fetchJobs = async () => {
    try {
      const response = await callApi<Job[]>('/jobs', 'GET');
      if (response) {
        setJobs(response);
      }
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    }
  };

  const applyFilters = () => {
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
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(job => 
        job.name.toLowerCase().includes(search) ||
        job.source_path.toLowerCase().includes(search) ||
        job.destination_path.toLowerCase().includes(search) ||
        job.id.toLowerCase().includes(search)
      );
    }

    // Date range filter
    if (dateRange[0] && dateRange[1]) {
      filtered = filtered.filter(job => {
        const jobDate = new Date(job.created_at);
        return jobDate >= dateRange[0]! && jobDate <= dateRange[1]!;
      });
    }

    setFilteredJobs(filtered);
    setPage(1); // Reset to first page when filters change
  };

  const handleRetry = async (jobId: string) => {
    try {
      await callApi(`/jobs/${jobId}/retry`, 'POST');
      notifications.show({
        title: 'Success',
        message: 'Transfer retry initiated',
        color: 'green',
      });
      fetchJobs();
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to retry transfer',
        color: 'red',
      });
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const formatDuration = (start?: string, end?: string) => {
    if (!start || !end) return '-';
    
    const duration = new Date(end).getTime() - new Date(start).getTime();
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const paginatedJobs = filteredJobs.slice(
    (page - 1) * itemsPerPage,
    page * itemsPerPage
  );

  const totalPages = Math.ceil(filteredJobs.length / itemsPerPage);

  const rows = paginatedJobs.map((job) => (
    <Table.Tr key={job.id}>
      <Table.Td>
        <Stack gap="xs">
          <Group gap="xs">
            <Text size="sm" fw={500}>{job.name}</Text>
            {job.type === 'chained' && (
              <Tooltip label="This is a chain transfer">
                <Badge size="xs" color="indigo" leftSection={<IconLink size={12} />}>
                  Chain
                </Badge>
              </Tooltip>
            )}
            {job.parent_job_id && (
              <Tooltip label={`Part of chain from job ${job.parent_job_id.substring(0, 8)}...`}>
                <IconLink size={14} color="var(--mantine-color-indigo-6)" />
              </Tooltip>
            )}
          </Group>
          <Text size="xs" c="dimmed">{job.id}</Text>
        </Stack>
      </Table.Td>
      <Table.Td>
        <Badge color={typeColors[job.type] || 'gray'} variant="light">
          {job.type}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Badge color={statusColors[job.status] || 'gray'}>
          {job.status}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Stack gap="xs">
          <Text size="sm">{job.source_path}</Text>
          <Text size="xs" c="dimmed">→ {job.destination_path}</Text>
        </Stack>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{formatBytes(job.total_bytes)}</Text>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{formatDate(job.created_at)}</Text>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{formatDuration(job.started_at, job.completed_at)}</Text>
      </Table.Td>
      <Table.Td>
        <Group gap="xs">
          {job.status === 'failed' && (
            <Tooltip label="Retry">
              <ActionIcon color="blue" variant="light" onClick={() => handleRetry(job.id)}>
                <IconRefresh size={16} />
              </ActionIcon>
            </Tooltip>
          )}
          <Tooltip label="View Details">
            <ActionIcon variant="light" onClick={() => {
              setSelectedJob(job);
              setShowDetails(true);
            }}>
              <IconEye size={16} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Table.Td>
    </Table.Tr>
  ));

  return (
    <Container size="xl">
      <Title order={2} mb="xl">Transfer History</Title>

      {/* Filters */}
      <Paper shadow="sm" p="md" mb="lg" withBorder>
        <Stack>
          <Group grow>
            <TextInput
              placeholder="Search by name, path, or ID..."
              leftSection={<IconSearch size={16} />}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.currentTarget.value)}
            />
            <Select
              placeholder="All statuses"
              data={[
                { value: 'all', label: 'All Statuses' },
                { value: 'completed', label: 'Completed' },
                { value: 'failed', label: 'Failed' },
                { value: 'running', label: 'Running' },
                { value: 'queued', label: 'Queued' },
                { value: 'pending', label: 'Pending' },
                { value: 'cancelled', label: 'Cancelled' },
              ]}
              value={statusFilter}
              onChange={(value) => setStatusFilter(value || 'all')}
            />
            <Select
              placeholder="All types"
              data={[
                { value: 'all', label: 'All Types' },
                { value: 'manual', label: 'Manual' },
                { value: 'scheduled', label: 'Scheduled' },
                { value: 'event_triggered', label: 'Event Triggered' },
                { value: 'chained', label: 'Chained' },
              ]}
              value={typeFilter}
              onChange={(value) => setTypeFilter(value || 'all')}
            />
          </Group>
          <Group>
            <DatePickerInput
              type="range"
              placeholder="Pick date range"
              value={dateRange}
              onChange={setDateRange}
              clearable
              style={{ flex: 1 }}
            />
            <Button variant="light" onClick={fetchJobs} loading={loading}>
              Refresh
            </Button>
          </Group>
        </Stack>
      </Paper>

      {/* Results Table */}
      <Paper shadow="sm" p="md" withBorder>
        <Group justify="space-between" mb="md">
          <Text size="sm" c="dimmed">
            Showing {filteredJobs.length} transfers
          </Text>
          <Select
            value={itemsPerPage.toString()}
            onChange={(value) => setItemsPerPage(parseInt(value || '25'))}
            data={[
              { value: '10', label: '10 per page' },
              { value: '25', label: '25 per page' },
              { value: '50', label: '50 per page' },
              { value: '100', label: '100 per page' },
            ]}
            style={{ width: 150 }}
          />
        </Group>

        <Table striped highlightOnHover withTableBorder>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Transfer</Table.Th>
              <Table.Th>Type</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Path</Table.Th>
              <Table.Th>Size</Table.Th>
              <Table.Th>Created</Table.Th>
              <Table.Th>Duration</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {rows.length > 0 ? rows : (
              <Table.Tr>
                <Table.Td colSpan={8} style={{ textAlign: 'center' }}>
                  <Text c="dimmed">No transfers found</Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>

        {totalPages > 1 && (
          <Group justify="center" mt="lg">
            <Pagination
              value={page}
              onChange={setPage}
              total={totalPages}
            />
          </Group>
        )}
      </Paper>

      {selectedJob && showDetails && (
        <JobDetailsModal
          job={selectedJob}
          opened={showDetails}
          onClose={() => {
            setShowDetails(false);
            setSelectedJob(null);
          }}
        />
      )}
    </Container>
  );
}