import { useState, useEffect } from 'react';
import { Box, VStack, Heading, useToast } from '@chakra-ui/react';
import VideoCard from '../components/VideoCard';
import VideoUploader from '../components/VideoUploader';
import axios from 'axios';

interface Video {
  id: string;
  url: string;
  title: string;
  processed: boolean;
}

const VideoSwiperContainer = () => {
  const [videos, setVideos] = useState<Video[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const toast = useToast();

  const handleSwipeLeft = async () => {
    if (currentIndex < videos.length) {
      // Discard the video
      try {
        await axios.post(`http://localhost:8000/api/videos/${videos[currentIndex].id}/discard`);
        setCurrentIndex(prev => prev + 1);
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

  const handleSwipeRight = async () => {
    if (currentIndex < videos.length) {
      // Save to collection
      try {
        await axios.post(`http://localhost:8000/api/videos/${videos[currentIndex].id}/save`);
        setCurrentIndex(prev => prev + 1);
        toast({
          title: 'Success',
          description: 'Video saved to collection',
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
    }
  };

  const handleUploadComplete = (videoUrl: string) => {
    // Add the new video to the queue
    setVideos(prev => [...prev, {
      id: Date.now().toString(), // Temporary ID until backend processes
      url: videoUrl,
      title: 'Processing...', // Will be updated after processing
      processed: false
    }]);
  };

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
                processed: true
              };
            }
          });
          return updatedVideos;
        });
      } catch (error) {
        console.error('Error polling for processed videos:', error);
      }
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(pollInterval);
  }, []);

  return (
    <VStack spacing={8} p={8} h="100vh">
      <Heading>TikTok to YouTube Shorts</Heading>
      
      {videos.length === 0 ? (
        <VideoUploader onUploadComplete={handleUploadComplete} />
      ) : currentIndex >= videos.length ? (
        <Box textAlign="center">
          <Heading size="md">No more videos to review</Heading>
          <VideoUploader onUploadComplete={handleUploadComplete} />
        </Box>
      ) : (
        <Box h="70vh" w="full" maxW="md">
          <VideoCard
            videoUrl={videos[currentIndex].url}
            title={videos[currentIndex].title}
            onSwipeLeft={handleSwipeLeft}
            onSwipeRight={handleSwipeRight}
          />
        </Box>
      )}
    </VStack>
  );
};

export default VideoSwiperContainer;