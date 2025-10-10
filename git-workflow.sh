#!/bin/bash
# SyFi AI Git Workflow Helper
# Usage: ./git-workflow.sh <command> [arguments]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ISSUES_DIR=".issues"
CHANGELOG_FILE="CHANGELOG.md"
VERSION_FILE="VERSION"

# Ensure issues directory exists
mkdir -p "$ISSUES_DIR"

# Initialize version file if it doesn't exist
if [ ! -f "$VERSION_FILE" ]; then
    echo "1.0.0" > "$VERSION_FILE"
fi

# Initialize changelog if it doesn't exist
if [ ! -f "$CHANGELOG_FILE" ]; then
    cat > "$CHANGELOG_FILE" << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

EOF
fi

function show_help() {
    echo -e "${BLUE}SyFi AI Git Workflow Helper${NC}"
    echo ""
    echo "Commands:"
    echo -e "  ${GREEN}story create <id> <title>${NC}     Create a new story"
    echo -e "  ${GREEN}story list${NC}                    List all stories"
    echo -e "  ${GREEN}story start <id>${NC}              Start work on a story"
    echo -e "  ${GREEN}story finish <id> <message>${NC}   Finish story and merge"
    echo -e "  ${GREEN}release create <type>${NC}         Create a new release (major|minor|patch)"
    echo -e "  ${GREEN}hotfix create <id> <title>${NC}    Create a hotfix branch"
    echo -e "  ${GREEN}hotfix finish <id> <message>${NC}  Finish hotfix and merge"
    echo -e "  ${GREEN}changelog update${NC}              Update changelog from commits"
    echo -e "  ${GREEN}status${NC}                        Show current workflow status"
}

function create_story() {
    local story_id="$1"
    local story_title="$2"
    
    if [ -z "$story_id" ] || [ -z "$story_title" ]; then
        echo -e "${RED}Error: Story ID and title are required${NC}"
        echo "Usage: ./git-workflow.sh story create STORY-001 \"Add user authentication\""
        exit 1
    fi
    
    local story_file="$ISSUES_DIR/$story_id.md"
    
    if [ -f "$story_file" ]; then
        echo -e "${RED}Error: Story $story_id already exists${NC}"
        exit 1
    fi
    
    cat > "$story_file" << EOF
# $story_id: $story_title

**Status:** Open  
**Type:** Feature  
**Created:** $(date '+%Y-%m-%d %H:%M:%S')  
**Assignee:** $(git config user.name)

## Description
$story_title

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Notes
Add any additional notes here.
EOF
    
    echo -e "${GREEN}✓ Story $story_id created: $story_title${NC}"
    echo -e "Edit the story file: ${BLUE}$story_file${NC}"
}

