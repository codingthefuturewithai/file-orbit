import { useState, useEffect } from 'react';
import { Modal, Stepper, Button, Group, TextInput, Select, Checkbox, Stack, Radio } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useNavigate } from 'react-router-dom';
import type { Endpoint, TransferTemplate } from '../types';
import { useApi } from '../hooks/useApi';

interface CreateTransferFormProps {
  opened: boolean;
  onClose: () => void;
}

interface FormValues {
  name: string;
  type: 'manual' | 'scheduled' | 'template';
  template_id?: string;
  source_endpoint_id: string;
  source_path: string;
  destination_endpoint_id: string;
  destination_path: string;
  file_pattern: string;
  delete_source_after_transfer: boolean;
  schedule?: string;
  schedule_type?: 'daily' | 'weekly' | 'custom';
  schedule_time?: string;
  schedule_days?: string[];
}

export default function CreateTransferForm({ opened, onClose }: CreateTransferFormProps) {
  const [active, setActive] = useState(0);
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [templates, setTemplates] = useState<TransferTemplate[]>([]);
  const { callApi, loading } = useApi();
  const navigate = useNavigate();

  const form = useForm<FormValues>({
    initialValues: {
      name: '',
      type: 'manual',
      template_id: undefined,
      source_endpoint_id: '',
      source_path: '',
      destination_endpoint_id: '',
      destination_path: '',
      file_pattern: '*',
      delete_source_after_transfer: false,
      schedule: undefined,
      schedule_type: 'daily',
      schedule_time: '00:00',
      schedule_days: [],
    },
    validate: (values) => {
      if (active === 0) {
        return {
          name: !values.name ? 'Transfer name is required' : null,
          template_id: values.type === 'template' && !values.template_id ? 'Please select a template' : null,
        };
      }
      if (active === 1) {
        return {
          source_endpoint_id: !values.source_endpoint_id ? 'Source endpoint is required' : null,
          source_path: !values.source_path ? 'Source path is required' : null,
        };
      }
      if (active === 2) {
        return {
          destination_endpoint_id: !values.destination_endpoint_id ? 'Destination endpoint is required' : null,
          destination_path: !values.destination_path ? 'Destination path is required' : null,
        };
      }
      return {};
    },
  });

  useEffect(() => {
    if (opened) {
      fetchEndpoints();
      fetchTemplates();
    }
  }, [opened]);

  useEffect(() => {
    if (form.values.type === 'template' && form.values.template_id) {
      loadTemplate(form.values.template_id);
    }
  }, [form.values.template_id]);

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

  const fetchTemplates = async () => {
    try {
      const response = await callApi<TransferTemplate[]>('/transfer-templates', 'GET');
      if (response) {
        setTemplates(response.filter(t => t.is_active));
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const loadTemplate = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      form.setValues({
        ...form.values,
        source_endpoint_id: template.source_endpoint_id,
        destination_endpoint_id: template.destination_endpoint_id,
        destination_path: template.destination_path_template,
        file_pattern: template.file_pattern,
        delete_source_after_transfer: template.delete_source_after_transfer,
      });
    }
  };

  const buildSchedule = () => {
    const { schedule_type, schedule_time, schedule_days } = form.values;
    if (form.values.type !== 'scheduled') return undefined;

    switch (schedule_type) {
      case 'daily':
        return `0 ${schedule_time?.split(':')[1] || '0'} ${schedule_time?.split(':')[0] || '0'} * * *`;
      case 'weekly':
        return `0 ${schedule_time?.split(':')[1] || '0'} ${schedule_time?.split(':')[0] || '0'} * * ${schedule_days?.join(',') || '1'}`;
      default:
        return form.values.schedule;
    }
  };

  const handleSubmit = async () => {
    const validation = form.validate();
    if (validation.hasErrors) return;

    try {
      const jobData = {
        name: form.values.name,
        type: form.values.type === 'template' ? 'manual' : form.values.type,
        source_endpoint_id: form.values.source_endpoint_id,
        source_path: form.values.source_path,
        destination_endpoint_id: form.values.destination_endpoint_id,
        destination_path: form.values.destination_path,
        file_pattern: form.values.file_pattern,
        delete_source_after_transfer: form.values.delete_source_after_transfer,
        schedule: buildSchedule(),
        is_active: true,
      };

      const response = await callApi('/jobs', 'POST', jobData);
      
      if (response && form.values.type === 'manual') {
        // Execute manual transfers immediately
        await callApi(`/jobs/${response.id}/execute`, 'POST');
      }

      notifications.show({
        title: 'Success',
        message: form.values.type === 'manual' 
          ? 'Transfer created and started'
          : 'Transfer created successfully',
        color: 'green',
      });

      onClose();
      navigate('/transfers');
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'Failed to create transfer',
        color: 'red',
      });
    }
  };

  const nextStep = () => {
    const validation = form.validate();
    if (!validation.hasErrors) {
      setActive((current) => (current < 4 ? current + 1 : current));
    }
  };

  const prevStep = () => setActive((current) => (current > 0 ? current - 1 : current));

  const shouldShowStep = (step: number) => {
    if (step === 4 && form.values.type !== 'scheduled') return false;
    return true;
  };

  const getActiveStep = () => {
    let step = active;
    if (active === 4 && form.values.type !== 'scheduled') {
      step = 3;
    }
    return step;
  };

  return (
    <Modal 
      opened={opened} 
      onClose={onClose} 
      title="Create Transfer" 
      size="xl"
    >
      <Stepper active={getActiveStep()} onStepClick={setActive}>
        {/* Step 1: Basic Info */}
        <Stepper.Step label="Basic Info">
          <Stack mt="md">
            <TextInput
              label="Transfer Name"
              placeholder="My Transfer Job"
              required
              {...form.getInputProps('name')}
            />
            
            <Radio.Group
              label="Transfer Type"
              {...form.getInputProps('type')}
            >
              <Stack mt="xs">
                <Radio value="manual" label="Manual - Execute immediately" />
                <Radio value="scheduled" label="Scheduled - Run on schedule" />
                <Radio value="template" label="From Template - Use existing template" />
              </Stack>
            </Radio.Group>

            {form.values.type === 'template' && (
              <Select
                label="Select Template"
                placeholder="Choose a template"
                data={templates.map(t => ({ value: t.id, label: t.name }))}
                {...form.getInputProps('template_id')}
              />
            )}
          </Stack>
        </Stepper.Step>

        {/* Step 2: Source Configuration */}
        <Stepper.Step label="Source">
          <Stack mt="md">
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

            <TextInput
              label="Source Path"
              placeholder="/path/to/source/files"
              description="Path on the source endpoint"
              required
              {...form.getInputProps('source_path')}
            />
          </Stack>
        </Stepper.Step>

        {/* Step 3: Destination Configuration */}
        <Stepper.Step label="Destination">
          <Stack mt="md">
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
              label="Destination Path"
              placeholder="/path/to/destination/{year}/{month}/{day}/{filename}"
              description="Path on the destination endpoint. Supports variables: {year}, {month}, {day}, {timestamp}, {filename}"
              required
              {...form.getInputProps('destination_path')}
            />
          </Stack>
        </Stepper.Step>

        {/* Step 4: Transfer Options */}
        <Stepper.Step label="Options">
          <Stack mt="md">
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
          </Stack>
        </Stepper.Step>

        {/* Step 5: Schedule (only for scheduled transfers) */}
        {shouldShowStep(4) && (
          <Stepper.Step label="Schedule">
            <Stack mt="md">
              <Radio.Group
                label="Schedule Type"
                {...form.getInputProps('schedule_type')}
              >
                <Stack mt="xs">
                  <Radio value="daily" label="Daily" />
                  <Radio value="weekly" label="Weekly" />
                  <Radio value="custom" label="Custom Cron Expression" />
                </Stack>
              </Radio.Group>

              {form.values.schedule_type !== 'custom' && (
                <TextInput
                  label="Time"
                  type="time"
                  {...form.getInputProps('schedule_time')}
                />
              )}

              {form.values.schedule_type === 'weekly' && (
                <Checkbox.Group
                  label="Days of Week"
                  {...form.getInputProps('schedule_days')}
                >
                  <Group mt="xs">
                    <Checkbox value="1" label="Mon" />
                    <Checkbox value="2" label="Tue" />
                    <Checkbox value="3" label="Wed" />
                    <Checkbox value="4" label="Thu" />
                    <Checkbox value="5" label="Fri" />
                    <Checkbox value="6" label="Sat" />
                    <Checkbox value="0" label="Sun" />
                  </Group>
                </Checkbox.Group>
              )}

              {form.values.schedule_type === 'custom' && (
                <TextInput
                  label="Cron Expression"
                  placeholder="0 0 * * *"
                  description="Enter a valid cron expression"
                  {...form.getInputProps('schedule')}
                />
              )}
            </Stack>
          </Stepper.Step>
        )}
      </Stepper>

      <Group justify="flex-end" mt="xl">
        <Button variant="default" onClick={onClose}>
          Cancel
        </Button>
        {active > 0 && (
          <Button variant="default" onClick={prevStep}>
            Back
          </Button>
        )}
        {active < (form.values.type === 'scheduled' ? 4 : 3) ? (
          <Button onClick={nextStep}>Next</Button>
        ) : (
          <Button onClick={handleSubmit} loading={loading}>
            Create Transfer
          </Button>
        )}
      </Group>
    </Modal>
  );
}