import { useState, useEffect } from 'react';
import { Container, Title, Paper, Tabs, TextInput, NumberInput, Select, Switch, Button, Group, Stack, Text, Divider, PasswordInput, Loader, Center, Alert } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconDeviceFloppy, IconRefresh, IconAlertCircle } from '@tabler/icons-react';
import { useApi } from '../../hooks/useApi';

interface Setting {
  key: string;
  value: any;
  description?: string;
  category?: string;
  value_type: string;
  default_value?: any;
  is_visible: boolean;
  is_editable: boolean;
}

interface SettingCategory {
  category: string;
  settings: Setting[];
}

interface SettingsResponse {
  categories: SettingCategory[];
  total_settings: number;
}

interface GeneralSettings {
  rclone_binary_path: string;
  log_level: string;
  max_log_size_mb: number;
  log_retention_days: number;
  temp_directory: string;
  enable_atomic_delivery: boolean;
}

interface PerformanceSettings {
  default_max_concurrent: number;
  default_bandwidth_limit: string;
  buffer_size_mb: number;
  check_interval: number;
  enable_prometheus_metrics: boolean;
  metrics_port: number;
}

interface NotificationSettings {
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_password: string;
  smtp_from: string;
  enable_notifications: boolean;
  webhook_url: string;
  enable_webhook_notifications: boolean;
}

