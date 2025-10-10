#!/bin/bash
# SyFi AI GitHub Issues Workflow Helper
# Usage: ./github-workflow.sh <command> [arguments]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
CHANGELOG_FILE="CHANGELOG.md"
VERSION_FILE="VERSION"

# Check if gh CLI is installed
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
        echo -e "${YELLOW}Install it with: ${NC}"
        echo "  Ubuntu/Debian: sudo apt install gh"
        echo "  macOS: brew install gh"
        echo "  Or download from: https://cli.github.com/"
        exit 1
    fi
}

# Initialize version file if it doesn't exist
init_files() {
    if [ ! -f "$VERSION_FILE" ]; then
        echo "1.0.0" > "$VERSION_FILE"
    fi

    if [ ! -f "$CHANGELOG_FILE" ]; then
        cat > "$CHANGELOG_FILE" << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

EOF
    fi
}

function show_help() {
    echo -e "${BLUE}SyFi AI GitHub Issues Workflow${NC}"
    echo ""
    echo "Commands:"
    echo -e "  ${GREEN}issue create${NC}               Create a new GitHub issue interactively"
    echo -e "  ${GREEN}issue list [state]${NC}         List issues (open|closed|all)"
    echo -e "  ${GREEN}issue start <number>${NC}       Start work on an issue"
    echo -e "  ${GREEN}issue finish <number>${NC}      Finish work and close issue"
    echo -e "  ${GREEN}release create <type>${NC}      Create a new release (major|minor|patch)"
    echo -e "  ${GREEN}hotfix start <number>${NC}      Start a hotfix branch"
    echo -e "  ${GREEN}hotfix finish <number>${NC}     Finish hotfix and merge"
    echo -e "  ${GREEN}pr create${NC}                  Create a pull request"
    echo -e "  ${GREEN}status${NC}                     Show current workflow status"
    echo -e "  ${GREEN}setup${NC}                      Setup GitHub repository"
}

function setup_github() {
    echo -e "${BLUE}🔧 Setting up GitHub repository...${NC}"
    
    # Check if already connected to GitHub
    if git remote get-url origin &>/dev/null; then
        echo -e "${GREEN}✓ Remote origin already configured${NC}"
        git remote -v
    else
        echo -e "${YELLOW}No remote origin found. Let's create a GitHub repository.${NC}"
        echo ""
        read -p "Enter GitHub repository name (default: syfi-ai): " repo_name
        repo_name=${repo_name:-syfi-ai}
        
        echo -e "${BLUE}Creating GitHub repository...${NC}"
        gh repo create "$repo_name" --public --source=. --remote=origin --push
        
        echo -e "${GREEN}✓ GitHub repository created and connected${NC}"
    fi
    
    # Authenticate with GitHub CLI if needed
    if ! gh auth status &>/dev/null; then
        echo -e "${YELLOW}Authenticating with GitHub...${NC}"
        gh auth login
    fi
    
    echo -e "${GREEN}✓ GitHub setup complete${NC}"
}

function create_issue() {
    echo -e "${BLUE}📝 Creating a new GitHub issue...${NC}"
    echo ""
    echo "Select issue type:"
    echo "1) 🚀 Feature Story"
    echo "2) 🐛 Bug Fix"
    echo "3) 🚨 Hotfix"
    echo "4) 💡 Custom"
    
    read -p "Enter choice (1-4): " choice
    
    # Create labels if they don't exist
    create_labels_if_needed
    
    case $choice in
        1)
            # Try template first, fallback to manual creation
            gh issue create --template feature-story.md 2>/dev/null || {
                echo -e "${YELLOW}Template not found, creating manually...${NC}"
                gh issue create --label "story,enhancement"
            }
            ;;
        2)
            gh issue create --template bug-fix.md 2>/dev/null || {
                echo -e "${YELLOW}Template not found, creating manually...${NC}"
                gh issue create --label "bug"
            }
            ;;
        3)
            gh issue create --template hotfix.md 2>/dev/null || {
                echo -e "${YELLOW}Template not found, creating manually...${NC}"
                gh issue create --label "hotfix,critical"
            }
            ;;
        4)
            gh issue create
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
}

