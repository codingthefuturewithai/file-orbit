# Known Issues - Mantine Migration

This document tracks known issues and missing features in the Mantine frontend migration.

## 🐛 Bugs

### 1. Template Selection Validation Bug in Create Transfer Form
**Location**: Create Transfer modal > Basic Info step  
**Issue**: When selecting "From Template - Use existing template" and choosing a template from the dropdown:
- The template appears selected in the dropdown
- But the form validation shows "Please select a template" error
- The Next button remains disabled/won't proceed
- No console errors - this is a form validation issue
**Impact**: Cannot create transfers from templates  
**Status**: Not fixed  
**Note**: Manual and Scheduled transfer types work correctly

## 🚧 Not Yet Implemented Features

### 1. Settings Persistence
**Location**: Settings page (all tabs)  
**Issue**: Settings are not saved or restored. The UI shows forms and allows changes, but:
- No API endpoints exist for saving/loading settings
- All values are hardcoded defaults
- "Save Changes" button only shows a success notification but doesn't persist data
**Impact**: Settings changes are lost on page refresh  
**Status**: Backend implementation needed

### 2. Templates Page - Missing Features
**Location**: Templates page  
**Missing**:
- Chain rules functionality may not work properly with the API
- Source config fields for file watching paths might need validation

### 3. Real-time Features
**Location**: Various pages  
**Potential Issues**:
- Transfer progress updates depend on worker.py running
- Log auto-refresh requires backend services to be generating logs
- Event-triggered transfers require event monitoring services

### 4. Transfer Functionality Not Fully Tested
**Location**: Transfers page, Create Transfer form  
**Issue**: Since the Mantine UI redesign, actual transfer creation and execution hasn't been tested
**Unknown Status**:
- Whether manual transfers execute properly
- Whether scheduled transfers work
- Whether the job execution flow works end-to-end
- Whether progress monitoring updates correctly
**Next Step**: Need to test creating and running actual transfers with the new UI

## 📝 Minor UI/UX Issues

### 1. Dark Theme Consistency
**Location**: Various components  
**Issue**: Some components may not fully respect the dark theme
- Log viewer background is correctly dark
- Other areas might need theme adjustments

### 2. Error Handling
**Location**: Throughout the app  
**Issue**: Some API errors might not be gracefully handled
- Need better user feedback for failed operations
- Loading states could be improved

## 🔧 Configuration Issues

### 1. GitIgnore Conflict
**Location**: `.gitignore` files  
**Issue**: The frontend-mantine/.gitignore has "logs" on line 2, which prevents the Logs page component from being tracked by git
**Workaround**: Use `git add -f` to force add files in the Logs directory
**Fix**: Should be "logs/" instead of "logs" to only ignore the logs directory, not all files/folders containing "logs"

### 2. Frontend Directory Migration Needed
**Location**: Project root  
**Issue**: Need to replace the old React frontend with the new Mantine frontend
**Tasks**:
- Remove the current `frontend` directory
- Rename `frontend-mantine` to `frontend`
- Update all references in:
  - manage.sh script
  - Documentation files (README.md, CLAUDE.md, etc.)
  - Docker configurations if any
  - GitHub Actions if any
**Impact**: Two frontends exist side-by-side causing confusion
**Status**: Not started

## 🎯 Next Steps

1. **Priority 1**: Fix the template selection error in Create Transfer form
2. **Priority 2**: Implement settings API endpoints in the backend
3. **Priority 3**: Update gitignore to be more specific about what to ignore
4. **Priority 4**: Add comprehensive error handling throughout the app

## 📅 Last Updated
July 15, 2025