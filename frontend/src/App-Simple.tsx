import { Routes, Route } from 'react-router-dom';
import { AppShell, Title, Group, Burger, ScrollArea, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import Navigation from './components/Layout/Navigation';
import Dashboard from './pages/Dashboard';

function AppSimple() {
  const [opened, { toggle }] = useDisclosure();

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 250,
        breakpoint: 'sm',
        collapsed: { mobile: !opened }
      }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger
            opened={opened}
            onClick={toggle}
            hiddenFrom="sm"
            size="sm"
          />
          <Title order={3}>FileOrbit</Title>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <ScrollArea>
          <Navigation />
        </ScrollArea>
      </AppShell.Navbar>

      <AppShell.Main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/endpoints" element={<Text>Endpoints Page (TODO)</Text>} />
          <Route path="/transfers" element={<Text>Transfers Page (TODO)</Text>} />
          <Route path="/history" element={<Text>History Page (TODO)</Text>} />
          <Route path="/templates" element={<Text>Templates Page (TODO)</Text>} />
          <Route path="/logs" element={<Text>Logs Page (TODO)</Text>} />
          <Route path="/settings" element={<Text>Settings Page (TODO)</Text>} />
        </Routes>
      </AppShell.Main>
    </AppShell>
  );
}

export default AppSimple;