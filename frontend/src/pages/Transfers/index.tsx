import { Container, Title, Button, Group, Paper } from '@mantine/core';
import { IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import TransferList from './TransferList';
import CreateTransferForm from '../../components/CreateTransferForm';

export default function Transfers() {
  const [showCreateForm, setShowCreateForm] = useState(false);

  return (
    <Container size="xl">
      <Group justify="space-between" mb="xl">
        <Title order={2}>Active Transfers</Title>
        <Button 
          leftSection={<IconPlus size={16} />}
          onClick={() => setShowCreateForm(true)}
        >
          Create Transfer
        </Button>
      </Group>

      <Paper shadow="sm" p="md" withBorder>
        <TransferList />
      </Paper>

      <CreateTransferForm 
        opened={showCreateForm}
        onClose={() => setShowCreateForm(false)}
      />
    </Container>
  );
}