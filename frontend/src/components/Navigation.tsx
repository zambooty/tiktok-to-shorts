import {
  Box,
  VStack,
  IconButton,
  Icon,
  Tooltip,
  useColorModeValue,
} from '@chakra-ui/react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  FiHome,
  FiSettings,
  FiBarChart2,
} from 'react-icons/fi';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const navItems = [
    { icon: FiHome, label: 'Video Processing', path: '/' },
    { icon: FiBarChart2, label: 'Dashboard', path: '/dashboard' },
    { icon: FiSettings, label: 'Settings', path: '/settings' },
  ];

  return (
    <Box
      h="100vh"
      w="16"
      bg={bg}
      borderRight="1px"
      borderColor={borderColor}
      position="sticky"
      top={0}
    >
      <VStack spacing={6} align="center" py={8}>
        {navItems.map(({ icon, label, path }) => (
          <Tooltip
            key={path}
            label={label}
            placement="right"
            hasArrow
          >
            <IconButton
              aria-label={label}
              icon={<Icon as={icon} boxSize={5} />}
              variant={location.pathname === path ? 'solid' : 'ghost'}
              colorScheme={location.pathname === path ? 'blue' : 'gray'}
              size="lg"
              onClick={() => navigate(path)}
              isRound
            />
          </Tooltip>
        ))}
      </VStack>
    </Box>
  );
};

export default Navigation;