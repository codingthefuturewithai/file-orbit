import { Component, ErrorInfo, ReactNode } from 'react';
import { Container, Title, Text, Button, Stack } from '@mantine/core';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <Container size="sm" mt="xl">
          <Stack align="center" spacing="md">
            <Title order={2}>Something went wrong</Title>
            <Text c="dimmed">
              An unexpected error occurred. Please try refreshing the page.
            </Text>
            {this.state.error && (
              <Text size="sm" c="red" style={{ fontFamily: 'monospace' }}>
                {this.state.error.message}
              </Text>
            )}
            <Button onClick={this.handleReset}>
              Return to Dashboard
            </Button>
          </Stack>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;