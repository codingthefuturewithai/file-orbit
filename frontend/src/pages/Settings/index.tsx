import { useState } from 'react';
import { Container, Title, Paper, Tabs, TextInput, NumberInput, Select, Switch, Button, Group, Stack, Text, Divider, PasswordInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconDeviceFloppy, IconRefresh } from '@tabler/icons-react';

interface GeneralSettings {
  rclone_binary_path: string;
  log_level: string;
  max_log_size_mb: number;
  log_retention_days: number;
  temp_directory: string;
  enable_atomic_delivery: boolean;
}

interface PerformanceSettings {
  default_concurrent_transfers: number;
  default_bandwidth_limit: string;
  buffer_size_mb: number;
  check_interval_seconds: number;
  enable_prometheus_metrics: boolean;
  metrics_port: number;
}

interface NotificationSettings {
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  smtp_from: string;
  enable_email_notifications: boolean;
  webhook_url: string;
  enable_webhook_notifications: boolean;
  notification_events: string[];
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
  const [loading, setLoading] = useState(false);

  // General Settings Form
  const generalForm = useForm<GeneralSettings>({
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
    initialValues: {
      default_concurrent_transfers: 5,
      default_bandwidth_limit: '100M',
      buffer_size_mb: 16,
      check_interval_seconds: 5,
      enable_prometheus_metrics: true,
      metrics_port: 9090,
    },
  });

  // Notification Settings Form
  const notificationForm = useForm<NotificationSettings>({
    initialValues: {
      smtp_host: 'smtp.ctf.org',
      smtp_port: 587,
      smtp_username: '',
      smtp_password: '',
      smtp_from: 'file-orbit@ctf.org',
      enable_email_notifications: true,
      webhook_url: '',
      enable_webhook_notifications: false,
      notification_events: ['transfer_failed', 'transfer_completed'],
    },
  });

