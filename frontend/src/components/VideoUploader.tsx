import { useState } from 'react';
import { 
  Box, 
  Button, 
  VStack, 
  useToast, 
  Progress, 
  Text 
} from '@chakra-ui/react';
import axios from 'axios';

interface VideoUploaderProps {
  onUploadComplete: (videoUrl: string) => void;
}

const VideoUploader = ({ onUploadComplete }: VideoUploaderProps) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const toast = useToast();

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type and size
    if (!file.type.includes('video/')) {
      toast({
        title: 'Invalid file type',
        description: 'Please upload a video file',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('http://localhost:8000/api/videos/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 100)
          );
          setProgress(percentCompleted);
        },
      });

      toast({
        title: 'Upload successful',
        description: 'Your video is being processed',
        status: 'success',
        duration: 3000,
      });

      // Pass the video URL back to parent component
      onUploadComplete(response.data.videoUrl);
    } catch (error) {
      toast({
        title: 'Upload failed',
        description: 'There was an error uploading your video',
        status: 'error',
        duration: 3000,
      });
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <Box p={6} borderWidth={2} borderRadius="lg" borderStyle="dashed">
      <VStack spacing={4}>
        <input
          type="file"
          accept="video/*"
          onChange={handleUpload}
          style={{ display: 'none' }}
          id="video-upload"
          disabled={uploading}
        />
        <label htmlFor="video-upload">
          <Button
            as="span"
            colorScheme="blue"
            isLoading={uploading}
            loadingText="Uploading..."
          >
            Select Video
          </Button>
        </label>
        {uploading && (
          <Box w="100%">
            <Text mb={2}>{progress}% uploaded</Text>
            <Progress value={progress} size="sm" colorScheme="blue" />
          </Box>
        )}
      </VStack>
    </Box>
  );
};

export default VideoUploader;