interface SecuritySettings {
  enable_ldap: boolean;
  ldap_server: string;
  ldap_base_dn: string;
  ldap_bind_dn: string;
  ldap_bind_password: string;
  api_key_expiry_days: number;
  enable_audit_logging: boolean;
  compliance_mode: string;
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState<string | null>('general');
  const [initialLoading, setInitialLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const { callApi, loading } = useApi();

  // General Settings Form
  const generalForm = useForm<GeneralSettings>({
    mode: 'uncontrolled',
    initialValues: {
      rclone_binary_path: '/usr/local/bin/rclone',
      log_level: 'info',
      max_log_size_mb: 100,
      log_retention_days: 30,
      temp_directory: '/tmp/file-orbit',
      enable_atomic_delivery: true,
    },
  });

  // Performance Settings Form
  const performanceForm = useForm<PerformanceSettings>({
    mode: 'uncontrolled',
    initialValues: {
      default_max_concurrent: 5,
      default_bandwidth_limit: '100M',
      buffer_size_mb: 16,
      check_interval: 5,
      enable_prometheus_metrics: true,
      metrics_port: 9090,
    },
  });

  // Notification Settings Form
  const notificationForm = useForm<NotificationSettings>({
    mode: 'uncontrolled',
    initialValues: {
      smtp_host: 'smtp.ctf.org',
      smtp_port: 587,
      smtp_user: '',
      smtp_password: '',
      smtp_from: 'file-orbit@ctf.org',
      enable_notifications: true,
      webhook_url: '',
      enable_webhook_notifications: false,
    },
  });

  // Security Settings Form
  const securityForm = useForm<SecuritySettings>({
    mode: 'uncontrolled',
    initialValues: {
      enable_ldap: false,
      ldap_server: 'ldap://ldap.ctf.org',
      ldap_base_dn: 'dc=ctf,dc=org',
      ldap_bind_dn: '',
      ldap_bind_password: '',
      api_key_expiry_days: 90,
      enable_audit_logging: true,
      compliance_mode: 'standard',
    },
  });

  // Load settings from API
  const loadSettings = async () => {
    try {
      const response = await callApi<SettingsResponse>('/settings/', 'GET');
      if (response && response.categories) {
        // Build form values objects for bulk update
        const generalValues: Partial<GeneralSettings> = {};
        const performanceValues: Partial<PerformanceSettings> = {};
        const notificationValues: Partial<NotificationSettings> = {};
        const securityValues: Partial<SecuritySettings> = {};

        response.categories.forEach((category) => {
          category.settings.forEach((setting: Setting) => {
            // Skip null values to avoid form errors
            if (setting.value === null || setting.value === undefined) {
              return;
            }
            
            // Extract the field name after the dot
            const fieldName = setting.key.split('.').pop() || '';
            
            // Collect values for bulk update
            if (setting.key.startsWith('general.')) {
              generalValues[fieldName as keyof GeneralSettings] = setting.value;
            } else if (setting.key.startsWith('throttling.')) {
              if (fieldName === 'default_max_concurrent' || fieldName === 'default_bandwidth_limit' || 
                  fieldName === 'buffer_size_mb' || fieldName === 'check_interval') {
                performanceValues[fieldName as keyof PerformanceSettings] = setting.value;
              }
            } else if (setting.key.startsWith('monitoring.')) {
              if (fieldName === 'enable_prometheus_metrics' || fieldName === 'metrics_port' ||
                  fieldName === 'webhook_url' || fieldName === 'enable_webhook_notifications') {
                performanceValues[fieldName as keyof PerformanceSettings] = setting.value;
              }
            } else if (setting.key.startsWith('email.')) {
              if (fieldName === 'smtp_host' || fieldName === 'smtp_port' || fieldName === 'smtp_user' ||
                  fieldName === 'smtp_password' || fieldName === 'smtp_from' || fieldName === 'enable_notifications') {
                notificationValues[fieldName as keyof NotificationSettings] = setting.value;
              }
            } else if (setting.key.startsWith('security.')) {
              securityValues[fieldName as keyof SecuritySettings] = setting.value;
            }
          });
        });

        // Bulk update form values
        if (Object.keys(generalValues).length > 0) {
          generalForm.setValues(generalValues);
        }
        if (Object.keys(performanceValues).length > 0) {
          performanceForm.setValues(performanceValues);
        }
        if (Object.keys(notificationValues).length > 0) {
          notificationForm.setValues(notificationValues);
        }
        if (Object.keys(securityValues).length > 0) {
          securityForm.setValues(securityValues);
        }
        
        setLoadError(null);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      setLoadError('Failed to load settings. Using default values.');
    } finally {
      setInitialLoading(false);
    }
  };

  // Load settings on first mount only
  useEffect(() => {
    loadSettings();
  }, []);

  const handleSave = async (section: string, values: any) => {
    try {
      // Convert form values to bulk update format with proper keys
      const updates: { [key: string]: any } = {};
      
      if (section === 'General') {
        Object.entries(values).forEach(([key, value]) => {
          updates[`general.${key}`] = value;
        });
      } else if (section === 'Performance') {
        Object.entries(values).forEach(([key, value]) => {
          if (['default_max_concurrent', 'default_bandwidth_limit', 'buffer_size_mb', 'check_interval'].includes(key)) {
            updates[`throttling.${key}`] = value;
          } else {
            updates[`monitoring.${key}`] = value;
          }
        });
      } else if (section === 'Notification') {
        Object.entries(values).forEach(([key, value]) => {
          if (key.startsWith('smtp_') || key === 'enable_notifications') {
            updates[`email.${key}`] = value;
          } else {
            updates[`monitoring.${key}`] = value;
          }
        });
      } else if (section === 'Security') {
        Object.entries(values).forEach(([key, value]) => {
          updates[`security.${key}`] = value;
        });
      }

      const response = await callApi('/settings/bulk-update', 'POST', { settings: updates });
      
      if (response) {
        notifications.show({
          title: 'Success',
          message: `${section} settings saved successfully`,
          color: 'green',
        });
      }
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: `Failed to save ${section} settings`,
        color: 'red',
      });
    }
  };

