import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  Input,
  Text,
  useToast,
  Box,
} from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import axios from 'axios';

interface Niche {
  id: number;
  name: string;
  description?: string;
}

interface NicheSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (nicheId: number) => void;
  videoId: number;
}

const NicheSelector = ({ isOpen, onClose, onSelect, videoId }: NicheSelectorProps) => {
  const [niches, setNiches] = useState<Niche[]>([]);
  const [newNicheName, setNewNicheName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    fetchNiches();
  }, []);

  const fetchNiches = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/niches');
      setNiches(response.data);
    } catch (error) {
      toast({
        title: 'Error fetching niches',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const createNiche = async () => {
    if (!newNicheName.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/api/niches', {
        name: newNicheName.trim(),
      });
      
      setNiches([...niches, response.data]);
      setNewNicheName('');
      
      toast({
        title: 'Niche created',
        status: 'success',
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: 'Error creating niche',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleNicheSelect = async (nicheId: number) => {
    try {
      await axios.post(`http://localhost:8000/api/videos/${videoId}/save`, {
        niche_id: nicheId,
      });
      onSelect(nicheId);
      onClose();
    } catch (error) {
      toast({
        title: 'Error saving video to niche',
        status: 'error',
        duration: 3000,
      });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Select or Create Niche</ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          <VStack spacing={4} align="stretch">
            <Box>
              <Text mb={2}>Create New Niche:</Text>
              <Input
                value={newNicheName}
                onChange={(e) => setNewNicheName(e.target.value)}
                placeholder="Enter niche name"
                mb={2}
              />
              <Button
                colorScheme="blue"
                onClick={createNiche}
                isLoading={isLoading}
                width="full"
              >
                Create Niche
              </Button>
            </Box>

            <Text mt={4} mb={2}>Existing Niches:</Text>
            <VStack spacing={2} align="stretch">
              {niches.map((niche) => (
                <Button
                  key={niche.id}
                  onClick={() => handleNicheSelect(niche.id)}
                  variant="outline"
                >
                  {niche.name}
                </Button>
              ))}
            </VStack>
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default NicheSelector;