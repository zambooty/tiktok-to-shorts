import {
  Box,
  Text,
  Progress,
  VStack,
  Badge,
} from '@chakra-ui/react';

interface ProcessingStatusProps {
  status: 'uploaded' | 'processing' | 'processed' | 'uploading' | 'completed' | 'failed';
  youtubeUrl?: string;
}

const ProcessingStatus = ({ status, youtubeUrl }: ProcessingStatusProps) => {
  const getStatusColor = () => {
    switch (status) {
      case 'uploaded':
        return 'yellow';
      case 'processing':
        return 'blue';
      case 'processed':
        return 'green';
      case 'uploading':
        return 'purple';
      case 'completed':
        return 'green';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getStatusMessage = () => {
    switch (status) {
      case 'uploaded':
        return 'Video uploaded, waiting to process...';
      case 'processing':
        return 'Processing video and detecting subtitles...';
      case 'processed':
        return 'Video processed, ready for YouTube';
      case 'uploading':
        return 'Uploading to YouTube Shorts...';
      case 'completed':
        return 'Successfully uploaded to YouTube!';
      case 'failed':
        return 'Processing failed. Please try again.';
      default:
        return 'Unknown status';
    }
  };

  const getProgress = () => {
    switch (status) {
      case 'uploaded':
        return 20;
      case 'processing':
        return 40;
      case 'processed':
        return 60;
      case 'uploading':
        return 80;
      case 'completed':
        return 100;
      case 'failed':
        return 0;
      default:
        return 0;
    }
  };

  return (
    <VStack spacing={3} w="100%" p={4} bg="gray.50" borderRadius="md">
      <Badge colorScheme={getStatusColor()} fontSize="sm">
        {status.toUpperCase()}
      </Badge>
      
      <Text fontSize="sm" color="gray.600">
        {getStatusMessage()}
      </Text>
      
      <Progress
        value={getProgress()}
        size="sm"
        w="100%"
        colorScheme={getStatusColor()}
        hasStripe
        isAnimated={status === 'processing' || status === 'uploading'}
      />
      
      {youtubeUrl && status === 'completed' && (
        <Box mt={2}>
          <Text fontSize="sm" color="blue.600">
            <a href={youtubeUrl} target="_blank" rel="noopener noreferrer">
              View on YouTube
            </a>
          </Text>
        </Box>
      )}
    </VStack>
  );
};

export default ProcessingStatus;