import { Container, Title, Text, SimpleGrid, Card, Group, Stack } from '@mantine/core';
import { useEffect, useState } from 'react';
import api from '../services/api';

interface Stats {
  total_jobs: number;
  active_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  total_endpoints: number;
  total_transfers: number;
}

const Dashboard = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/stats/');
        setStats(response.data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const statCards = [
    { label: 'Total Jobs', value: stats?.total_jobs || 0, color: 'blue' },
    { label: 'Active Jobs', value: stats?.active_jobs || 0, color: 'green' },
    { label: 'Completed Jobs', value: stats?.completed_jobs || 0, color: 'teal' },
    { label: 'Failed Jobs', value: stats?.failed_jobs || 0, color: 'red' },
    { label: 'Total Endpoints', value: stats?.total_endpoints || 0, color: 'violet' },
    { label: 'Total Transfers', value: stats?.total_transfers || 0, color: 'orange' },
  ];

  return (
    <Container size="xl">
      <Stack>
        <div>
          <Title order={2}>Dashboard</Title>
          <Text c="dimmed" size="sm">System overview and statistics</Text>
        </div>

        <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
          {statCards.map((stat) => (
            <Card key={stat.label} shadow="sm" padding="lg" radius="md" withBorder>
              <Text size="sm" c="dimmed" fw={500}>{stat.label}</Text>
              <Text size="xl" fw={700} c={stat.color}>{stat.value}</Text>
            </Card>
          ))}
        </SimpleGrid>
      </Stack>
    </Container>
  );
};

export default Dashboard;