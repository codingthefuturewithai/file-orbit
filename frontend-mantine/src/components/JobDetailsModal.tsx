import { Modal, Stack, Group, Text, Badge, Progress, Table, Divider, ScrollArea } from '@mantine/core';
import type { Job, Transfer } from '../types';
import { formatBytes } from '../utils/format';
import { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';

interface JobDetailsModalProps {
  job: Job;
  opened: boolean;
  onClose: () => void;
}

const statusColors: Record<string, string> = {
  pending: 'gray',
  queued: 'blue',
  running: 'cyan',
  completed: 'green',
  failed: 'red',
  cancelled: 'orange',
  retrying: 'yellow',
  in_progress: 'cyan',
};

export default function JobDetailsModal({ job, opened, onClose }: JobDetailsModalProps) {
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const { callApi } = useApi();

  useEffect(() => {
    if (opened && job.id) {
      fetchTransfers();
    }
  }, [opened, job.id]);

  const fetchTransfers = async () => {
    try {
      const response = await callApi<Transfer[]>(`/jobs/${job.id}/transfers`, 'GET');
      if (response) {
        setTransfers(response);
      }
    } catch (error) {
      console.error('Failed to fetch transfers:', error);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  return (
    <Modal 
      opened={opened} 
      onClose={onClose} 
      title="Transfer Details" 
      size="xl"
    >
      <Stack>
        {/* Job Information */}
        <div>
          <Text size="lg" fw={600} mb="sm">Job Information</Text>
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Name:</Text>
              <Text size="sm">{job.name}</Text>
            </Group>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Type:</Text>
              <Badge variant="light">{job.type}</Badge>
            </Group>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Status:</Text>
              <Badge color={statusColors[job.status] || 'gray'}>{job.status}</Badge>
            </Group>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Created:</Text>
              <Text size="sm">{formatDate(job.created_at)}</Text>
            </Group>
            {job.started_at && (
              <Group justify="space-between">
                <Text size="sm" c="dimmed">Started:</Text>
                <Text size="sm">{formatDate(job.started_at)}</Text>
              </Group>
            )}
            {job.completed_at && (
              <Group justify="space-between">
                <Text size="sm" c="dimmed">Completed:</Text>
                <Text size="sm">{formatDate(job.completed_at)}</Text>
              </Group>
            )}
            {job.error_message && (
              <div>
                <Text size="sm" c="dimmed">Error:</Text>
                <Text size="sm" c="red">{job.error_message}</Text>
              </div>
            )}
          </Stack>
        </div>

        <Divider />

        {/* Transfer Information */}
        <div>
          <Text size="lg" fw={600} mb="sm">Transfer Configuration</Text>
          <Stack gap="xs">
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Source Path:</Text>
              <Text size="sm">{job.source_path}</Text>
            </Group>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Destination Path:</Text>
              <Text size="sm">{job.destination_path}</Text>
            </Group>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">File Pattern:</Text>
              <Text size="sm">{job.file_pattern || '*'}</Text>
            </Group>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Delete After Transfer:</Text>
              <Badge color={job.delete_source_after_transfer ? 'red' : 'green'}>
                {job.delete_source_after_transfer ? 'Yes' : 'No'}
              </Badge>
            </Group>
          </Stack>
        </div>

        <Divider />

        {/* Progress Information */}
        <div>
          <Text size="lg" fw={600} mb="sm">Progress</Text>
          <Stack gap="md">
            <div>
              <Group justify="space-between" mb="xs">
                <Text size="sm">Overall Progress</Text>
                <Text size="sm">{job.progress_percentage.toFixed(1)}%</Text>
              </Group>
              <Progress value={job.progress_percentage} size="lg" />
            </div>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Files:</Text>
              <Text size="sm">{job.transferred_files} / {job.total_files}</Text>
            </Group>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Size:</Text>
              <Text size="sm">{formatBytes(job.transferred_bytes)} / {formatBytes(job.total_bytes)}</Text>
            </Group>
          </Stack>
        </div>

        <Divider />

        {/* File Transfers */}
        <div>
          <Text size="lg" fw={600} mb="sm">File Transfers</Text>
          <ScrollArea h={200}>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>File Name</Table.Th>
                  <Table.Th>Size</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Progress</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {transfers.map((transfer) => (
                  <Table.Tr key={transfer.id}>
                    <Table.Td>{transfer.file_name}</Table.Td>
                    <Table.Td>{formatBytes(transfer.file_size)}</Table.Td>
                    <Table.Td>
                      <Badge size="sm" color={statusColors[transfer.status] || 'gray'}>
                        {transfer.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>{transfer.progress_percentage.toFixed(1)}%</Table.Td>
                  </Table.Tr>
                ))}
                {transfers.length === 0 && (
                  <Table.Tr>
                    <Table.Td colSpan={4} style={{ textAlign: 'center' }}>
                      <Text c="dimmed" size="sm">No file transfers yet</Text>
                    </Table.Td>
                  </Table.Tr>
                )}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        </div>
      </Stack>
    </Modal>
  );
}