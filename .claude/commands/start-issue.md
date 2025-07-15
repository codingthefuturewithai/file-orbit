---
description: Start work on a new JIRA issue (feature, bug, or task) by fetching the issue, creating a branch, and updating status
usage: /project:start-issue [ISSUE-KEY] [SITE-ALIAS]
example: /project:start-issue ASEP-40 saaga
---

I'll help you start working on JIRA issue $ARGUMENTS. Let me parse the issue key and site alias, then fetch the issue details and set up your development environment.

## Parse Arguments
Let me extract the issue key and site alias from the provided arguments:
- Arguments provided: $ARGUMENTS
- Expected format: [ISSUE-KEY] [SITE-ALIAS] (e.g., "ACT-123 saaga")

## Step 1: Fetch JIRA Issue
I'll use the parsed issue key and site alias to fetch the JIRA issue:
- Use mcp__mcp_jira__search_jira_issues to search for the issue
- The JQL query will be: key = [ISSUE-KEY]
- Using the provided site_alias

## Step 2: Analyze Existing Codebase
Before creating a branch, I'll analyze the current codebase to determine if this feature:
- **Already exists** (fully implemented)
- **Partially exists** (some components in place)
- **Conflicts with existing architecture**
- **Is no longer relevant** (deprecated approach or outdated requirement)

### Analysis Strategy:
1. **Extract Key Requirements** from JIRA issue description and acceptance criteria
2. **Search for Existing Implementations**:
   - Use Grep/Task to search for keywords from the issue
   - Look for function names, class names, or patterns mentioned
   - Check for similar UI components or endpoints
   - Review recent commits for related work
3. **Analyze Project Structure**:
   - Check if mentioned files/directories already exist
   - Look for competing implementations
   - Review configuration for feature flags or existing settings
4. **Check Documentation**:
   - Search README and docs for feature mentions
   - Look for deprecated notices or architecture decisions

### Decision Points:
- **If Fully Implemented**: 
  - ❌ Stop and report findings
  - Suggest closing JIRA issue or converting to documentation task
  - Show evidence of existing implementation
  
- **If Partially Implemented**:
  - 🔄 Document what exists vs. what's missing
  - Adjust implementation plan to build on existing work
  - Note potential refactoring needs
  
- **If Conflicts Detected**:
  - ⚠️ Highlight architectural concerns
  - Suggest discussing with team before proceeding
  - Propose alternative approaches if applicable
  
- **If No Issues Found**:
  - ✅ Proceed with branch creation

## Step 3: Create Branch (If Appropriate)
After codebase analysis confirms the work is needed, I'll create an appropriate branch:

**Branch naming convention:**
- **Feature/Story**: `feature/[ISSUE-KEY]-<brief-description>`
- **Bug**: `fix/[ISSUE-KEY]-<brief-description>`  
- **Task**: `task/[ISSUE-KEY]-<brief-description>`
- **Other**: `issue/[ISSUE-KEY]-<brief-description>`

!git checkout -b [PREFIX]/[ISSUE-KEY]-<brief-description>

(The branch prefix will be automatically determined from the JIRA issue type)

## Step 4: Update JIRA Status
Use mcp__Conduit__update_jira_status to update the issue to 'In Progress' status using the provided site_alias

## Step 5: Research Technical Requirements
If needed, I'll research unfamiliar technologies mentioned in the issue:

1. **First**: Check RAG system for MCP/Claude Code topics using `/rag-search-knowledge`
2. **Then**: Use Context7 for other technologies/libraries/frameworks
3. **Priority**: RAG has current docs, Context7 may be 2-3 weeks behind for MCP/Claude topics

## Step 6: Determine Testing Approach
Based on the issue details and acceptance criteria, I'll identify the testing strategy:
- **UI Testing**: If the issue involves user interfaces, forms, or visual elements
- **MCP Testing**: If the issue involves API endpoints, tools, or integrations
- **Integration Testing**: If the issue involves system components or data flow
- **Regression Testing**: If the issue is a bug fix that needs validation
- **Hybrid**: If the issue spans multiple areas

## Step 7: Create Implementation Plan
Based on the issue's acceptance criteria and codebase analysis, I'll create a detailed implementation plan including:
- **Analysis Results**: Summary of existing implementations found
- Overview of the approach (building on existing work if applicable)
- Components to modify/create
- Implementation order
- Testing strategy (UI testing with Puppeteer, MCP testing, integration testing, or regression testing)
- Any risks or dependencies
- Special considerations for bug fixes (root cause analysis, validation approach)
- **Integration Points**: How new work will integrate with existing code

## Step 8: Request Human Review
I'll present the codebase analysis findings and implementation plan, then wait for your approval before proceeding with exit_plan_mode.

**Key Review Points**:
- Existing implementations found (if any)
- Recommended approach based on current codebase
- Any concerns about duplication or conflicts
- Confirmation that the work is still needed

Let's begin by fetching the JIRA issue details...

---

## 🚀 Next Steps After Approval

Once you approve the plan and implement the solution:

1. **Test your implementation:**
   ```
   /project:test-issue
   ```
   This will intelligently detect and run appropriate tests (UI, API, MCP, or regression)

2. **When tests pass, complete the issue:**
   ```
   /project:complete-issue $SITE_ALIAS
   ```
   This will commit, create a PR, and update JIRA to "Done"

3. **After PR is merged:**
   ```
   /project:post-merge
   ```
   This will sync your main branch and clean up

💡 **Tip:** Save your site alias - you'll need it for the complete-issue command!