function list_stories() {
    echo -e "${BLUE}📋 Current Stories${NC}"
    echo ""
    
    if [ ! -d "$ISSUES_DIR" ] || [ -z "$(ls -A $ISSUES_DIR 2>/dev/null)" ]; then
        echo -e "${YELLOW}No stories found. Create one with: ./git-workflow.sh story create STORY-001 \"Story Title\"${NC}"
        return
    fi
    
    for story_file in "$ISSUES_DIR"/*.md; do
        if [ -f "$story_file" ]; then
            local story_id=$(basename "$story_file" .md)
            local story_title=$(grep "^# $story_id:" "$story_file" | sed "s/^# $story_id: //")
            local status=$(grep "^\*\*Status:\*\*" "$story_file" | sed 's/.*Status:\*\* //')
            
            case "$status" in
                "Open")
                    echo -e "  ${YELLOW}○${NC} $story_id: $story_title"
                    ;;
                "In Progress")
                    echo -e "  ${BLUE}●${NC} $story_id: $story_title"
                    ;;
                "Done")
                    echo -e "  ${GREEN}✓${NC} $story_id: $story_title"
                    ;;
                *)
                    echo -e "  ${RED}?${NC} $story_id: $story_title"
                    ;;
            esac
        fi
    done
}

function start_story() {
    local story_id="$1"
    
    if [ -z "$story_id" ]; then
        echo -e "${RED}Error: Story ID is required${NC}"
        echo "Usage: ./git-workflow.sh story start STORY-001"
        exit 1
    fi
    
    local story_file="$ISSUES_DIR/$story_id.md"
    
    if [ ! -f "$story_file" ]; then
        echo -e "${RED}Error: Story $story_id does not exist${NC}"
        exit 1
    fi
    
    # Get story title for branch name
    local story_title=$(grep "^# $story_id:" "$story_file" | sed "s/^# $story_id: //" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-zA-Z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
    local branch_name="feature/$story_id-$story_title"
    
    # Ensure we're on main branch
    git checkout main
    
    # Create and switch to feature branch
    git checkout -b "$branch_name"
    
    # Update story status
    sed -i 's/\*\*Status:\*\* Open/\*\*Status:\*\* In Progress/' "$story_file"
    
    # Commit the status change
    git add "$story_file"
    git commit -m "Start work on $story_id

Started working on: $(grep "^# $story_id:" "$story_file" | sed "s/^# $story_id: //")"
    
    echo -e "${GREEN}✓ Started work on $story_id${NC}"
    echo -e "Branch: ${BLUE}$branch_name${NC}"
    echo -e "Make your changes and commit regularly with: ${YELLOW}git commit -m \"$story_id: Your commit message\"${NC}"
}

function finish_story() {
    local story_id="$1"
    local commit_message="$2"
    
    if [ -z "$story_id" ] || [ -z "$commit_message" ]; then
        echo -e "${RED}Error: Story ID and commit message are required${NC}"
        echo "Usage: ./git-workflow.sh story finish STORY-001 \"Implemented user authentication\""
        exit 1
    fi
    
    local story_file="$ISSUES_DIR/$story_id.md"
    local current_branch=$(git branch --show-current)
    
    if [[ ! "$current_branch" =~ ^feature/$story_id- ]]; then
        echo -e "${RED}Error: Not on the correct feature branch for $story_id${NC}"
        echo -e "Current branch: $current_branch"
        exit 1
    fi
    
    # Update story status
    sed -i 's/\*\*Status:\*\* In Progress/\*\*Status:\*\* Done/' "$story_file"
    
    # Add and commit final changes
    git add -A
    git commit -m "$story_id: $commit_message

Closes $story_id"
    
    # Switch to main and merge
    git checkout main
    git merge --no-ff "$current_branch" -m "Merge $story_id: $commit_message"
    
    # Delete feature branch
    git branch -d "$current_branch"
    
    echo -e "${GREEN}✓ Story $story_id completed and merged${NC}"
    echo -e "${YELLOW}Consider creating a release if ready${NC}"
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
    
    # Update changelog
    update_changelog "$new_version"
    
    # Commit version bump
    git add "$VERSION_FILE" "$CHANGELOG_FILE"
    git commit -m "Release v$new_version"
    
    # Create tag
    git tag -a "v$new_version" -m "Release version $new_version"
    
    echo -e "${GREEN}✓ Release v$new_version created${NC}"
    echo -e "${YELLOW}Push with: git push origin main --tags${NC}"
}

function update_changelog() {
    local version="$1"
    local date=$(date '+%Y-%m-%d')
    
    # Get commits since last tag
    local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    local commits
    
    if [ -z "$last_tag" ]; then
        commits=$(git log --oneline --pretty=format:"- %s" | head -20)
    else
        commits=$(git log "$last_tag"..HEAD --oneline --pretty=format:"- %s")
    fi
    
    # Create temporary changelog content
    local temp_changelog=$(mktemp)
    
    {
        echo "# Changelog"
        echo ""
        echo "All notable changes to this project will be documented in this file."
        echo ""
        echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
        echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
        echo ""
        echo "## [Unreleased]"
        echo ""
        if [ -n "$version" ]; then
            echo "## [$version] - $date"
            echo ""
            if [ -n "$commits" ]; then
                echo "$commits"
            else
                echo "- Initial release"
            fi
            echo ""
        fi
        
        # Add existing changelog content (skip header)
        tail -n +9 "$CHANGELOG_FILE" 2>/dev/null | grep -v "^## \[Unreleased\]" | grep -v "^$" -m 1 -A 1000 || true
    } > "$temp_changelog"
    
    mv "$temp_changelog" "$CHANGELOG_FILE"
}

function show_status() {
    echo -e "${BLUE}📊 Workflow Status${NC}"
    echo ""
    
    # Current branch
    local current_branch=$(git branch --show-current)
    echo -e "Current branch: ${GREEN}$current_branch${NC}"
    
    # Current version
    local version=$(cat "$VERSION_FILE" 2>/dev/null || echo "unknown")
    echo -e "Current version: ${YELLOW}v$version${NC}"
    
    # Git status
    echo ""
    echo -e "${BLUE}Git Status:${NC}"
    git status --short
    
    # Recent commits
    echo ""
    echo -e "${BLUE}Recent Commits:${NC}"
    git log --oneline -5
    
    echo ""
    list_stories
}

# Main command dispatcher
case "${1:-help}" in
    "story")
        case "$2" in
            "create") create_story "$3" "$4" ;;
            "list") list_stories ;;
            "start") start_story "$3" ;;
            "finish") finish_story "$3" "$4" ;;
            *) show_help ;;
        esac
        ;;
    "release")
        case "$2" in
            "create") create_release "$3" ;;
            *) show_help ;;
        esac
        ;;
    "changelog")
        case "$2" in
            "update") update_changelog ;;
            *) show_help ;;
        esac
        ;;
    "status") show_status ;;
    "help"|*) show_help ;;
esac