# Known Issues - Mantine Migration

This document tracks known issues and missing features in the Mantine frontend migration.

## 🐛 Bugs

### 1. Template Selection Error in Create Transfer Form
**Location**: Create Transfer modal > Basic Info step  
**Issue**: When selecting "From Template - Use existing template", attempting to select a template shows error:
```
Uncaught (in promise) Error: Unlisted TLDs in URLs are not supported.
```
**Impact**: Cannot create transfers from templates  
**Status**: Not fixed

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

## 🎯 Next Steps

1. **Priority 1**: Fix the template selection error in Create Transfer form
2. **Priority 2**: Implement settings API endpoints in the backend
3. **Priority 3**: Update gitignore to be more specific about what to ignore
4. **Priority 4**: Add comprehensive error handling throughout the app

## 📅 Last Updated
July 15, 2025