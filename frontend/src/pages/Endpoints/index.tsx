import { useState, useEffect } from 'react';
import {
  Container,
  Title,
  Text,
  Button,
  Table,
  Badge,
  Group,
  ActionIcon,
  Stack,
  LoadingOverlay,
} from '@mantine/core';
import { modals } from '@mantine/modals';
import { notifications } from '@mantine/notifications';
import { IconPlus, IconEdit, IconTrash } from '@tabler/icons-react';
import api from '../../services/api';
import type { Endpoint } from '../../types/index';
import EndpointModal from '../../components/EndpointModal';
import { formatBytes } from '../../utils/format';

const EndpointsPage = () => {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpened, setModalOpened] = useState(false);
  const [selectedEndpoint, setSelectedEndpoint] = useState<Endpoint | null>(null);

  const fetchEndpoints = async () => {
    try {
      setLoading(true);
      const response = await api.get('/endpoints/');
      setEndpoints(response.data);
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to fetch endpoints',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEndpoints();
  }, []);

  const handleCreate = () => {
    setSelectedEndpoint(null);
    setModalOpened(true);
  };

  const handleEdit = (endpoint: Endpoint) => {
    setSelectedEndpoint(endpoint);
    setModalOpened(true);
  };

  const handleDelete = (endpoint: Endpoint) => {
    modals.openConfirmModal({
      title: 'Delete Endpoint',
      children: (
        <Text size="sm">
          Are you sure you want to delete "{endpoint.name}"? This action cannot be undone.
        </Text>
      ),
      labels: { confirm: 'Delete', cancel: 'Cancel' },
      confirmProps: { color: 'red' },
      onConfirm: async () => {
        try {
          await api.delete(`/endpoints/${endpoint.id}/`);
          notifications.show({
            title: 'Success',
            message: 'Endpoint deleted successfully',
            color: 'green',
          });
          fetchEndpoints();
        } catch (error) {
          notifications.show({
            title: 'Error',
            message: 'Failed to delete endpoint',
            color: 'red',
          });
        }
      },
    });
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      local: 'blue',
      s3: 'orange',
      smb: 'grape',
      sftp: 'teal',
    };
    return colors[type] || 'gray';
  };

  const rows = endpoints.map((endpoint) => (
    <Table.Tr key={endpoint.id}>
      <Table.Td>{endpoint.name}</Table.Td>
      <Table.Td>
        <Badge color={getTypeColor(endpoint.type)}>
          {endpoint.type.toUpperCase()}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Badge color={endpoint.is_active ? 'green' : 'red'}>
          {endpoint.is_active ? 'Active' : 'Inactive'}
        </Badge>
      </Table.Td>
      <Table.Td>{endpoint.max_concurrent_transfers}</Table.Td>
      <Table.Td>{endpoint.total_transfers || 0}</Table.Td>
      <Table.Td>{formatBytes(endpoint.total_bytes_transferred || 0)}</Table.Td>
      <Table.Td>
        <Group gap="xs">
          <ActionIcon
            variant="subtle"
            color="blue"
            onClick={() => handleEdit(endpoint)}
          >
            <IconEdit size={16} />
          </ActionIcon>
          <ActionIcon
            variant="subtle"
            color="red"
            onClick={() => handleDelete(endpoint)}
          >
            <IconTrash size={16} />
          </ActionIcon>
        </Group>
      </Table.Td>
    </Table.Tr>
  ));

  return (
    <Container size="xl">
      <Stack>
        <Group justify="space-between">
          <div>
            <Title order={2}>Endpoints</Title>
            <Text c="dimmed" size="sm">Manage storage endpoints</Text>
          </div>
          <Button leftSection={<IconPlus size={16} />} onClick={handleCreate}>
            Add Endpoint
          </Button>
        </Group>

        <div style={{ position: 'relative' }}>
          <LoadingOverlay visible={loading} />
          <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Name</Table.Th>
                <Table.Th>Type</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Max Concurrent</Table.Th>
                <Table.Th>Total Transfers</Table.Th>
                <Table.Th>Data Transferred</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {rows.length > 0 ? rows : (
                <Table.Tr>
                  <Table.Td colSpan={7} style={{ textAlign: 'center' }}>
                    <Text c="dimmed">No endpoints found</Text>
                  </Table.Td>
                </Table.Tr>
              )}
            </Table.Tbody>
          </Table>
        </div>

        <EndpointModal
          opened={modalOpened}
          onClose={() => setModalOpened(false)}
          endpoint={selectedEndpoint}
          onSuccess={fetchEndpoints}
        />
      </Stack>
    </Container>
  );
};

export default EndpointsPage;