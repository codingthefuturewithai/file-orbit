---
description: Merge an issue locally to main and continue development without creating a PR
usage: /project:merge-issue [SITE-ALIAS]
example: /project:merge-issue saaga
---

I'll help you merge the current issue to main locally and update JIRA without creating a PR.

## Parse Arguments
- Site alias provided: $ARGUMENTS (e.g., "saaga")
- I'll extract the JIRA issue key from the current branch name

## Step 1: Review Changes
First, let me check the current status:

!git status
!git diff --stat

## Step 2: Run Quality Checks
Running linting and tests before merging:

!ruff check .
!pytest

## Step 3: Commit Changes
I'll stage all changes and create a detailed commit message:

!git add -A

The commit message will follow conventional commits format based on issue type:
- **Feature/Story**: `feat: [Description]`
- **Bug**: `fix: [Description]`
- **Task**: `task: [Description]`
- **Other**: `chore: [Description]`

The commit will include:
- Brief description
- Detailed changes
- Reference to JIRA issue
- Claude Code attribution

## Step 4: Merge to Main
Switch to main and merge the issue branch:

!git checkout main
!git merge $(git rev-parse --abbrev-ref @{-1})

## Step 5: Update JIRA to Done
After the merge, I'll:
1. Extract the JIRA issue key from the branch name (e.g., fix/ASEP-40-description → ASEP-40)
2. Update the issue status to 'Done' using mcp__Conduit__update_jira_status with the site alias
3. Add a comment about local merge completion using mcp__mcp_jira__update_jira_issue

## Step 6: Clean Up Issue Branch
Delete the merged issue branch:

!git branch -d $(git rev-parse --abbrev-ref @{-2})

Let's start by reviewing your changes...

---

## 🚀 Next Steps After Local Merge

Once your issue is merged locally:

1. **Start your next issue immediately:
   ```
   /project:start-issue [NEW-ISSUE-KEY] [SITE-ALIAS]
   ```
   Continue rapid development on the same main branch

2. **When ready to sync with remote:**
   ```
   !git push origin main
   ```
   Push all accumulated changes to remote

3. **If you need to create PRs later:**
   - Use individual commits in main to create separate PRs
   - Or create a single PR with all accumulated changes

💡 **Tip:** This workflow is perfect for rapid prototyping and continuous local development!