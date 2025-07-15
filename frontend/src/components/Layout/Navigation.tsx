import { NavLink } from '@mantine/core';
import { 
  IconDashboard, 
  IconServer, 
  IconTransfer, 
  IconHistory, 
  IconTemplate, 
  IconFileText, 
  IconSettings 
} from '@tabler/icons-react';
import { useNavigate, useLocation } from 'react-router-dom';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { label: 'Dashboard', icon: IconDashboard, path: '/' },
    { label: 'Endpoints', icon: IconServer, path: '/endpoints' },
    { label: 'Transfers', icon: IconTransfer, path: '/transfers' },
    { label: 'Transfer History', icon: IconHistory, path: '/history' },
    { label: 'Templates', icon: IconTemplate, path: '/templates' },
    { label: 'Logs', icon: IconFileText, path: '/logs' },
    { label: 'Settings', icon: IconSettings, path: '/settings' },
  ];

  return (
    <>
      {navItems.map((item) => (
        <NavLink
          key={item.path}
          active={location.pathname === item.path}
          label={item.label}
          leftSection={<item.icon size={16} />}
          onClick={() => navigate(item.path)}
          variant="subtle"
        />
      ))}
    </>
  );
};

export default Navigation;