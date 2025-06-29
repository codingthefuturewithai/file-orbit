# Event Rules to Transfer Templates Migration Summary

## Overview
Complete removal of all "event rules" terminology from the codebase and replacement with "transfer templates".

## Backend Changes

### 1. Database Schema
- Table renamed: `event_rules` → `transfer_templates`
- Foreign key in jobs table: `event_rule_id` → `transfer_template_id`
- Migration script created: `migrate_event_rules_to_transfer_templates.py`

### 2. Models
- `app/models/event_rule.py` → `app/models/transfer_template.py`
- Class renamed: `EventRule` → `TransferTemplate`
- Updated table name in SQLAlchemy model

### 3. Schemas
- `app/schemas/event_rule.py` → `app/schemas/transfer_template.py`
- Classes renamed:
  - `EventRuleBase` → `TransferTemplateBase`
  - `EventRuleCreate` → `TransferTemplateCreate`
  - `EventRuleUpdate` → `TransferTemplateUpdate`
  - `EventRuleResponse` → `TransferTemplateResponse`

### 4. API Endpoints
- `app/api/api_v1/endpoints/event_rules.py` → `app/api/api_v1/endpoints/transfer_templates.py`
- Route changed: `/event-rules` → `/transfer-templates`
- All function names and variables updated

### 5. Services
- Updated all event monitoring services to use `TransferTemplate`
- Updated imports in:
  - `event_monitor.py`
  - `s3_event_monitor.py`
  - `file_watcher.py`
  - `event_monitor_service.py`

### 6. Other Backend Files
- `worker.py`: Updated to use `transfer_template_id`
- `init_db.py`: Updated table creation
- `seed_db.py`: Updated seeding functions
- `test_event_driven.py`: Updated test scripts

## Frontend Changes

### 1. Pages
- `src/pages/EventRules.tsx` → `src/pages/TransferTemplates.tsx`
- All component names and variables updated

### 2. Types
- `src/types/index.ts`: `EventRule` interface → `TransferTemplate`

### 3. Routing
- `src/App.tsx`: Route changed from `/event-rules` to `/transfer-templates`

### 4. Components
- `src/components/CreateTransferForm.tsx`: Updated to use transfer templates

### 5. API Calls
- All API endpoints updated from `/event-rules` to `/transfer-templates`

## Documentation Updates
- `SETUP_GUIDE.md`: Updated references
- `SCAFFOLD_STATUS.md`: Updated model descriptions
- `README.md`: Updated feature descriptions

## Migration Instructions

To migrate an existing database:

1. Stop all services:
   ```bash
   ./manage.sh stop
   ```

2. Run the migration script:
   ```bash
   cd backend
   python migrate_event_rules_to_transfer_templates.py
   ```

3. Restart services:
   ```bash
   cd ..
   ./manage.sh start
   ```

For a fresh installation, simply run `init_db.py` and the new schema will be used.

## Verification

After migration, verify:
1. Database table is renamed to `transfer_templates`
2. API endpoints respond at `/api/v1/transfer-templates`
3. Frontend shows "Transfer Templates" in navigation
4. All CRUD operations work correctly