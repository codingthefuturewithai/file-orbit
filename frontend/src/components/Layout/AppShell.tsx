import { AppShell as MantineAppShell, Title, Group, Burger, ScrollArea } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { Outlet } from 'react-router-dom';
import Navigation from './Navigation';

const AppShell = () => {
  const [opened, { toggle }] = useDisclosure();

  return (
    <MantineAppShell
      header={{ height: 60 }}
      navbar={{
        width: 250,
        breakpoint: 'sm',
        collapsed: { mobile: !opened }
      }}
      padding="md"
    >
      <MantineAppShell.Header>
        <Group h="100%" px="md">
          <Burger
            opened={opened}
            onClick={toggle}
            hiddenFrom="sm"
            size="sm"
          />
          <Title order={3}>FileOrbit</Title>
        </Group>
      </MantineAppShell.Header>

      <MantineAppShell.Navbar p="md">
        <ScrollArea>
          <Navigation />
        </ScrollArea>
      </MantineAppShell.Navbar>

      <MantineAppShell.Main>
        <Outlet />
      </MantineAppShell.Main>
    </MantineAppShell>
  );
};

export default AppShell;