import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  VStack,
  HStack,
  Text,
  useColorModeValue,
} from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import axios from 'axios';

interface VideoStats {
  id: number;
  title: string;
  status: string;
  niche: string;
  youtubeUrl: string;
  views?: number;
  likes?: number;
  processedAt: string;
}

interface DashboardStats {
  totalVideos: number;
  processedVideos: number;
  totalNiches: number;
  averageProcessingTime: number;
}

const Dashboard = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalVideos: 0,
    processedVideos: 0,
    totalNiches: 0,
    averageProcessingTime: 0,
  });
  const [recentVideos, setRecentVideos] = useState<VideoStats[]>([]);
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsResponse, videosResponse] = await Promise.all([
        axios.get('http://localhost:8000/api/stats'),
        axios.get('http://localhost:8000/api/videos/recent')
      ]);

      setStats(statsResponse.data);
      setRecentVideos(videosResponse.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'green';
      case 'processing':
        return 'blue';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  return (
    <VStack spacing={8} w="full" align="stretch">
      <Heading size="lg">Dashboard</Heading>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
        <Stat
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth="1px"
          borderColor={borderColor}
        >
          <StatLabel>Total Videos</StatLabel>
          <StatNumber>{stats.totalVideos}</StatNumber>
          <StatHelpText>All time</StatHelpText>
        </Stat>

        <Stat
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth="1px"
          borderColor={borderColor}
        >
          <StatLabel>Processed Videos</StatLabel>
          <StatNumber>{stats.processedVideos}</StatNumber>
          <StatHelpText>Successfully converted</StatHelpText>
        </Stat>

        <Stat
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth="1px"
          borderColor={borderColor}
        >
          <StatLabel>Total Niches</StatLabel>
          <StatNumber>{stats.totalNiches}</StatNumber>
          <StatHelpText>Active categories</StatHelpText>
        </Stat>

        <Stat
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth="1px"
          borderColor={borderColor}
        >
          <StatLabel>Avg. Processing Time</StatLabel>
          <StatNumber>{stats.averageProcessingTime}s</StatNumber>
          <StatHelpText>Per video</StatHelpText>
        </Stat>
      </SimpleGrid>

      <Box
        bg={bgColor}
        borderRadius="lg"
        borderWidth="1px"
        borderColor={borderColor}
        p={6}
      >
        <Heading size="md" mb={4}>Recent Videos</Heading>
        <Box overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Title</Th>
                <Th>Niche</Th>
                <Th>Status</Th>
                <Th>Views</Th>
                <Th>Likes</Th>
                <Th>Processed</Th>
              </Tr>
            </Thead>
            <Tbody>
              {recentVideos.map((video) => (
                <Tr key={video.id}>
                  <Td>
                    {video.youtubeUrl ? (
                      <a href={video.youtubeUrl} target="_blank" rel="noopener noreferrer">
                        {video.title}
                      </a>
                    ) : (
                      video.title
                    )}
                  </Td>
                  <Td>{video.niche}</Td>
                  <Td>
                    <Badge colorScheme={getStatusColor(video.status)}>
                      {video.status}
                    </Badge>
                  </Td>
                  <Td>{video.views || 'N/A'}</Td>
                  <Td>{video.likes || 'N/A'}</Td>
                  <Td>{new Date(video.processedAt).toLocaleDateString()}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      </Box>
    </VStack>
  );
};

export default Dashboard;