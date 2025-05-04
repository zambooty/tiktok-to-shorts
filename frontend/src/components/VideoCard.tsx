import { Box, Heading, Text, VStack } from '@chakra-ui/react';
import { motion, useAnimation } from 'framer-motion';
import { useState } from 'react';

interface VideoCardProps {
  videoUrl: string;
  title: string;
  onSwipeLeft: () => void;
  onSwipeRight: () => void;
}

const VideoCard = ({ videoUrl, title, onSwipeLeft, onSwipeRight }: VideoCardProps) => {
  const controls = useAnimation();
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const handleDragEnd = async (event: any, info: any) => {
    const offset = info.offset.x;
    const velocity = info.velocity.x;

    if (offset > 100 || velocity > 500) {
      await controls.start({ x: '100%', opacity: 0 });
      onSwipeRight();
    } else if (offset < -100 || velocity < -500) {
      await controls.start({ x: '-100%', opacity: 0 });
      onSwipeLeft();
    } else {
      controls.start({ x: 0, opacity: 1 });
    }
  };

  return (
    <motion.div
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      onDragStart={(e, info) => setDragStart({ x: info.point.x, y: info.point.y })}
      onDragEnd={handleDragEnd}
      animate={controls}
      style={{ width: '100%', height: '100%' }}
    >
      <Box
        bg="white"
        rounded="lg"
        shadow="xl"
        overflow="hidden"
        position="relative"
        h="full"
      >
        <video
          src={videoUrl}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          controls
          playsInline
        />
        <VStack
          position="absolute"
          bottom={0}
          w="full"
          p={4}
          bg="rgba(0,0,0,0.7)"
          color="white"
          align="start"
        >
          <Heading size="md">{title}</Heading>
          <Text fontSize="sm">Swipe right to save, left to discard</Text>
        </VStack>
      </Box>
    </motion.div>
  );
};

export default VideoCard;