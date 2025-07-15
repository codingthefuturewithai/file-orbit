# Phase 0: Foundation Setup Checklist

## Quick Start Commands
```bash
cd /Users/timkitchens/projects/consumer-apps/file-orbit
npm create vite@latest frontend-mantine -- --template react-ts
cd frontend-mantine
npm install @mantine/core @mantine/hooks @mantine/form @mantine/dates @mantine/notifications @mantine/modals @mantine/dropzone @tabler/icons-react dayjs react-router-dom axios
```

## File Copy Commands
```bash
# From frontend-mantine directory
mkdir -p ./src/services
cp ../frontend/src/services/api.ts ./src/services/
cp -r ../frontend/src/types ./src/ 2>/dev/null || echo "No types directory found"
cp ../frontend/.env.example .env.example
cp ../frontend/.env .env 2>/dev/null || cp ../frontend/.env.example .env
```

## Required File Creation

### 1. src/main.tsx
```typescript
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

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <MantineProvider defaultColorScheme="light">
        <Notifications />
        <ModalsProvider>
          <App />
        </ModalsProvider>
      </MantineProvider>
    </BrowserRouter>
  </StrictMode>,
)
```

### 2. src/App.tsx
```typescript
import { AppShell, Container, Text, Title } from '@mantine/core'
import { useEffect, useState } from 'react'
import api from './services/api'

function App() {
  const [endpoints, setEndpoints] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Test API connection
    api.get('/endpoints')
      .then(response => {
        setEndpoints(response.data)
        setLoading(false)
      })
      .catch(err => {
        console.error('API Error:', err)
        setLoading(false)
      })
  }, [])

  return (
    <AppShell padding="md">
      <AppShell.Main>
        <Container>
          <Title order={1}>FileOrbit - Mantine Edition</Title>
          <Text mt="md">
            {loading ? 'Testing API connection...' : 
             `API Connected! Found ${endpoints.length} endpoints`}
          </Text>
        </Container>
      </AppShell.Main>
    </AppShell>
  )
}

export default App
```

### 3. Update vite.config.ts
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

## Validation Steps

1. **Start the backend first**:
   ```bash
   cd /Users/timkitchens/projects/consumer-apps/file-orbit
   ./manage.sh start backend
   ```

2. **Start the new frontend**:
   ```bash
   cd frontend-mantine
   npm run dev
   ```

3. **Check these endpoints**:
   - http://localhost:3000 - Should show "FileOrbit - Mantine Edition"
   - Console should show successful API connection or error details
   - No TypeScript errors in terminal

## Success Criteria
- [ ] Dev server runs without errors
- [ ] API service imported correctly (no TS errors)
- [ ] Can fetch endpoints from backend
- [ ] Mantine UI components render correctly
- [ ] Console shows API connection status

## Important Resources
- **Mantine Docs**: Use `mcp__rag-retriever__vector_search` with `collection_name: mantine_v7_docs`
- **POC Reference**: Check `mantine-poc/src/components/` for implementation patterns
- **API Patterns**: Reference `frontend/src/pages/` for how API is used

## If API Connection Fails
1. Check backend is running: `curl http://localhost:8000/api/health`
2. Check proxy config in vite.config.ts
3. Verify .env has correct `VITE_API_URL=http://localhost:8000`
4. Check CORS settings in backend

## Next Step
Once all validation passes, proceed to Phase 1: Core Infrastructure