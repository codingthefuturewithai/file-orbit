import { useState, useEffect, useCallback } from 'react';
import { Table, Button, Badge, Group, Progress, Text, ActionIcon, Tooltip, Stack } from '@mantine/core';
import { IconPlayerPause, IconPlayerPlay, IconRefresh, IconX, IconEye, IconEdit, IconLink } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { modals } from '@mantine/modals';
import type { Job } from '../../types';
import { useApi } from '../../hooks/useApi';
import { formatBytes } from '../../utils/format';
import JobDetailsModal from '../../components/JobDetailsModal';
import EditJobModal from '../../components/EditJobModal';

const statusColors: Record<string, string> = {
  pending: 'gray',
  queued: 'blue',
  running: 'cyan',
  completed: 'green',
  failed: 'red',
  cancelled: 'orange',
  retrying: 'yellow',
};

export default function TransferList() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const { callApi, loading } = useApi();

  const fetchJobs = useCallback(async () => {
    try {
      const response = await callApi<Job[]>('/jobs', 'GET');
      if (response) {
        // Filter for active transfers (running, queued, pending, retrying)
        const activeJobs = response.filter(job => 
          ['running', 'queued', 'pending', 'retrying'].includes(job.status)
        );
        setJobs(activeJobs);
      }
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    }
  }, [callApi]);

  // Real-time polling every 5 seconds
  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, [fetchJobs]);

  const handleAction = async (jobId: string, action: 'pause' | 'resume' | 'retry' | 'cancel') => {
    try {
      await callApi(`/jobs/${jobId}/${action}`, 'POST');
      notifications.show({
        title: 'Success',
        message: `Transfer ${action}d successfully`,
        color: 'green',
      });
      fetchJobs();
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: `Failed to ${action} transfer`,
        color: 'red',
      });
    }
  };

  const confirmCancel = (jobId: string) => {
    modals.openConfirmModal({
      title: 'Cancel Transfer',
      centered: true,
      children: (
        <Text size="sm">
          Are you sure you want to cancel this transfer? This action cannot be undone.
        </Text>
      ),
      labels: { confirm: 'Cancel Transfer', cancel: 'Keep Running' },
      confirmProps: { color: 'red' },
      onCancel: () => {},
      onConfirm: () => handleAction(jobId, 'cancel'),
    });
  };

  const getActionButtons = (job: Job) => {
    const actions = [];

    if (job.status === 'running') {
      actions.push(
        <Tooltip label="Pause" key="pause">
          <ActionIcon color="orange" variant="light" onClick={() => handleAction(job.id, 'pause')}>
            <IconPlayerPause size={16} />
          </ActionIcon>
        </Tooltip>
      );
    }

    if (job.status === 'pending' || job.status === 'queued') {
      actions.push(
        <Tooltip label="Resume" key="resume">
          <ActionIcon color="green" variant="light" onClick={() => handleAction(job.id, 'resume')}>
            <IconPlayerPlay size={16} />
          </ActionIcon>
        </Tooltip>
      );
    }

    if (job.status === 'failed') {
      actions.push(
        <Tooltip label="Retry" key="retry">
          <ActionIcon color="blue" variant="light" onClick={() => handleAction(job.id, 'retry')}>
            <IconRefresh size={16} />
          </ActionIcon>
        </Tooltip>
      );
    }

    if (['running', 'pending', 'queued', 'retrying'].includes(job.status)) {
      actions.push(
        <Tooltip label="Cancel" key="cancel">
          <ActionIcon color="red" variant="light" onClick={() => confirmCancel(job.id)}>
            <IconX size={16} />
          </ActionIcon>
        </Tooltip>
      );
    }

    actions.push(
      <Tooltip label="View Details" key="details">
        <ActionIcon variant="light" onClick={() => {
          setSelectedJob(job);
          setShowDetails(true);
        }}>
          <IconEye size={16} />
        </ActionIcon>
      </Tooltip>
    );

    actions.push(
      <Tooltip label="Edit" key="edit">
        <ActionIcon variant="light" onClick={() => {
          setSelectedJob(job);
          setShowEdit(true);
        }}>
          <IconEdit size={16} />
        </ActionIcon>
      </Tooltip>
    );

    return <Group gap="xs">{actions}</Group>;
  };

  const formatTransferRate = (bytesPerSecond?: number) => {
    if (!bytesPerSecond) return '-';
    return `${formatBytes(bytesPerSecond)}/s`;
  };

  const formatETA = (job: Job) => {
    if (!job.started_at || job.status !== 'running') return '-';
    
    const elapsed = Date.now() - new Date(job.started_at).getTime();
    const rate = job.transferred_bytes / (elapsed / 1000);
    const remaining = job.total_bytes - job.transferred_bytes;
    
    if (rate <= 0) return '-';
    
    const etaSeconds = remaining / rate;
    const etaMinutes = Math.floor(etaSeconds / 60);
    const etaHours = Math.floor(etaMinutes / 60);
    
    if (etaHours > 0) {
      return `${etaHours}h ${etaMinutes % 60}m`;
    } else if (etaMinutes > 0) {
      return `${etaMinutes}m ${Math.floor(etaSeconds % 60)}s`;
    } else {
      return `${Math.floor(etaSeconds)}s`;
    }
  };

  const rows = jobs.map((job) => (
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
          <Text size="xs" c="dimmed">{job.source_path} → {job.destination_path}</Text>
        </Stack>
      </Table.Td>
      <Table.Td>
        <Badge color={statusColors[job.status] || 'gray'}>
          {job.status}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Stack gap="xs">
          <Progress value={job.progress_percentage} size="md" />
          <Group justify="space-between">
            <Text size="xs" c="dimmed">
              {formatBytes(job.transferred_bytes)} / {formatBytes(job.total_bytes)}
            </Text>
            <Text size="xs" c="dimmed">
              {job.progress_percentage.toFixed(1)}%
            </Text>
          </Group>
        </Stack>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{job.transferred_files} / {job.total_files}</Text>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{formatTransferRate(job.status === 'running' && job.started_at ? 
          job.transferred_bytes / ((Date.now() - new Date(job.started_at).getTime()) / 1000) : undefined
        )}</Text>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{formatETA(job)}</Text>
      </Table.Td>
      <Table.Td>{getActionButtons(job)}</Table.Td>
    </Table.Tr>
  ));

  return (
    <>
      <Table striped highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Transfer Details</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Progress</Table.Th>
            <Table.Th>Files</Table.Th>
            <Table.Th>Rate</Table.Th>
            <Table.Th>ETA</Table.Th>
            <Table.Th>Actions</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {loading && rows.length === 0 ? (
            <Table.Tr>
              <Table.Td colSpan={7} style={{ textAlign: 'center' }}>
                <Text c="dimmed">Loading transfers...</Text>
              </Table.Td>
            </Table.Tr>
          ) : rows.length > 0 ? (
            rows
          ) : (
            <Table.Tr>
              <Table.Td colSpan={7} style={{ textAlign: 'center' }}>
                <Text c="dimmed">No active transfers</Text>
              </Table.Td>
            </Table.Tr>
          )}
        </Table.Tbody>
      </Table>

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

      {selectedJob && showEdit && (
        <EditJobModal
          job={selectedJob}
          opened={showEdit}
          onClose={() => {
            setShowEdit(false);
            setSelectedJob(null);
          }}
          onSave={() => {
            setShowEdit(false);
            setSelectedJob(null);
            fetchJobs();
          }}
        />
      )}
    </>
  );
}