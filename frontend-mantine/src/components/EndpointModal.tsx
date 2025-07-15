import { Modal, TextInput, Select, Checkbox, NumberInput, Button, Stack, Group, PasswordInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useEffect } from 'react';
import api from '../services/api';
import type { Endpoint } from '../types/index';
import { parseBandwidth, formatBandwidth } from '../utils/format';

interface EndpointModalProps {
  opened: boolean;
  onClose: () => void;
  endpoint?: Endpoint | null;
  onSuccess: () => void;
}

const EndpointModal = ({ opened, onClose, endpoint, onSuccess }: EndpointModalProps) => {
  const form = useForm({
    initialValues: {
      name: '',
      type: 'local' as Endpoint['type'],
      is_active: true,
      max_concurrent_transfers: 5,
      max_bandwidth: '',
      config: {} as Record<string, any>,
    },
  });

  useEffect(() => {
    if (endpoint) {
      form.setValues({
        name: endpoint.name,
        type: endpoint.type,
        is_active: endpoint.is_active,
        max_concurrent_transfers: endpoint.max_concurrent_transfers,
        max_bandwidth: endpoint.max_bandwidth ? formatBandwidth(endpoint.max_bandwidth) : '',
        config: { ...endpoint.config },
      });
    } else {
      form.reset();
    }
  }, [endpoint]);

  const handleSubmit = async (values: typeof form.values) => {
    try {
      const payload = {
        ...values,
        max_bandwidth: values.max_bandwidth ? parseBandwidth(values.max_bandwidth) : undefined,
      };

      if (endpoint) {
        await api.put(`/endpoints/${endpoint.id}/`, payload);
        notifications.show({
          title: 'Success',
          message: 'Endpoint updated successfully',
          color: 'green',
        });
      } else {
        await api.post('/endpoints/', payload);
        notifications.show({
          title: 'Success',
          message: 'Endpoint created successfully',
          color: 'green',
        });
      }
      onSuccess();
      onClose();
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.detail || 'Failed to save endpoint',
        color: 'red',
      });
    }
  };

  const renderConfigFields = () => {
    const { type, config } = form.values;

    switch (type) {
      case 'local':
        return (
          <TextInput
            label="Path"
            placeholder="/path/to/directory"
            required
            {...form.getInputProps('config.path')}
          />
        );

      case 's3':
        return (
          <>
            <TextInput
              label="Bucket"
              placeholder="my-bucket"
              required
              {...form.getInputProps('config.bucket')}
            />
            <TextInput
              label="Region"
              placeholder="us-east-1"
              required
              {...form.getInputProps('config.region')}
            />
            <TextInput
              label="Access Key"
              placeholder="AKIAIOSFODNN7EXAMPLE"
              required
              {...form.getInputProps('config.access_key')}
            />
            <PasswordInput
              label="Secret Key"
              placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
              required={!endpoint}
              {...form.getInputProps('config.secret_key')}
            />
          </>
        );

      case 'smb':
        return (
          <>
            <TextInput
              label="Host"
              placeholder="192.168.1.100"
              required
              {...form.getInputProps('config.host')}
            />
            <TextInput
              label="Share"
              placeholder="shared-folder"
              required
              {...form.getInputProps('config.share')}
            />
            <TextInput
              label="Username"
              placeholder="domain\\username"
              required
              {...form.getInputProps('config.user')}
            />
            <PasswordInput
              label="Password"
              required={!endpoint}
              {...form.getInputProps('config.password')}
            />
            <TextInput
              label="Domain"
              placeholder="WORKGROUP"
              {...form.getInputProps('config.domain')}
            />
          </>
        );

      case 'sftp':
        return (
          <>
            <TextInput
              label="Host"
              placeholder="sftp.example.com"
              required
              {...form.getInputProps('config.host')}
            />
            <NumberInput
              label="Port"
              placeholder="22"
              defaultValue={22}
              {...form.getInputProps('config.port')}
            />
            <TextInput
              label="Username"
              placeholder="username"
              required
              {...form.getInputProps('config.user')}
            />
            <PasswordInput
              label="Password"
              placeholder="Leave empty to use SSH key"
              {...form.getInputProps('config.password')}
            />
            <TextInput
              label="SSH Key File"
              placeholder="/path/to/id_rsa"
              {...form.getInputProps('config.key_file')}
            />
            <PasswordInput
              label="Key Passphrase"
              placeholder="Passphrase for SSH key"
              {...form.getInputProps('config.key_passphrase')}
            />
          </>
        );

      default:
        return null;
    }
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={endpoint ? 'Edit Endpoint' : 'Create Endpoint'}
      size="md"
    >
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack>
          <TextInput
            label="Name"
            placeholder="My Endpoint"
            required
            {...form.getInputProps('name')}
          />

          <Select
            label="Type"
            data={[
              { value: 'local', label: 'Local' },
              { value: 's3', label: 'Amazon S3' },
              { value: 'smb', label: 'SMB/CIFS' },
              { value: 'sftp', label: 'SFTP' },
            ]}
            required
            {...form.getInputProps('type')}
          />

          {renderConfigFields()}

          <NumberInput
            label="Max Concurrent Transfers"
            min={1}
            max={100}
            required
            {...form.getInputProps('max_concurrent_transfers')}
          />

          <TextInput
            label="Max Bandwidth"
            placeholder="10M, 1G, or leave empty for unlimited"
            {...form.getInputProps('max_bandwidth')}
          />

          <Checkbox
            label="Active"
            {...form.getInputProps('is_active', { type: 'checkbox' })}
          />

          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">
              {endpoint ? 'Update' : 'Create'}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
};

export default EndpointModal;