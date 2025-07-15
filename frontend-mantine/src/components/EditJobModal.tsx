import { Modal, TextInput, Stack, Button, Group, Checkbox, Text } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import type { Job } from '../types';
import { useApi } from '../hooks/useApi';

interface EditJobModalProps {
  job: Job;
  opened: boolean;
  onClose: () => void;
  onSave: () => void;
}

export default function EditJobModal({ job, opened, onClose, onSave }: EditJobModalProps) {
  const { callApi, loading } = useApi();

  const form = useForm({
    initialValues: {
      source_path: job.source_path,
      destination_path: job.destination_path,
      file_pattern: job.file_pattern || '*',
      delete_source_after_transfer: job.delete_source_after_transfer,
      execute_immediately: false,
    },
    validate: {
      source_path: (value) => (!value ? 'Source path is required' : null),
      destination_path: (value) => (!value ? 'Destination path is required' : null),
    },
  });

  const handleSubmit = async (values: typeof form.values) => {
    try {
      const endpoint = values.execute_immediately 
        ? `/jobs/${job.id}/update-and-execute`
        : `/jobs/${job.id}`;

      await callApi(endpoint, 'PUT', {
        source_path: values.source_path,
        destination_path: values.destination_path,
        file_pattern: values.file_pattern,
        delete_source_after_transfer: values.delete_source_after_transfer,
      });

      notifications.show({
        title: 'Success',
        message: values.execute_immediately 
          ? 'Transfer updated and execution started'
          : 'Transfer updated successfully',
        color: 'green',
      });

      onSave();
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to update transfer',
        color: 'red',
      });
    }
  };

  return (
    <Modal 
      opened={opened} 
      onClose={onClose} 
      title="Edit Transfer" 
      size="md"
    >
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack>
          <TextInput
            label="Source Path"
            description="Path on the source endpoint"
            required
            {...form.getInputProps('source_path')}
          />

          <TextInput
            label="Destination Path"
            description="Path on the destination endpoint. Supports variables: {year}, {month}, {day}, {timestamp}, {filename}"
            required
            {...form.getInputProps('destination_path')}
          />

          <TextInput
            label="File Pattern"
            description="Pattern to match files (e.g., *.mp4, *.mov)"
            {...form.getInputProps('file_pattern')}
          />

          <Checkbox
            label="Delete source files after successful transfer"
            {...form.getInputProps('delete_source_after_transfer', { type: 'checkbox' })}
          />

          {job.status === 'failed' && (
            <Checkbox
              label="Execute immediately after saving"
              {...form.getInputProps('execute_immediately', { type: 'checkbox' })}
            />
          )}

          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={loading}>
              Save Changes
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}