  const handleReset = async (section: string, form: any) => {
    try {
      const keys: string[] = [];
      
      if (section === 'General') {
        Object.keys(generalForm.getValues()).forEach(key => {
          keys.push(`general.${key}`);
        });
      } else if (section === 'Performance') {
        Object.keys(performanceForm.getValues()).forEach(key => {
          if (['default_max_concurrent', 'default_bandwidth_limit', 'buffer_size_mb', 'check_interval'].includes(key)) {
            keys.push(`throttling.${key}`);
          } else {
            keys.push(`monitoring.${key}`);
          }
        });
      } else if (section === 'Notification') {
        Object.keys(notificationForm.getValues()).forEach(key => {
          if (key.startsWith('smtp_') || key === 'enable_notifications') {
            keys.push(`email.${key}`);
          } else {
            keys.push(`monitoring.${key}`);
          }
        });
      } else if (section === 'Security') {
        Object.keys(securityForm.getValues()).forEach(key => {
          keys.push(`security.${key}`);
        });
      }
      
      // Reset each setting in the section
      for (const key of keys) {
        await callApi(`/settings/${key}/reset`, 'POST');
      }
      
      // Reload settings to get the reset values
      await loadSettings();
      
      notifications.show({
        title: 'Reset',
        message: `${section} settings reset to defaults`,
        color: 'blue',
      });
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: `Failed to reset ${section} settings`,
        color: 'red',
      });
    }
  };

  if (initialLoading) {
    return (
      <Container size="xl">
        <Title order={2} mb="xl">Settings</Title>
        <Paper shadow="sm" p="xl" withBorder>
          <Center>
            <Loader size="lg" />
          </Center>
        </Paper>
      </Container>
    );
  }

  return (
    <Container size="xl">
      <Title order={2} mb="xl">Settings</Title>

      {loadError && (
        <Alert icon={<IconAlertCircle size="1rem" />} color="yellow" mb="md">
          {loadError}
        </Alert>
      )}

      <Paper shadow="sm" p="md" withBorder>
        <Tabs value={activeTab} onChange={setActiveTab}>
          <Tabs.List>
            <Tabs.Tab value="general">General</Tabs.Tab>
            <Tabs.Tab value="performance">Performance</Tabs.Tab>
            <Tabs.Tab value="notifications">Notifications</Tabs.Tab>
            <Tabs.Tab value="security">Security</Tabs.Tab>
          </Tabs.List>

          {/* General Settings */}
          <Tabs.Panel value="general" pt="lg">
            <form onSubmit={generalForm.onSubmit((values) => handleSave('General', values))}>
              <Stack>
                <Text size="lg" fw={600}>General Configuration</Text>
                
                <TextInput
                  label="Rclone Binary Path"
                  description="Path to the rclone executable"
                  {...generalForm.getInputProps('rclone_binary_path')}
                  key={generalForm.key('rclone_binary_path')}
                />

                <Select
                  label="Log Level"
                  description="Logging verbosity level"
                  data={[
                    { value: 'debug', label: 'Debug' },
                    { value: 'info', label: 'Info' },
                    { value: 'warning', label: 'Warning' },
                    { value: 'error', label: 'Error' },
                  ]}
                  {...generalForm.getInputProps('log_level')}
                  key={generalForm.key('log_level')}
                />

                <Group grow>
                  <NumberInput
                    label="Max Log Size (MB)"
                    description="Maximum size for log files before rotation"
                    min={10}
                    max={1000}
                    {...generalForm.getInputProps('max_log_size_mb')}
                    key={generalForm.key('max_log_size_mb')}
                  />

                  <NumberInput
                    label="Log Retention (Days)"
                    description="Number of days to keep log files"
                    min={1}
                    max={365}
                    {...generalForm.getInputProps('log_retention_days')}
                    key={generalForm.key('log_retention_days')}
                  />
                </Group>

                <TextInput
                  label="Temporary Directory"
                  description="Directory for temporary files during transfers"
                  {...generalForm.getInputProps('temp_directory')}
                  key={generalForm.key('temp_directory')}
                />

                <Switch
                  label="Enable Atomic Delivery"
                  description="Use temporary files and rename on completion"
                  {...generalForm.getInputProps('enable_atomic_delivery', { type: 'checkbox' })}
                  key={generalForm.key('enable_atomic_delivery')}
                />

                <Divider />

                <Group justify="flex-end">
                  <Button
                    variant="light"
                    leftSection={<IconRefresh size={16} />}
                    onClick={() => handleReset('General', generalForm)}
                    disabled={loading}
                  >
                    Reset
                  </Button>
                  <Button
                    type="submit"
                    leftSection={<IconDeviceFloppy size={16} />}
                    loading={loading}
                  >
                    Save Changes
                  </Button>
                </Group>
              </Stack>
            </form>
          </Tabs.Panel>

          {/* Performance Settings */}
          <Tabs.Panel value="performance" pt="lg">
            <form onSubmit={performanceForm.onSubmit((values) => handleSave('Performance', values))}>
              <Stack>
                <Text size="lg" fw={600}>Performance Configuration</Text>
                
                <NumberInput
                  label="Default Concurrent Transfers"
                  description="Default number of simultaneous transfers per endpoint"
                  min={1}
                  max={20}
                  {...performanceForm.getInputProps('default_max_concurrent')}
                  key={performanceForm.key('default_max_concurrent')}
                />

                <TextInput
                  label="Default Bandwidth Limit"
                  description="Default bandwidth limit (e.g., 100M, 1G)"
                  placeholder="100M"
                  {...performanceForm.getInputProps('default_bandwidth_limit')}
                  key={performanceForm.key('default_bandwidth_limit')}
                />

                <NumberInput
                  label="Buffer Size (MB)"
                  description="Transfer buffer size in megabytes"
                  min={1}
                  max={256}
                  {...performanceForm.getInputProps('buffer_size_mb')}
                  key={performanceForm.key('buffer_size_mb')}
                />

                <NumberInput
                  label="Check Interval (Seconds)"
                  description="How often to check for new transfers"
                  min={1}
                  max={60}
                  {...performanceForm.getInputProps('check_interval')}
                  key={performanceForm.key('check_interval')}
                />

                <Divider label="Monitoring" />

                <Switch
                  label="Enable Prometheus Metrics"
                  description="Export metrics for Prometheus monitoring"
                  {...performanceForm.getInputProps('enable_prometheus_metrics', { type: 'checkbox' })}
                  key={performanceForm.key('enable_prometheus_metrics')}
                />

                {performanceForm.getValues().enable_prometheus_metrics && (
                  <NumberInput
                    label="Metrics Port"
                    description="Port for Prometheus metrics endpoint"
                    min={1024}
                    max={65535}
                    {...performanceForm.getInputProps('metrics_port')}
                    key={performanceForm.key('metrics_port')}
                  />
                )}

                <Divider />

                <Group justify="flex-end">
                  <Button
                    variant="light"
                    leftSection={<IconRefresh size={16} />}
                    onClick={() => handleReset('Performance', performanceForm)}
                    disabled={loading}
                  >
                    Reset
                  </Button>
                  <Button
                    type="submit"
                    leftSection={<IconDeviceFloppy size={16} />}
                    loading={loading}
                  >
                    Save Changes
                  </Button>
                </Group>
              </Stack>
            </form>
          </Tabs.Panel>

          {/* Notification Settings */}
          <Tabs.Panel value="notifications" pt="lg">
            <form onSubmit={notificationForm.onSubmit((values) => handleSave('Notification', values))}>
              <Stack>
                <Text size="lg" fw={600}>Notification Configuration</Text>
                
                <Switch
                  label="Enable Email Notifications"
                  {...notificationForm.getInputProps('enable_notifications', { type: 'checkbox' })}
                  key={notificationForm.key('enable_notifications')}
                />

                {notificationForm.getValues().enable_notifications && (
                  <>
                    <Group grow>
                      <TextInput
                        label="SMTP Host"
                        placeholder="smtp.example.com"
                        {...notificationForm.getInputProps('smtp_host')}
                        key={notificationForm.key('smtp_host')}
                      />
                      <NumberInput
                        label="SMTP Port"
                        min={1}
                        max={65535}
                        {...notificationForm.getInputProps('smtp_port')}
                        key={notificationForm.key('smtp_port')}
                      />
                    </Group>

                    <TextInput
                      label="SMTP Username"
                      {...notificationForm.getInputProps('smtp_user')}
                      key={notificationForm.key('smtp_user')}
                    />

                    <PasswordInput
                      label="SMTP Password"
                      {...notificationForm.getInputProps('smtp_password')}
                      key={notificationForm.key('smtp_password')}
                    />

                    <TextInput
                      label="From Address"
                      type="email"
                      {...notificationForm.getInputProps('smtp_from')}
                      key={notificationForm.key('smtp_from')}
                    />
                  </>
                )}

                <Divider />

                <Switch
                  label="Enable Webhook Notifications"
                  {...notificationForm.getInputProps('enable_webhook_notifications', { type: 'checkbox' })}
                  key={notificationForm.key('enable_webhook_notifications')}
                />

                {notificationForm.getValues().enable_webhook_notifications && (
                  <TextInput
                    label="Webhook URL"
                    placeholder="https://example.com/webhook"
                    {...notificationForm.getInputProps('webhook_url')}
                    key={notificationForm.key('webhook_url')}
                  />
                )}

                <Divider />

                <Group justify="flex-end">
                  <Button
                    variant="light"
                    leftSection={<IconRefresh size={16} />}
                    onClick={() => handleReset('Notification', notificationForm)}
                    disabled={loading}
                  >
                    Reset
                  </Button>
                  <Button
                    type="submit"
                    leftSection={<IconDeviceFloppy size={16} />}
                    loading={loading}
                  >
                    Save Changes
                  </Button>
                </Group>
              </Stack>
            </form>
          </Tabs.Panel>

          {/* Security Settings */}
          <Tabs.Panel value="security" pt="lg">
            <form onSubmit={securityForm.onSubmit((values) => handleSave('Security', values))}>
              <Stack>
                <Text size="lg" fw={600}>Security Configuration</Text>
                
                <Switch
                  label="Enable LDAP Authentication"
                  description="Use LDAP/Active Directory for user authentication"
                  {...securityForm.getInputProps('enable_ldap', { type: 'checkbox' })}
                  key={securityForm.key('enable_ldap')}
                />

                {securityForm.getValues().enable_ldap && (
                  <>
                    <TextInput
                      label="LDAP Server"
                      placeholder="ldap://ldap.example.com"
                      {...securityForm.getInputProps('ldap_server')}
                      key={securityForm.key('ldap_server')}
                    />

                    <TextInput
                      label="Base DN"
                      placeholder="dc=example,dc=com"
                      {...securityForm.getInputProps('ldap_base_dn')}
                      key={securityForm.key('ldap_base_dn')}
                    />

                    <TextInput
                      label="Bind DN"
                      placeholder="cn=admin,dc=example,dc=com"
                      {...securityForm.getInputProps('ldap_bind_dn')}
                      key={securityForm.key('ldap_bind_dn')}
                    />

                    <PasswordInput
                      label="Bind Password"
                      {...securityForm.getInputProps('ldap_bind_password')}
                      key={securityForm.key('ldap_bind_password')}
                    />
                  </>
                )}

                <Divider />

                <NumberInput
                  label="API Key Expiry (Days)"
                  description="Number of days before API keys expire"
                  min={1}
                  max={365}
                  {...securityForm.getInputProps('api_key_expiry_days')}
                  key={securityForm.key('api_key_expiry_days')}
                />

                <Switch
                  label="Enable Audit Logging"
                  description="Log all user actions and API calls"
                  {...securityForm.getInputProps('enable_audit_logging', { type: 'checkbox' })}
                  key={securityForm.key('enable_audit_logging')}
                />

                <Select
                  label="Compliance Mode"
                  description="Security compliance level"
                  data={[
                    { value: 'standard', label: 'Standard' },
                    { value: 'hipaa', label: 'HIPAA' },
                    { value: 'pci', label: 'PCI-DSS' },
                    { value: 'sox', label: 'SOX' },
                  ]}
                  {...securityForm.getInputProps('compliance_mode')}
                  key={securityForm.key('compliance_mode')}
                />

                <Divider />

                <Group justify="flex-end">
                  <Button
                    variant="light"
                    leftSection={<IconRefresh size={16} />}
                    onClick={() => handleReset('Security', securityForm)}
                    disabled={loading}
                  >
                    Reset
                  </Button>
                  <Button
                    type="submit"
                    leftSection={<IconDeviceFloppy size={16} />}
                    loading={loading}
                  >
                    Save Changes
                  </Button>
                </Group>
              </Stack>
            </form>
          </Tabs.Panel>
        </Tabs>
      </Paper>
    </Container>
  );
}