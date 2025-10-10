# GitHub Issues Workflow Guide

This guide explains how to use GitHub Issues for story-driven development, similar to Jira workflows.

## 🚀 Quick Start

### 1. Setup (One-time)
```bash
# Install GitHub CLI (if not already installed)
# Ubuntu/Debian: sudo apt install gh
# macOS: brew install gh

# Setup the repository
./github-workflow.sh setup
```

### 2. Create a Story/Issue
```bash
# Interactive issue creation
./github-workflow.sh issue create

# Or create directly on GitHub web interface
```

### 3. Start Working on a Story
```bash
# Start work on issue #123
./github-workflow.sh issue start 123

# This will:
# - Create a branch: feature/issue-123-story-title
# - Add "in-progress" label
# - Switch to the new branch
```

### 4. Make Changes
```bash
# Make your code changes
# Commit with issue reference
git add .
git commit -m "#123: Implement user authentication"
```

### 5. Finish the Story
```bash
# Finish issue #123
./github-workflow.sh issue finish 123

# This will:
# - Push your branch
# - Create a pull request
# - Link it to the issue
```

### 6. Create Releases
```bash
# Create a new release (patch/minor/major)
./github-workflow.sh release create minor

# This will:
# - Bump version number
# - Generate changelog
# - Create GitHub release
# - Auto-generate release notes
```

## 📋 Issue Types

### 🚀 Feature Story
Use for new features or enhancements
- Template includes: Description, Acceptance Criteria, Tasks, DoD
- Label: `story`, `enhancement`

### 🐛 Bug Fix  
Use for bug reports and fixes
- Template includes: Steps to reproduce, Expected vs Actual behavior
- Label: `bug`

### 🚨 Hotfix
Use for critical issues needing immediate attention
- Template includes: Impact assessment, Rollback plan
- Label: `hotfix`, `critical`

## 🔄 Workflow States

1. **Open** - Issue created, awaiting assignment
2. **In Progress** - Developer working on it (auto-applied)
3. **Review** - Pull request created, awaiting review
4. **Done** - Issue closed, merged to main

## 🏷️ Labeling Strategy

- **Type**: `story`, `bug`, `hotfix`, `enhancement`
- **Priority**: `critical`, `high`, `medium`, `low`
- **Status**: `in-progress`, `needs-review`, `blocked`
- **Size**: `small`, `medium`, `large`, `epic`

## 🎯 Best Practices

### Writing Good Issues
1. **Clear Title**: Use descriptive titles that explain the goal
2. **Acceptance Criteria**: Define what "done" looks like
3. **Break Down Large Work**: Split epics into smaller stories
4. **Link Dependencies**: Use "depends on" and "blocks" relationships

### Branch Naming
- Features: `feature/issue-123-short-description`
- Bugs: `bugfix/issue-456-fix-login-error`
- Hotfixes: `hotfix/issue-789-security-patch`

### Commit Messages
- Always reference the issue: `#123: Add user validation`
- Use imperative mood: "Add", "Fix", "Update"
- Be descriptive but concise

### Pull Requests
- Use "Closes #123" in PR description to auto-close issues
- Keep PRs focused on single issues
- Request reviews before merging

## 📊 Tracking Progress

### View Current Status
```bash
./github-workflow.sh status
```

### List Issues
```bash
# List open issues
./github-workflow.sh issue list

# List all issues
./github-workflow.sh issue list all

# List closed issues  
./github-workflow.sh issue list closed
```

## 🔧 Automation Features

### Auto Release Notes
- GitHub Actions automatically generate release notes
- Includes closed issues and commit messages
- Triggered when you create version tags

### Auto Branch Creation
- Branch names generated from issue titles
- Consistent naming across the project
- Automatic label management

### Auto Issue Linking
- Commits with "#123" automatically link to issues
- Pull requests can auto-close issues
- Dependency tracking between issues

## 🎨 GitHub Web Interface

You can also use GitHub's web interface for:
- Creating issues with templates
- Managing project boards (Kanban view)
- Code review and discussions
- Release management

## 🔍 Example Workflow

```bash
# 1. Create a new feature story
./github-workflow.sh issue create
# Select "Feature Story" template
# Fill in: "Add customer profile filtering"

# 2. Start working (assuming issue #42 was created)
./github-workflow.sh issue start 42
# Creates branch: feature/issue-42-add-customer-profile-filtering

# 3. Make changes
git add src/filters.py
git commit -m "#42: Implement customer profile filter logic"

git add templates/profiles.html  
git commit -m "#42: Add profile filter UI components"

# 4. Finish the work
./github-workflow.sh issue finish 42
# Creates PR, links to issue #42

# 5. After PR is merged, create release
./github-workflow.sh release create minor
# Creates v1.1.0 with auto-generated release notes
```

This workflow provides the same structure and discipline as Jira while leveraging GitHub's integrated tooling!