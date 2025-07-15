import { useState, useEffect, useRef } from 'react';
import { Container, Title, Paper, Tabs, Select, Button, Group, ScrollArea, Text, Badge, Stack, TextInput } from '@mantine/core';
import { IconRefresh, IconDownload, IconSearch, IconFilter } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { useApi } from '../../hooks/useApi';

interface LogData {
  lines: string[];
  total: number;
  filtered: number;
  returned: number;
}

const levelColors: Record<string, string> = {
  info: 'blue',
  warning: 'yellow',
  error: 'red',
  debug: 'gray',
};

export default function Logs() {
  const [selectedTab, setSelectedTab] = useState<string | null>('backend');
  const [logData, setLogData] = useState<LogData | null>(null);
  const [lineCount, setLineCount] = useState<number>(100);
  const [searchTerm, setSearchTerm] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { callApi, loading } = useApi();

  useEffect(() => {
    if (selectedTab) {
      fetchLogs(selectedTab);
    }
  }, [selectedTab, lineCount, searchTerm]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh && selectedTab) {
      interval = setInterval(() => {
        fetchLogs(selectedTab);
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [autoRefresh, selectedTab]);

  const fetchLogs = async (logType: string) => {
    try {
      const params = new URLSearchParams({
        lines: lineCount.toString()
      });
      
      if (searchTerm) {
        params.append('filter', searchTerm);
      }
      
      const response = await callApi<LogData>(`/logs/${logType}?${params.toString()}`, 'GET');
      if (response) {
        setLogData(response);
        // Auto-scroll to bottom on new logs
        if (scrollAreaRef.current) {
          scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
        }
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      setLogData(null);
    }
  };

  const formatLogLine = (line: string, index: number) => {
    // Determine log level color based on content
    let levelColor = 'dimmed';
    let level = 'info';
    
    if (line.includes('ERROR') || line.includes('CRITICAL')) {
      levelColor = 'red';
      level = 'error';
    } else if (line.includes('WARNING') || line.includes('WARN')) {
      levelColor = 'yellow';
      level = 'warning';
    } else if (line.includes('INFO')) {
      levelColor = 'blue';
      level = 'info';
    } else if (line.includes('DEBUG')) {
      levelColor = 'gray';
      level = 'debug';
    }

    return { line, levelColor, level, index };
  };

  const handleExport = () => {
    if (!logData || !logData.lines.length) return;
    
    const logText = logData.lines.join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedTab}-logs-${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    notifications.show({
      title: 'Success',
      message: 'Logs exported successfully',
      color: 'green',
    });
  };

  return (
    <Container size="xl">
      <Title order={2} mb="xl">System Logs</Title>

      <Paper shadow="sm" p="md" withBorder>
        <Tabs value={selectedTab} onChange={setSelectedTab}>
          <Tabs.List>
            <Tabs.Tab value="backend">Backend</Tabs.Tab>
            <Tabs.Tab value="worker">Worker</Tabs.Tab>
            <Tabs.Tab value="event-monitor">Event Monitor</Tabs.Tab>
            <Tabs.Tab value="scheduler">Scheduler</Tabs.Tab>
          </Tabs.List>

          <Stack mt="md">
            <Group>
              <TextInput
                placeholder="Search logs..."
                leftSection={<IconSearch size={16} />}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.currentTarget.value)}
                style={{ flex: 1 }}
              />
              <Select
                placeholder="Lines to show"
                data={[
                  { value: '50', label: '50 lines' },
                  { value: '100', label: '100 lines' },
                  { value: '500', label: '500 lines' },
                  { value: '1000', label: '1000 lines' },
                ]}
                value={lineCount.toString()}
                onChange={(value) => setLineCount(parseInt(value || '100'))}
                style={{ width: 150 }}
              />
              <Button
                variant={autoRefresh ? 'filled' : 'light'}
                leftSection={<IconRefresh size={16} />}
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
              </Button>
              <Button
                variant="light"
                leftSection={<IconDownload size={16} />}
                onClick={handleExport}
                disabled={!logData || logData.lines.length === 0}
              >
                Export
              </Button>
            </Group>

            {logData && (
              <Group gap="md">
                <Text size="sm" c="dimmed">Total lines: {logData.total}</Text>
                {searchTerm && <Text size="sm" c="dimmed">Filtered: {logData.filtered}</Text>}
                <Text size="sm" c="dimmed">Showing: {logData.returned}</Text>
              </Group>
            )}

            <Paper p="sm" withBorder style={{ backgroundColor: '#1a1b1e' }}>
              <ScrollArea h={500} ref={scrollAreaRef}>
                <Stack gap={0}>
                  {loading ? (
                    <Text c="dimmed" ta="center" p="md">Loading logs...</Text>
                  ) : logData && logData.lines.length > 0 ? (
                    logData.lines.map((line, index) => {
                      const formatted = formatLogLine(line, index);
                      return (
                        <Group key={index} gap="xs" wrap="nowrap" style={{ fontFamily: 'monospace', fontSize: '13px', padding: '2px 0' }}>
                          <Text size="xs" c="dimmed" style={{ minWidth: '40px', textAlign: 'right' }}>
                            {index + 1}
                          </Text>
                          <Text size="xs" c={formatted.levelColor} style={{ flex: 1, whiteSpace: 'pre-wrap' }}>
                            {formatted.line}
                          </Text>
                        </Group>
                      );
                    })
                  ) : (
                    <Text c="dimmed" ta="center" p="md">No logs found</Text>
                  )}
                </Stack>
              </ScrollArea>
            </Paper>
          </Stack>
        </Tabs>
      </Paper>
    </Container>
  );
}