import { useState, useEffect } from 'react';
import { Container, Title, Button, Group, Paper, Table, Badge, ActionIcon, Tooltip, Text, Stack } from '@mantine/core';
import { IconPlus, IconEdit, IconTrash, IconToggleLeft, IconToggleRight } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { modals } from '@mantine/modals';
import type { TransferTemplate } from '../../types';
import { useApi } from '../../hooks/useApi';
import TemplateModal from '../../components/TemplateModal';

const eventTypeColors: Record<string, string> = {
  's3:ObjectCreated': 'blue',
  'file:created': 'green',
  'file:modified': 'orange',
  'manual': 'gray',
};

export default function Templates() {
  const [templates, setTemplates] = useState<TransferTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<TransferTemplate | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const { callApi, loading } = useApi();

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await callApi<TransferTemplate[]>('/transfer-templates', 'GET');
      if (response) {
        setTemplates(response);
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const handleCreate = () => {
    setSelectedTemplate(null);
    setIsEdit(false);
    setShowModal(true);
  };

  const handleEdit = (template: TransferTemplate) => {
    setSelectedTemplate(template);
    setIsEdit(true);
    setShowModal(true);
  };

  const handleToggleActive = async (template: TransferTemplate) => {
    try {
      await callApi(`/transfer-templates/${template.id}`, 'PUT', {
        ...template,
        is_active: !template.is_active,
      });
      
      notifications.show({
        title: 'Success',
        message: `Template ${template.is_active ? 'deactivated' : 'activated'} successfully`,
        color: 'green',
      });
      
      fetchTemplates();
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to update template status',
        color: 'red',
      });
    }
  };

  const confirmDelete = (template: TransferTemplate) => {
    modals.openConfirmModal({
      title: 'Delete Template',
      centered: true,
      children: (
        <Text size="sm">
          Are you sure you want to delete template "{template.name}"? This action cannot be undone.
        </Text>
      ),
      labels: { confirm: 'Delete', cancel: 'Cancel' },
      confirmProps: { color: 'red' },
      onCancel: () => {},
      onConfirm: () => handleDelete(template),
    });
  };

  const handleDelete = async (template: TransferTemplate) => {
    try {
      await callApi(`/transfer-templates/${template.id}`, 'DELETE');
      
      notifications.show({
        title: 'Success',
        message: 'Template deleted successfully',
        color: 'green',
      });
      
      fetchTemplates();
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to delete template',
        color: 'red',
      });
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString();
  };

  const rows = templates.map((template) => (
    <Table.Tr key={template.id}>
      <Table.Td>
        <Stack gap="xs">
          <Text size="sm" fw={500}>{template.name}</Text>
          {template.description && (
            <Text size="xs" c="dimmed">{template.description}</Text>
          )}
        </Stack>
      </Table.Td>
      <Table.Td>
        <Badge color={eventTypeColors[template.event_type] || 'gray'} variant="light">
          {template.event_type}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Badge color={template.is_active ? 'green' : 'red'}>
          {template.is_active ? 'Active' : 'Inactive'}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{template.source_endpoint_id}</Text>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{template.destination_path_template}</Text>
      </Table.Td>
      <Table.Td>
        <Text size="sm">{template.file_pattern || '*'}</Text>
      </Table.Td>
      <Table.Td>
        <Stack gap="xs">
          <Text size="xs">{template.total_triggers || 0} triggers</Text>
          <Text size="xs" c="green">{template.successful_transfers || 0} success</Text>
          {template.failed_transfers > 0 && (
            <Text size="xs" c="red">{template.failed_transfers} failed</Text>
          )}
        </Stack>
      </Table.Td>
      <Table.Td>
        <Group gap="xs">
          <Tooltip label={template.is_active ? 'Deactivate' : 'Activate'}>
            <ActionIcon
              color={template.is_active ? 'red' : 'green'}
              variant="light"
              onClick={() => handleToggleActive(template)}
            >
              {template.is_active ? <IconToggleRight size={16} /> : <IconToggleLeft size={16} />}
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Edit">
            <ActionIcon variant="light" onClick={() => handleEdit(template)}>
              <IconEdit size={16} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Delete">
            <ActionIcon color="red" variant="light" onClick={() => confirmDelete(template)}>
              <IconTrash size={16} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Table.Td>
    </Table.Tr>
  ));

  return (
    <Container size="xl">
      <Group justify="space-between" mb="xl">
        <Title order={2}>Transfer Templates</Title>
        <Button 
          leftSection={<IconPlus size={16} />}
          onClick={handleCreate}
        >
          Create Template
        </Button>
      </Group>

      <Paper shadow="sm" p="md" withBorder>
        <Table striped highlightOnHover withTableBorder>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Template</Table.Th>
              <Table.Th>Event Type</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Source</Table.Th>
              <Table.Th>Destination</Table.Th>
              <Table.Th>Pattern</Table.Th>
              <Table.Th>Statistics</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {loading && templates.length === 0 ? (
              <Table.Tr>
                <Table.Td colSpan={8} style={{ textAlign: 'center' }}>
                  <Text c="dimmed">Loading templates...</Text>
                </Table.Td>
              </Table.Tr>
            ) : rows.length > 0 ? (
              rows
            ) : (
              <Table.Tr>
                <Table.Td colSpan={8} style={{ textAlign: 'center' }}>
                  <Text c="dimmed">No templates found</Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </Paper>

      {showModal && (
        <TemplateModal
          template={selectedTemplate}
          opened={showModal}
          onClose={() => {
            setShowModal(false);
            setSelectedTemplate(null);
          }}
          onSave={() => {
            setShowModal(false);
            setSelectedTemplate(null);
            fetchTemplates();
          }}
        />
      )}
    </Container>
  );
}