function create_labels_if_needed() {
    # Create common labels if they don't exist
    local labels=("story" "bug" "hotfix" "enhancement" "critical" "in-progress" "needs-review")
    
    for label in "${labels[@]}"; do
        gh label create "$label" --description "Auto-created label" 2>/dev/null || true
    done
}

function list_issues() {
    local state=${1:-open}
    echo -e "${BLUE}📋 GitHub Issues (${state})${NC}"
    gh issue list --state "$state"
}

function start_issue() {
    local issue_number="$1"
    
    if [ -z "$issue_number" ]; then
        echo -e "${RED}Error: Issue number is required${NC}"
        echo "Usage: ./github-workflow.sh issue start 123"
        exit 1
    fi
    
    # Get issue details
    local issue_title=$(gh issue view "$issue_number" --json title --jq '.title')
    local issue_labels=$(gh issue view "$issue_number" --json labels --jq '.labels[].name' | tr '\n' ',' | sed 's/,$//')
    
    if [ -z "$issue_title" ]; then
        echo -e "${RED}Error: Issue #$issue_number not found${NC}"
        exit 1
    fi
    
    # Determine branch type and name
    local branch_type="feature"
    if echo "$issue_labels" | grep -q "hotfix"; then
        branch_type="hotfix"
    elif echo "$issue_labels" | grep -q "bug"; then
        branch_type="bugfix"
    fi
    
    # Create branch name from issue title
    local branch_suffix=$(echo "$issue_title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-zA-Z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g' | cut -c1-50)
    local branch_name="$branch_type/issue-$issue_number-$branch_suffix"
    
    # Ensure we're on main branch
    git checkout main
    git pull origin main
    
    # Create and switch to feature branch
    git checkout -b "$branch_name"
    
    # Assign issue to yourself and add in-progress label
    gh issue edit "$issue_number" --add-label "in-progress"
    
    echo -e "${GREEN}✓ Started work on issue #$issue_number${NC}"
    echo -e "Title: ${YELLOW}$issue_title${NC}"
    echo -e "Branch: ${BLUE}$branch_name${NC}"
    echo -e "Make your changes and commit with: ${YELLOW}git commit -m \"#$issue_number: Your commit message\"${NC}"
}

function finish_issue() {
    local issue_number="$1"
    
    if [ -z "$issue_number" ]; then
        echo -e "${RED}Error: Issue number is required${NC}"
        echo "Usage: ./github-workflow.sh issue finish 123"
        exit 1
    fi
    
    local current_branch=$(git branch --show-current)
    
    if [[ ! "$current_branch" =~ issue-$issue_number ]]; then
        echo -e "${RED}Error: Not on the correct branch for issue #$issue_number${NC}"
        echo -e "Current branch: $current_branch"
        exit 1
    fi
    
    # Push current branch
    git push -u origin "$current_branch"
    
    # Create pull request
    local issue_title=$(gh issue view "$issue_number" --json title --jq '.title')
    gh pr create --title "Fix #$issue_number: $issue_title" --body "Closes #$issue_number"
    
    echo -e "${GREEN}✓ Pull request created for issue #$issue_number${NC}"
    echo -e "${YELLOW}Review and merge the PR when ready${NC}"
    echo -e "${BLUE}Or use 'gh pr merge' to merge directly${NC}"
}

function create_release() {
    local release_type="$1"
    
    if [ -z "$release_type" ]; then
        echo -e "${RED}Error: Release type is required (major|minor|patch)${NC}"
        exit 1
    fi
    
    local current_version=$(cat "$VERSION_FILE")
    local new_version
    
    case "$release_type" in
        "major")
            new_version=$(echo "$current_version" | awk -F. '{print ($1+1)".0.0"}')
            ;;
        "minor")
            new_version=$(echo "$current_version" | awk -F. '{print $1"."($2+1)".0"}')
            ;;
        "patch")
            new_version=$(echo "$current_version" | awk -F. '{print $1"."$2"."($3+1)}')
            ;;
        *)
            echo -e "${RED}Error: Invalid release type. Use: major, minor, or patch${NC}"
            exit 1
            ;;
    esac
    
    echo "$new_version" > "$VERSION_FILE"
    
    # Generate changelog
    generate_changelog "$new_version"
    
    # Commit version bump
    git add "$VERSION_FILE" "$CHANGELOG_FILE"
    git commit -m "🚀 Release v$new_version"
    
    # Create and push tag
    git tag -a "v$new_version" -m "Release version $new_version"
    git push origin main --tags
    
    # Create GitHub release
    gh release create "v$new_version" --title "Release v$new_version" --notes-file "$CHANGELOG_FILE"
    
    echo -e "${GREEN}✓ Release v$new_version created on GitHub${NC}"
}

