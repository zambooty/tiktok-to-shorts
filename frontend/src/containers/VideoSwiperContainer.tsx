import { useState, useEffect } from 'react';
import { Box, VStack, Heading, useToast, Text } from '@chakra-ui/react';
import VideoCard from '../components/VideoCard';
import VideoUploader from '../components/VideoUploader';
import NicheSelector from '../components/NicheSelector';
import ProcessingStatus from '../components/ProcessingStatus';
import axios from 'axios';

interface Video {
  id: number;
  url: string;
  title: string;
  status: 'uploaded' | 'processing' | 'processed' | 'uploading' | 'completed' | 'failed';
  youtubeUrl?: string;
}

const VideoSwiperContainer = () => {
  const [videos, setVideos] = useState<Video[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isNicheSelectorOpen, setIsNicheSelectorOpen] = useState(false);
  const toast = useToast();

  // Poll for processed videos
  useEffect(() => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/videos/processed');
        setVideos(prevVideos => {
          const updatedVideos = [...prevVideos];
          response.data.forEach((processedVideo: any) => {
            const index = updatedVideos.findIndex(v => v.id === processedVideo.id);
            if (index !== -1) {
              updatedVideos[index] = {
                ...updatedVideos[index],
                ...processedVideo,
                status: processedVideo.youtube_url ? 'completed' : 'processed'
              };
            }
          });
          return updatedVideos;
        });
      } catch (error) {
        console.error('Error polling for processed videos:', error);
      }
    }, 5000);

    return () => clearInterval(pollInterval);
  }, []);

  const handleSwipeLeft = async () => {
    if (currentIndex < videos.length) {
      try {
        await axios.post(`http://localhost:8000/api/videos/${videos[currentIndex].id}/discard`);
        setCurrentIndex(prev => prev + 1);
        toast({
          title: 'Video discarded',
          status: 'info',
          duration: 2000,
        });
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Failed to discard video',
          status: 'error',
          duration: 3000,
        });
      }
    }
  };

  const handleSwipeRight = () => {
    if (currentIndex < videos.length) {
      setIsNicheSelectorOpen(true);
    }
  };

  const handleNicheSelect = async (nicheId: number) => {
    try {
      const video = videos[currentIndex];
      await axios.post(`http://localhost:8000/api/videos/${video.id}/save`, {
        niche_id: nicheId
      });
      
      // Update video status
      setVideos(prevVideos => {
        const updatedVideos = [...prevVideos];
        updatedVideos[currentIndex].status = 'uploading';
        return updatedVideos;
      });
      
      setCurrentIndex(prev => prev + 1);
      toast({
        title: 'Video saved',
        description: 'Starting YouTube upload...',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save video',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleUploadComplete = (videoData: Video) => {
    setVideos(prev => [...prev, {
      ...videoData,
      status: 'processing'
    }]);
  };

  return (
    <VStack spacing={8} p={8} h="100vh">
      <Heading>TikTok to YouTube Shorts</Heading>
      
      {videos.length === 0 ? (
        <VideoUploader onUploadComplete={handleUploadComplete} />
      ) : currentIndex >= videos.length ? (
        <Box textAlign="center">
          <Heading size="md" mb={4}>No more videos to review</Heading>
          <VideoUploader onUploadComplete={handleUploadComplete} />
        </Box>
      ) : (
        <VStack spacing={4} w="full" maxW="md">
          <Box h="70vh" w="full" position="relative">
            <VideoCard
              videoUrl={videos[currentIndex].url}
              title={videos[currentIndex].title}
              onSwipeLeft={handleSwipeLeft}
              onSwipeRight={handleSwipeRight}
            />
          </Box>
          
          <ProcessingStatus
            status={videos[currentIndex].status}
            youtubeUrl={videos[currentIndex].youtubeUrl}
          />
          
          <Text fontSize="sm" color="gray.600">
            Swipe right to save, left to discard
          </Text>
        </VStack>
      )}

      <NicheSelector
        isOpen={isNicheSelectorOpen}
        onClose={() => setIsNicheSelectorOpen(false)}
        onSelect={handleNicheSelect}
        videoId={videos[currentIndex]?.id}
      />
    </VStack>
  );
};

export default VideoSwiperContainer;