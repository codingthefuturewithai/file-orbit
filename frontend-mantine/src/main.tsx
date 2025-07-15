import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { MantineProvider } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import { ModalsProvider } from '@mantine/modals'
import { BrowserRouter } from 'react-router-dom'
import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'
import '@mantine/dates/styles.css'
import '@mantine/dropzone/styles.css'
import App from './App'
import ErrorBoundary from './components/common/ErrorBoundary'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <MantineProvider defaultColorScheme="light">
        <Notifications />
        <ModalsProvider>
          <ErrorBoundary>
            <App />
          </ErrorBoundary>
        </ModalsProvider>
      </MantineProvider>
    </BrowserRouter>
  </StrictMode>,
)