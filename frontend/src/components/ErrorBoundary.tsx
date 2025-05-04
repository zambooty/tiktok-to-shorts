import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  Box,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Button,
  Code,
  VStack,
} from '@chakra-ui/react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log error to our backend service
    this.logError(error, errorInfo);
  }

  private logError = async (error: Error, errorInfo: ErrorInfo) => {
    try {
      await fetch('http://localhost:8000/api/errors/log', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error: {
            name: error.name,
            message: error.message,
            stack: error.stack,
          },
          errorInfo: errorInfo.componentStack,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (e) {
      console.error('Failed to log error:', e);
    }
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <Box p={8}>
          <Alert
            status="error"
            variant="subtle"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            textAlign="center"
            borderRadius="lg"
            p={6}
          >
            <AlertIcon boxSize="40px" mr={0} />
            <AlertTitle mt={4} mb={1} fontSize="lg">
              Oops! Something went wrong
            </AlertTitle>
            <AlertDescription maxWidth="xl">
              <VStack spacing={4} mt={4}>
                <Box>
                  {this.state.error && (
                    <Code p={2} borderRadius="md">
                      {this.state.error.message}
                    </Code>
                  )}
                </Box>
                
                <Box>
                  <Button
                    colorScheme="blue"
                    mr={4}
                    onClick={this.handleReset}
                  >
                    Try Again
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={this.handleReload}
                  >
                    Reload Page
                  </Button>
                </Box>
              </VStack>
            </AlertDescription>
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;