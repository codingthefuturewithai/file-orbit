import { useEffect, useState } from 'react';
import { Modal, TextInput, Textarea, Select, Checkbox, Stack, Button, Group, Text, Divider } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconPlus, IconTrash } from '@tabler/icons-react';
import type { TransferTemplate, Endpoint } from '../types';
import { useApi } from '../hooks/useApi';

interface TemplateModalProps {
  template: TransferTemplate | null;
  opened: boolean;
  onClose: () => void;
  onSave: () => void;
}

interface ChainRule {
  endpoint_id: string;
  path_template: string;
}

export default function TemplateModal({ template, opened, onClose, onSave }: TemplateModalProps) {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const { callApi, loading } = useApi();
  const isEdit = !!template;

  const form = useForm({
    initialValues: {
      name: template?.name || '',
      description: template?.description || '',
      event_type: template?.event_type || 's3:ObjectCreated',
      is_active: template?.is_active ?? true,
      source_endpoint_id: template?.source_endpoint_id || '',
      destination_endpoint_id: template?.destination_endpoint_id || '',
      destination_path_template: template?.destination_path_template || '',
      file_pattern: template?.file_pattern || '*',
      delete_source_after_transfer: template?.delete_source_after_transfer || false,
      chain_rules: template?.chain_rules || [],
      source_config: template?.source_config || {},
    },
    validate: {
      name: (value) => (!value ? 'Template name is required' : null),
      source_endpoint_id: (value) => (!value ? 'Source endpoint is required' : null),
      destination_endpoint_id: (value) => (!value ? 'Destination endpoint is required' : null),
      destination_path_template: (value) => (!value ? 'Destination path is required' : null),
    },
  });

  useEffect(() => {
    if (opened) {
      fetchEndpoints();
    }
  }, [opened]);

  const fetchEndpoints = async () => {
    try {
      const response = await callApi<Endpoint[]>('/endpoints', 'GET');
      if (response) {
        setEndpoints(response.filter(ep => ep.is_active));
      }
    } catch (error) {
      console.error('Failed to fetch endpoints:', error);
    }
  };

  const handleSubmit = async (values: typeof form.values) => {
    try {
      const endpoint = isEdit ? `/transfer-templates/${template.id}` : '/transfer-templates';
      const method = isEdit ? 'PUT' : 'POST';

      await callApi(endpoint, method, values);

      notifications.show({
        title: 'Success',
        message: `Template ${isEdit ? 'updated' : 'created'} successfully`,
        color: 'green',
      });

      onSave();
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: `Failed to ${isEdit ? 'update' : 'create'} template`,
        color: 'red',
      });
    }
  };

  const addChainRule = () => {
    form.setFieldValue('chain_rules', [
      ...form.values.chain_rules,
      { endpoint_id: '', path_template: '' }
    ]);
  };

  const removeChainRule = (index: number) => {
    form.setFieldValue(
      'chain_rules',
      form.values.chain_rules.filter((_, i) => i !== index)
    );
  };

  const updateChainRule = (index: number, field: keyof ChainRule, value: string) => {
    const updatedRules = [...form.values.chain_rules];
    updatedRules[index] = { ...updatedRules[index], [field]: value };
    form.setFieldValue('chain_rules', updatedRules);
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={isEdit ? 'Edit Template' : 'Create Template'}
      size="lg"
    >
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack>
          <TextInput
            label="Template Name"
            placeholder="My Transfer Template"
            required
            {...form.getInputProps('name')}
          />

          <Textarea
            label="Description"
            placeholder="Describe what this template does"
            rows={2}
            {...form.getInputProps('description')}
          />

          <Select
            label="Event Type"
            required
            data={[
              { value: 's3:ObjectCreated', label: 'S3 Object Created' },
              { value: 'file:created', label: 'File Created' },
              { value: 'file:modified', label: 'File Modified' },
              { value: 'manual', label: 'Manual Trigger' },
            ]}
            {...form.getInputProps('event_type')}
          />

          <Checkbox
            label="Active"
            {...form.getInputProps('is_active', { type: 'checkbox' })}
          />

          <Divider label="Transfer Configuration" />

          <Select
            label="Source Endpoint"
            placeholder="Select source endpoint"
            required
            data={endpoints.map(ep => ({
              value: ep.id,
              label: `${ep.name} (${ep.type.toUpperCase()})`
            }))}
            {...form.getInputProps('source_endpoint_id')}
          />

          {form.values.event_type === 'file:created' || form.values.event_type === 'file:modified' ? (
            <TextInput
              label="Watch Path"
              placeholder="/path/to/watch"
              description="Path to monitor for file events"
              {...form.getInputProps('source_config.watch_path')}
            />
          ) : form.values.event_type === 's3:ObjectCreated' ? (
            <TextInput
              label="S3 Prefix"
              placeholder="uploads/"
              description="S3 prefix to monitor (optional)"
              {...form.getInputProps('source_config.prefix')}
            />
          ) : null}

          <Select
            label="Destination Endpoint"
            placeholder="Select destination endpoint"
            required
            data={endpoints.map(ep => ({
              value: ep.id,
              label: `${ep.name} (${ep.type.toUpperCase()})`
            }))}
            {...form.getInputProps('destination_endpoint_id')}
          />

          <TextInput
            label="Destination Path Template"
            placeholder="/archive/{year}/{month}/{day}/{filename}"
            description="Supports variables: {year}, {month}, {day}, {timestamp}, {filename}"
            required
            {...form.getInputProps('destination_path_template')}
          />

          <TextInput
            label="File Pattern"
            placeholder="*.mp4"
            description="Pattern to match files (e.g., *.mp4, *.mov, *)"
            {...form.getInputProps('file_pattern')}
          />

          <Checkbox
            label="Delete source files after successful transfer"
            {...form.getInputProps('delete_source_after_transfer', { type: 'checkbox' })}
          />

          <Divider label="Chain Rules (Optional)" />
          
          <Text size="sm" c="dimmed">
            Chain rules allow you to create additional transfers after the primary transfer completes
          </Text>

          {form.values.chain_rules.map((rule, index) => (
            <Group key={index} align="flex-end">
              <Select
                label={`Chain Endpoint ${index + 1}`}
                placeholder="Select endpoint"
                data={endpoints.map(ep => ({
                  value: ep.id,
                  label: `${ep.name} (${ep.type.toUpperCase()})`
                }))}
                value={rule.endpoint_id}
                onChange={(value) => updateChainRule(index, 'endpoint_id', value || '')}
                style={{ flex: 1 }}
              />
              <TextInput
                label="Path Template"
                placeholder="/backup/{year}/{month}/{filename}"
                value={rule.path_template}
                onChange={(e) => updateChainRule(index, 'path_template', e.currentTarget.value)}
                style={{ flex: 2 }}
              />
              <Button
                color="red"
                variant="light"
                onClick={() => removeChainRule(index)}
              >
                <IconTrash size={16} />
              </Button>
            </Group>
          ))}

          <Button
            variant="light"
            leftSection={<IconPlus size={16} />}
            onClick={addChainRule}
          >
            Add Chain Rule
          </Button>

          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={loading}>
              {isEdit ? 'Update' : 'Create'} Template
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}