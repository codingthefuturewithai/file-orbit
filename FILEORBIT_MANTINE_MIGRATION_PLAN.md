# FileOrbit Frontend Migration Plan: Shadcn → Mantine

## Overview
Complete rewrite of FileOrbit frontend using Mantine UI, maintaining all existing functionality while improving UI/UX and developer experience.

## Directory Structure
```
file-orbit/
├── frontend/                 # KEEP - Existing Shadcn frontend (reference only)
├── frontend-mantine/         # NEW - Fresh Mantine frontend
├── mantine-poc/             # KEEP - POC for component reference
├── backend/                 # Unchanged - Continue using same backend
└── FILEORBIT_MANTINE_MIGRATION_PLAN.md  # This file
```

## High-Level Phases

### Phase 0: Foundation Setup (Day 1)
- Create `frontend-mantine/` with Vite + React + TypeScript
- Setup Mantine with all required packages
- Copy API client and types from existing frontend
- Setup routing and basic layout
- **Validation**: Dev server runs, API client can fetch endpoints

### Phase 1: Core Infrastructure (Day 1-2)
- Endpoints management (CRUD)
- Basic navigation and layout
- Authentication placeholder
- Error handling and notifications
- **Validation**: Can create, view, edit, delete endpoints

### Phase 2: Transfer Management (Day 2-3)
- Transfer list with data table
- Transfer creation (multi-step form)
- Transfer history and filtering
- Transfer status monitoring
- **Validation**: Can create transfers and monitor progress

### Phase 3: Advanced Features (Day 3-4)
- Transfer templates
- Event rules (if implemented)
- System logs viewer
- Settings/configuration
- **Validation**: Feature parity with existing frontend

### Phase 4: Polish & Testing (Day 4-5)
- UI/UX refinements
- Performance optimization
- Comprehensive testing
- Documentation update
- **Validation**: Ready for production use

---

## Detailed Phase Plans

### Phase 0: Foundation Setup

#### Commands to Execute:
```bash
# Create new frontend directory
cd /Users/timkitchens/projects/consumer-apps/file-orbit
npm create vite@latest frontend-mantine -- --template react-ts
cd frontend-mantine

# Install Mantine and dependencies
npm install @mantine/core @mantine/hooks @mantine/form @mantine/dates \
  @mantine/notifications @mantine/modals @mantine/dropzone \
  @tabler/icons-react dayjs

# Install routing and API dependencies  
npm install react-router-dom axios

# Copy API service and types
mkdir -p ./src/services
cp ../frontend/src/services/api.ts ./src/services/
cp -r ../frontend/src/types ./src/  # If exists
cp ../frontend/.env.example .env.example
cp ../frontend/.env .env 2>/dev/null || cp ../frontend/.env.example .env

# Start dev server
npm run dev
```

#### File Structure to Create:
```
frontend-mantine/src/
├── services/              # API service (copied from existing)
│   └── api.ts
├── types/                 # Type definitions (if they exist)
├── components/
│   ├── Layout/
│   │   ├── AppShell.tsx   # Main layout with navigation
│   │   └── Navigation.tsx  # Side navigation component
│   └── common/
│       └── ErrorBoundary.tsx
├── pages/
│   ├── Dashboard.tsx
│   ├── Endpoints/
│   ├── Transfers/
│   └── Settings/
├── hooks/
│   └── useApi.ts          # API hooks
├── App.tsx
└── main.tsx
```

#### Main.tsx Template:
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

---

### Phase 1: Core Infrastructure

#### 1.1 AppShell Layout
Reference: `mantine-poc/src/App.tsx` for structure

Create navigation matching existing routes:
- Dashboard (/)
- Endpoints (/endpoints)
- Transfers (/transfers)
- Transfer History (/history)
- Templates (/templates)
- Logs (/logs)
- Settings (/settings)

#### 1.2 Endpoints Management
Reference: 
- Existing: `frontend/src/pages/Endpoints.tsx`
- Pattern: `mantine-poc/src/components/DataTableExample.tsx`

Features to implement:
- List endpoints in data table
- Create endpoint modal
- Edit endpoint modal  
- Delete endpoint confirmation
- Test connection functionality

#### 1.3 API Integration
Reuse existing API client with minor adjustments:
- Update error handling to use Mantine notifications
- Add loading states using Mantine's LoadingOverlay
- Integrate with React Query if desired

---

### Phase 2: Transfer Management

#### 2.1 Transfer List
Reference:
- Existing: `frontend/src/components/TransferList.tsx`
- Pattern: `mantine-poc/src/components/DataTableExample.tsx`

Features:
- Active transfers with progress
- Status badges (completed, failed, in_progress, pending)
- Pause/resume/retry actions
- Real-time updates via polling