  // Security Settings Form
  const securityForm = useForm<SecuritySettings>({
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

  const handleSave = async (section: string) => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      notifications.show({
        title: 'Success',
        message: `${section} settings saved successfully`,
        color: 'green',
      });
      setLoading(false);
    }, 1000);
  };

  const handleReset = (form: any, section: string) => {
    form.reset();
    notifications.show({
      title: 'Reset',
      message: `${section} settings reset to defaults`,
      color: 'blue',
    });
  };

  return (
    <Container size="xl">
      <Title order={2} mb="xl">Settings</Title>

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
            <form onSubmit={generalForm.onSubmit(() => handleSave('General'))}>
              <Stack>
                <Text size="lg" fw={600}>General Configuration</Text>
                
                <TextInput
                  label="Rclone Binary Path"
                  description="Path to the rclone executable"
                  {...generalForm.getInputProps('rclone_binary_path')}
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
                />

                <Group grow>
                  <NumberInput
                    label="Max Log Size (MB)"
                    description="Maximum size for log files before rotation"
                    min={10}
                    max={1000}
                    {...generalForm.getInputProps('max_log_size_mb')}
                  />

                  <NumberInput
                    label="Log Retention (Days)"
                    description="Number of days to keep log files"
                    min={1}
                    max={365}
                    {...generalForm.getInputProps('log_retention_days')}
                  />
                </Group>

                <TextInput
                  label="Temporary Directory"
                  description="Directory for temporary files during transfers"
                  {...generalForm.getInputProps('temp_directory')}
                />

                <Switch
                  label="Enable Atomic Delivery"
                  description="Use temporary files and rename on completion"
                  {...generalForm.getInputProps('enable_atomic_delivery', { type: 'checkbox' })}
                />

                <Divider />

                <Group justify="flex-end">
                  <Button
                    variant="light"
                    leftSection={<IconRefresh size={16} />}
                    onClick={() => handleReset(generalForm, 'General')}
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
            <form onSubmit={performanceForm.onSubmit(() => handleSave('Performance'))}>
              <Stack>
                <Text size="lg" fw={600}>Performance Configuration</Text>
                
                <NumberInput
                  label="Default Concurrent Transfers"
                  description="Default number of simultaneous transfers per endpoint"
                  min={1}
                  max={20}
                  {...performanceForm.getInputProps('default_concurrent_transfers')}
                />

                <TextInput
                  label="Default Bandwidth Limit"
                  description="Default bandwidth limit (e.g., 100M, 1G)"
                  placeholder="100M"
                  {...performanceForm.getInputProps('default_bandwidth_limit')}
                />

                <NumberInput
                  label="Buffer Size (MB)"
                  description="Transfer buffer size in megabytes"
                  min={1}
                  max={256}
                  {...performanceForm.getInputProps('buffer_size_mb')}
                />

                <NumberInput
                  label="Check Interval (Seconds)"
                  description="How often to check for new transfers"
                  min={1}
                  max={60}
                  {...performanceForm.getInputProps('check_interval_seconds')}
                />

                <Divider label="Monitoring" />

                <Switch
                  label="Enable Prometheus Metrics"
                  description="Export metrics for Prometheus monitoring"
                  {...performanceForm.getInputProps('enable_prometheus_metrics', { type: 'checkbox' })}
                />

                {performanceForm.values.enable_prometheus_metrics && (
                  <NumberInput
                    label="Metrics Port"
                    description="Port for Prometheus metrics endpoint"
                    min={1024}
                    max={65535}
                    {...performanceForm.getInputProps('metrics_port')}
                  />
                )}

                <Divider />

                <Group justify="flex-end">
                  <Button
                    variant="light"
                    leftSection={<IconRefresh size={16} />}
                    onClick={() => handleReset(performanceForm, 'Performance')}
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
            <form onSubmit={notificationForm.onSubmit(() => handleSave('Notification'))}>
              <Stack>
                <Text size="lg" fw={600}>Notification Configuration</Text>
                
                <Switch
                  label="Enable Email Notifications"
                  {...notificationForm.getInputProps('enable_email_notifications', { type: 'checkbox' })}
                />

                {notificationForm.values.enable_email_notifications && (
                  <>
                    <Group grow>
                      <TextInput
                        label="SMTP Host"
                        placeholder="smtp.example.com"
                        {...notificationForm.getInputProps('smtp_host')}
                      />
                      <NumberInput
                        label="SMTP Port"
                        min={1}
                        max={65535}
                        {...notificationForm.getInputProps('smtp_port')}
                      />
                    </Group>

                    <TextInput
                      label="SMTP Username"
                      {...notificationForm.getInputProps('smtp_username')}
                    />

                    <PasswordInput
                      label="SMTP Password"
                      {...notificationForm.getInputProps('smtp_password')}
                    />

                    <TextInput
                      label="From Address"
                      type="email"
                      {...notificationForm.getInputProps('smtp_from')}
                    />
                  </>
                )}

                <Divider />

                <Switch
                  label="Enable Webhook Notifications"
                  {...notificationForm.getInputProps('enable_webhook_notifications', { type: 'checkbox' })}
                />

                {notificationForm.values.enable_webhook_notifications && (
                  <TextInput
                    label="Webhook URL"
                    placeholder="https://example.com/webhook"
                    {...notificationForm.getInputProps('webhook_url')}
                  />
                )}

                <Divider />

                <Group justify="flex-end">
                  <Button
                    variant="light"
                    leftSection={<IconRefresh size={16} />}
                    onClick={() => handleReset(notificationForm, 'Notification')}
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
            <form onSubmit={securityForm.onSubmit(() => handleSave('Security'))}>
              <Stack>
                <Text size="lg" fw={600}>Security Configuration</Text>
                
                <Switch
                  label="Enable LDAP Authentication"
                  description="Use LDAP/Active Directory for user authentication"
                  {...securityForm.getInputProps('enable_ldap', { type: 'checkbox' })}
                />

                {securityForm.values.enable_ldap && (
                  <>
                    <TextInput
                      label="LDAP Server"
                      placeholder="ldap://ldap.example.com"
                      {...securityForm.getInputProps('ldap_server')}
                    />

                    <TextInput
                      label="Base DN"
                      placeholder="dc=example,dc=com"
                      {...securityForm.getInputProps('ldap_base_dn')}
                    />

                    <TextInput
                      label="Bind DN"
                      placeholder="cn=admin,dc=example,dc=com"
                      {...securityForm.getInputProps('ldap_bind_dn')}
                    />

                    <PasswordInput
                      label="Bind Password"
                      {...securityForm.getInputProps('ldap_bind_password')}
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
                />

                <Switch
                  label="Enable Audit Logging"
                  description="Log all user actions and API calls"
                  {...securityForm.getInputProps('enable_audit_logging', { type: 'checkbox' })}
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
                />

                <Divider />

                <Group justify="flex-end">
                  <Button
                    variant="light"
                    leftSection={<IconRefresh size={16} />}
                    onClick={() => handleReset(securityForm, 'Security')}
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