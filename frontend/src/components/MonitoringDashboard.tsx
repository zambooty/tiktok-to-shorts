import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Badge,
  Progress,
  SimpleGrid,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  useColorModeValue,
  Icon,
  Tooltip,
} from '@chakra-ui/react';
import { FaDatabase, FaRedis, FaHdd, FaFolder, FaServer } from 'react-icons/fa';
import axios from 'axios';

interface HealthStatus {
  status: string;
  checks: {
    database: HealthCheck;
    redis: HealthCheck;
    disk_space: HealthCheck;
    directories: HealthCheck;
    system_resources: HealthCheck;
  };
  timestamp: number;
}

interface HealthCheck {
  status: string;
  message: string | {
    cpu_percent?: number;
    memory_percent?: number;
    warnings?: string[];
  };
}

const MonitoringDashboard: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    const fetchHealthStatus = async () => {
      try {
        const response = await axios.get('http://localhost:8000/health');
        setHealthData(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch health status');
        console.error('Health check error:', err);
      }
    };

    // Initial fetch
    fetchHealthStatus();

    // Poll every 30 seconds
    const interval = setInterval(fetchHealthStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'green';
      case 'warning':
        return 'yellow';
      case 'unhealthy':
        return 'red';
      default:
        return 'gray';
    }
  };

  const ServiceCard: React.FC<{
    title: string;
    icon: React.ElementType;
    status: string;
    message: any;
  }> = ({ title, icon, status, message }) => (
    <Card
      bg={bgColor}
      borderWidth="1px"
      borderColor={borderColor}
      borderRadius="lg"
      overflow="hidden"
    >
      <CardHeader>
        <HStack spacing={4}>
          <Icon as={icon} boxSize={6} />
          <Heading size="md">{title}</Heading>
          <Badge
            ml="auto"
            colorScheme={getStatusColor(status)}
            borderRadius="full"
            px={2}
          >
            {status}
          </Badge>
        </HStack>
      </CardHeader>
      <CardBody>
        {typeof message === 'string' ? (
          <Text>{message}</Text>
        ) : (
          <VStack align="stretch" spacing={4}>
            {message.cpu_percent !== undefined && (
              <Box>
                <Text mb={2}>CPU Usage</Text>
                <Tooltip label={`${message.cpu_percent}%`}>
                  <Progress
                    value={message.cpu_percent}
                    colorScheme={message.cpu_percent > 80 ? 'red' : 'green'}
                  />
                </Tooltip>
              </Box>
            )}
            {message.memory_percent !== undefined && (
              <Box>
                <Text mb={2}>Memory Usage</Text>
                <Tooltip label={`${message.memory_percent}%`}>
                  <Progress
                    value={message.memory_percent}
                    colorScheme={message.memory_percent > 80 ? 'red' : 'green'}
                  />
                </Tooltip>
              </Box>
            )}
            {message.warnings?.map((warning: string, index: number) => (
              <Text key={index} color="yellow.500">
                ⚠️ {warning}
              </Text>
            ))}
          </VStack>
        )}
      </CardBody>
    </Card>
  );

  if (error) {
    return (
      <Box p={8}>
        <Text color="red.500">{error}</Text>
      </Box>
    );
  }

  if (!healthData) {
    return (
      <Box p={8}>
        <Text>Loading health status...</Text>
      </Box>
    );
  }

  return (
    <VStack spacing={8} w="full" p={8}>
      <Heading size="lg">System Health Monitor</Heading>

      <Stat
        bg={bgColor}
        borderWidth="1px"
        borderColor={borderColor}
        borderRadius="lg"
        p={4}
      >
        <StatLabel>Overall System Status</StatLabel>
        <StatNumber>
          <Badge
            colorScheme={getStatusColor(healthData.status)}
            fontSize="lg"
            borderRadius="full"
            px={4}
            py={1}
          >
            {healthData.status.toUpperCase()}
          </Badge>
        </StatNumber>
        <StatHelpText>
          Last updated: {new Date(healthData.timestamp * 1000).toLocaleString()}
        </StatHelpText>
      </Stat>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6} w="full">
        <ServiceCard
          title="Database"
          icon={FaDatabase}
          status={healthData.checks.database.status}
          message={healthData.checks.database.message}
        />
        <ServiceCard
          title="Redis"
          icon={FaRedis}
          status={healthData.checks.redis.status}
          message={healthData.checks.redis.message}
        />
        <ServiceCard
          title="Disk Space"
          icon={FaHdd}
          status={healthData.checks.disk_space.status}
          message={healthData.checks.disk_space.message}
        />
        <ServiceCard
          title="Directories"
          icon={FaFolder}
          status={healthData.checks.directories.status}
          message={healthData.checks.directories.message}
        />
        <ServiceCard
          title="System Resources"
          icon={FaServer}
          status={healthData.checks.system_resources.status}
          message={healthData.checks.system_resources.message}
        />
      </SimpleGrid>
    </VStack>
  );
};

export default MonitoringDashboard;