function generate_changelog() {
    local version="$1"
    local date=$(date '+%Y-%m-%d')
    
    # Get commits since last tag
    local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    
    echo -e "${BLUE}📝 Generating changelog for v$version...${NC}"
    
    # Get closed issues since last release
    local issues_since=""
    if [ -n "$last_tag" ]; then
        # Get commits that mention issues since last tag
        issues_since=$(git log "$last_tag"..HEAD --grep="#" --oneline | grep -o "#[0-9]\+" | sort -u | tr '\n' ' ')
    fi
    
    # Create release notes
    local release_notes="## [$version] - $date\n\n"
    
    if [ -n "$issues_since" ]; then
        release_notes+="### 🚀 Features\n"
        release_notes+="### 🐛 Bug Fixes\n"
        release_notes+="### 🔧 Improvements\n\n"
        
        for issue in $issues_since; do
            local issue_num=$(echo "$issue" | tr -d '#')
            local issue_title=$(gh issue view "$issue_num" --json title --jq '.title' 2>/dev/null || echo "Issue $issue_num")
            release_notes+="- $issue: $issue_title\n"
        done
    else
        release_notes+="- Initial release\n"
    fi
    
    # Update changelog
    local temp_changelog=$(mktemp)
    echo -e "$release_notes" > "$temp_changelog"
    echo "" >> "$temp_changelog"
    tail -n +4 "$CHANGELOG_FILE" >> "$temp_changelog"
    mv "$temp_changelog" "$CHANGELOG_FILE"
}

function show_status() {
    echo -e "${BLUE}📊 GitHub Workflow Status${NC}"
    echo ""
    
    # Current branch and git status
    local current_branch=$(git branch --show-current)
    echo -e "Current branch: ${GREEN}$current_branch${NC}"
    
    # Current version
    local version=$(cat "$VERSION_FILE" 2>/dev/null || echo "unknown")
    echo -e "Current version: ${YELLOW}v$version${NC}"
    
    # GitHub status
    if gh auth status &>/dev/null; then
        echo -e "GitHub CLI: ${GREEN}✓ Authenticated${NC}"
    else
        echo -e "GitHub CLI: ${RED}✗ Not authenticated${NC}"
    fi
    
    # Recent issues
    echo ""
    echo -e "${BLUE}📋 Recent Issues:${NC}"
    gh issue list --limit 5 2>/dev/null || echo "No issues found"
    
    # Git status
    echo ""
    echo -e "${BLUE}📁 Git Status:${NC}"
    git status --short
}

# Initialize files
init_files

# Main command dispatcher
case "${1:-help}" in
    "issue")
        check_gh_cli
        case "$2" in
            "create") create_issue ;;
            "list") list_issues "$3" ;;
            "start") start_issue "$3" ;;
            "finish") finish_issue "$3" ;;
            *) show_help ;;
        esac
        ;;
    "release")
        check_gh_cli
        case "$2" in
            "create") create_release "$3" ;;
            *) show_help ;;
        esac
        ;;
    "hotfix")
        check_gh_cli
        case "$2" in
            "start") start_issue "$3" ;;
            "finish") finish_issue "$3" ;;
            *) show_help ;;
        esac
        ;;
    "pr")
        check_gh_cli
        case "$2" in
            "create") gh pr create ;;
            *) show_help ;;
        esac
        ;;
    "setup") 
        check_gh_cli
        setup_github 
        ;;
    "status") show_status ;;
    "help"|*) show_help ;;
esac