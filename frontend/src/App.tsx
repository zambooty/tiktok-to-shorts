import { ChakraProvider, Box, Flex } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import VideoSwiperContainer from './containers/VideoSwiperContainer';
import SettingsPanel from './components/SettingsPanel';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <ChakraProvider>
      <Router>
        <Flex minH="100vh">
          <Navigation />
          <Box flex="1" p={4}>
            <Routes>
              <Route path="/" element={<VideoSwiperContainer />} />
              <Route path="/settings" element={<SettingsPanel />} />
              <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
          </Box>
        </Flex>
      </Router>
    </ChakraProvider>
  );
}

export default App;