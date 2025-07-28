#!/bin/bash
# ================================================================================================
# Git Helper Script - Clean Operations Without Credential Warnings
# Usage: ./git_helper.sh [push|pull|status|commit|add|log] [message]
# ================================================================================================

# Parse command line arguments
OPERATION=""
MESSAGE=""

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 [push|pull|status|commit|add|log] [message]"
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 commit 'Your commit message'"
    echo "  $0 push"
    exit 1
fi

OPERATION="$1"
MESSAGE="$2"

# Validate operation
case "$OPERATION" in
    push|pull|status|commit|add|log)
        ;;
    *)
        echo "Error: Invalid operation '$OPERATION'"
        echo "Valid operations: push, pull, status, commit, add, log"
        exit 1
        ;;
esac

# Color output functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

function print_success() { echo -e "${GREEN}✅ $1${NC}"; }
function print_error() { echo -e "${RED}❌ $1${NC}"; }
function print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
function print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

echo -e "${GREEN}🔧 Git Helper - Clean Operations${NC}"
echo -e "${GREEN}=================================${NC}"

# Suppress some git warnings
export GIT_TERMINAL_PROMPT=0
export GCM_CREDENTIAL_STORE="dpapi"

case "$OPERATION" in
    status)
        echo -e "${YELLOW}📊 Checking repository status...${NC}"
        git status
        ;;
    
    add)
        echo -e "${YELLOW}➕ Adding all changes...${NC}"
        git add -A
        git status --short
        ;;
    
    commit)
        if [[ -z "$MESSAGE" ]]; then
            print_error "Commit message required!"
            echo -e "${GRAY}Usage: $0 commit 'Your message here'${NC}"
            exit 1
        fi
        echo -e "${YELLOW}💾 Committing changes...${NC}"
        git add -A
        git commit -m "$MESSAGE"
        ;;
    
    push)
        echo -e "${YELLOW}⬆️ Pushing to remote repository...${NC}"
        echo -e "${CYAN}📡 Connecting to origin/master...${NC}"
        
        # Capture output and filter credential warnings
        PUSH_OUTPUT=$(git push origin master 2>&1)
        PUSH_EXIT_CODE=$?
        
        # Filter out credential warnings but show important messages
        FILTERED_OUTPUT=$(echo "$PUSH_OUTPUT" | grep -v -E "(Unable to persist credentials|credential helper|askpass)")
        
        if [[ $PUSH_EXIT_CODE -eq 0 ]]; then
            if [[ -n "$FILTERED_OUTPUT" ]]; then
                echo "$FILTERED_OUTPUT"
            fi
            print_success "Successfully pushed to remote repository"
        else
            print_error "Push failed!"
            echo "$FILTERED_OUTPUT"
            exit 1
        fi
        ;;
    
    pull)
        echo -e "${YELLOW}⬇️ Pulling from remote repository...${NC}"
        echo -e "${CYAN}📡 Connecting to origin/master...${NC}"
        
        # Capture output and filter credential warnings  
        PULL_OUTPUT=$(git pull origin master 2>&1)
        PULL_EXIT_CODE=$?
        
        # Filter out credential warnings
        FILTERED_OUTPUT=$(echo "$PULL_OUTPUT" | grep -v -E "(Unable to persist credentials|credential helper|askpass)")
        
        if [[ $PULL_EXIT_CODE -eq 0 ]]; then
            if [[ -n "$FILTERED_OUTPUT" ]]; then
                echo "$FILTERED_OUTPUT"
            fi
            print_success "Successfully pulled from remote repository"
        else
            print_error "Pull failed!"
            echo "$FILTERED_OUTPUT"
            exit 1
        fi
        ;;
    
    log)
        echo -e "${YELLOW}📜 Showing recent commits...${NC}"
        git log --oneline -10 --graph --decorate
        ;;
esac

echo -e "\n${GREEN}🎉 Git operation completed!${NC}"
