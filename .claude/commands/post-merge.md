---
description: Execute post-merge actions including syncing main, re-running tests, and cleanup
usage: /project:post-merge
example: /project:post-merge
---

I'll help you complete the post-merge workflow to ensure your local environment is synchronized and the merged changes are validated.

## Step 1: Sync with Remote Main
Switching to main and pulling latest changes:

!git checkout main
!git pull origin main

Verifying your changes are included:
!git log --oneline -5

## Step 2: Re-run Feature Tests
Re-running the same tests that validated your feature:

!pytest
!ruff check .

## Step 3: Clean Up Branch
Getting the previous branch name and deleting it:

!git branch -d $(git rev-parse --abbrev-ref @{-1})

Cleaning up remote tracking branches:
!git remote prune origin

## Step 4: Update Development Environment
Ensuring dependencies are up to date:

!pip install -e ".[dev]"

## Step 5: Verify Everything Works
Running a final check to ensure the development environment is healthy:

!python -c "import conduit; print('Conduit package imported successfully')"
!pytest --collect-only | head -20

## Summary
Post-merge actions completed! Your local environment is now:
- Synchronized with the latest main branch
- All tests passing
- Issue branch cleaned up
- Dependencies updated

You're ready to start your next issue!

---

## 🚀 Next Steps

Now that your issue is merged and environment is clean:

1. **Start a new issue:**
   ```
   /project:start-issue [ISSUE-KEY] [SITE-ALIAS]
   ```
   Begin work on your next JIRA issue (feature, bug, or task)

2. **List available sites:**
   ```
   /project:list-sites
   ```
   If you need to check which Atlassian sites are configured

3. **Check JIRA board:**
   - Review your team's backlog
   - Pick up the next priority issue
   - Coordinate with your team on Slack/Teams

💡 **Tip:** Your development environment is fresh and ready for the next issue!