import {
  Box,
  VStack,
  Heading,
  FormControl,
  FormLabel,
  Input,
  Button,
  useToast,
  Switch,
  Select,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Divider,
  Text,
} from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import axios from 'axios';

interface Settings {
  youtubeClientSecretsFile: string;
  subtitleFontSize: number;
  subtitleFontColor: string;
  subtitleBackground: boolean;
  subtitlePosition: 'top' | 'bottom';
  checkSubtitleFrames: number;
}

const SettingsPanel = () => {
  const [settings, setSettings] = useState<Settings>({
    youtubeClientSecretsFile: '',
    subtitleFontSize: 24,
    subtitleFontColor: 'white',
    subtitleBackground: true,
    subtitlePosition: 'bottom',
    checkSubtitleFrames: 10,
  });
  const [clientSecretsFile, setClientSecretsFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    // Load current settings
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/settings');
      setSettings(response.data);
    } catch (error) {
      toast({
        title: 'Error loading settings',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleClientSecretsUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setClientSecretsFile(file);
    }
  };

  const handleSaveSettings = async () => {
    setIsLoading(true);
    try {
      const formData = new FormData();
      if (clientSecretsFile) {
        formData.append('client_secrets', clientSecretsFile);
      }
      
      // Append other settings
      Object.entries(settings).forEach(([key, value]) => {
        if (key !== 'youtubeClientSecretsFile') {
          formData.append(key, value.toString());
        }
      });

      await axios.post('http://localhost:8000/api/settings', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast({
        title: 'Settings saved',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error saving settings',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box p={6} bg="white" borderRadius="lg" shadow="md">
      <VStack spacing={6} align="stretch">
        <Heading size="md">YouTube API Configuration</Heading>
        
        <FormControl>
          <FormLabel>YouTube API Client Secrets File</FormLabel>
          <Input
            type="file"
            accept=".json"
            onChange={handleClientSecretsUpload}
          />
          <Text fontSize="sm" color="gray.600" mt={1}>
            Upload your client_secrets.json file from Google Cloud Console
          </Text>
        </FormControl>

        <Divider />

        <Heading size="md">Subtitle Settings</Heading>

        <FormControl>
          <FormLabel>Font Size</FormLabel>
          <NumberInput
            value={settings.subtitleFontSize}
            onChange={(_, value) => setSettings({ ...settings, subtitleFontSize: value })}
            min={12}
            max={48}
          >
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>

        <FormControl>
          <FormLabel>Font Color</FormLabel>
          <Select
            value={settings.subtitleFontColor}
            onChange={(e) => setSettings({ ...settings, subtitleFontColor: e.target.value })}
          >
            <option value="white">White</option>
            <option value="yellow">Yellow</option>
            <option value="black">Black</option>
          </Select>
        </FormControl>

        <FormControl display="flex" alignItems="center">
          <FormLabel mb={0}>Show Subtitle Background</FormLabel>
          <Switch
            isChecked={settings.subtitleBackground}
            onChange={(e) => setSettings({ ...settings, subtitleBackground: e.target.checked })}
          />
        </FormControl>

        <FormControl>
          <FormLabel>Subtitle Position</FormLabel>
          <Select
            value={settings.subtitlePosition}
            onChange={(e) => setSettings({ ...settings, subtitlePosition: e.target.value as 'top' | 'bottom' })}
          >
            <option value="top">Top</option>
            <option value="bottom">Bottom</option>
          </Select>
        </FormControl>

        <FormControl>
          <FormLabel>Number of Frames to Check for Subtitles</FormLabel>
          <NumberInput
            value={settings.checkSubtitleFrames}
            onChange={(_, value) => setSettings({ ...settings, checkSubtitleFrames: value })}
            min={5}
            max={30}
          >
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
          <Text fontSize="sm" color="gray.600" mt={1}>
            Increase this number for more accurate subtitle detection
          </Text>
        </FormControl>

        <Button
          colorScheme="blue"
          onClick={handleSaveSettings}
          isLoading={isLoading}
          mt={4}
        >
          Save Settings
        </Button>
      </VStack>
    </Box>
  );
};

export default SettingsPanel;