#### 2.2 Create Transfer Form
Reference:
- Existing: `frontend/src/components/CreateTransferForm.tsx`
- Pattern: `mantine-poc/src/components/ComplexFormExample.tsx`

Steps to match:
1. Basic Info
2. Source Configuration
3. Destination Configuration  
4. Transfer Options
5. Schedule (if applicable)

#### 2.3 Transfer History
Reference: `frontend/src/pages/TransferHistory.tsx`

Features:
- Historical data table
- Date range filtering
- Status filtering
- Export functionality

---

### Phase 3: Advanced Features

#### 3.1 Transfer Templates
Reference: `frontend/src/pages/TransferTemplates.tsx`
- CRUD operations for templates
- Apply template to new transfer

#### 3.2 System Logs
Reference: `frontend/src/pages/Logs.tsx`
- Log viewer with Monaco editor
- Auto-refresh capability
- Download logs

#### 3.3 Settings
Reference: `frontend/src/pages/Settings.tsx`
- Application configuration
- User preferences
- System information

---

### Phase 4: Polish & Testing

#### 4.1 UI/UX Improvements
- Consistent spacing and sizing
- Loading states for all async operations
- Error boundaries and fallbacks
- Keyboard navigation support
- Mobile responsiveness

#### 4.2 Performance
- Code splitting with React.lazy
- Optimize bundle size
- Implement virtual scrolling for large lists

#### 4.3 Testing Checklist
- [ ] All endpoints CRUD operations work
- [ ] Transfer creation flow complete
- [ ] Transfer monitoring updates in real-time
- [ ] History filtering and pagination work
- [ ] Templates can be created and applied
- [ ] Logs display and auto-refresh
- [ ] Dark mode works throughout
- [ ] No console errors
- [ ] All API errors handled gracefully

---

## Migration Commands for New Session

```bash
# Step 1: Navigate to project
cd /Users/timkitchens/projects/consumer-apps/file-orbit

# Step 2: Read this plan
cat FILEORBIT_MANTINE_MIGRATION_PLAN.md

# Step 3: Start Phase 0
# Follow the detailed phase plans above

# Step 4: Reference POC for patterns
# Check mantine-poc/src/components/* for implementation patterns

# Step 5: Reference existing frontend for features
# Check frontend/src/* for business logic and API usage
```

## Success Criteria

Each phase should result in a working, testable subset of functionality:
- Phase 0: Basic app shell loads, can call API
- Phase 1: Can manage endpoints completely  
- Phase 2: Can create and monitor transfers
- Phase 3: All features available
- Phase 4: Production-ready quality

## Important Notes

1. **Keep both frontends** until migration is complete
2. **Test against same backend** throughout migration
3. **Copy API responses** to ensure compatibility
4. **Maintain URL structure** for easy switch-over
5. **Document any deviations** from original functionality

## Available Resources

### Mantine Documentation
A vector store collection named `mantine_v7_docs` is available via RAG retriever.
Use it when you need help with Mantine components:
```
mcp__rag-retriever__vector_search
- collection_name: mantine_v7_docs
- query_text: "your question about Mantine"
```

### Reference Code
1. **POC Components** at `mantine-poc/src/components/`:
   - DataTableExample.tsx - for transfer lists/history
   - ComplexFormExample.tsx - for multi-step forms
   - FileUploadExample.tsx - for file handling

2. **Existing Frontend** at `frontend/src/`:
   - pages/ - for feature requirements
   - services/api.ts - for API integration patterns
   - components/ - for business logic

### API Endpoints Reference
All API calls use axios instance from `services/api.ts`:
- GET `/api/v1/endpoints` - List endpoints
- POST `/api/v1/endpoints` - Create endpoint
- PUT `/api/v1/endpoints/{id}` - Update endpoint
- DELETE `/api/v1/endpoints/{id}` - Delete endpoint
- GET `/api/v1/jobs` - List transfers
- POST `/api/v1/jobs` - Create transfer
- GET `/api/v1/jobs/{id}` - Get transfer details
- PUT `/api/v1/jobs/{id}/pause` - Pause transfer
- PUT `/api/v1/jobs/{id}/resume` - Resume transfer
- PUT `/api/v1/jobs/{id}/retry` - Retry transfer

## When You're Done

1. Update `manage.sh` to point to new frontend
2. Update `docker-compose.yml` if needed
3. Archive old frontend: `mv frontend frontend-shadcn-archived`
4. Rename new frontend: `mv frontend-mantine frontend`
5. Update all documentation

---

This plan provides a clear, incremental path from the current Shadcn implementation to a clean Mantine-based frontend, with validation points at each phase to ensure nothing is broken.