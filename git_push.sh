#!/usr/bin/env bash
# Initializes git repo (if needed), commits current stage, and pushes to GitHub.
#
# Usage:
#   ./git_push.sh "Stage 1: scaffolding" https://github.com/<you>/<repo>.git
#
# First run will: git init, set branch to main, add remote, commit, push.
# Subsequent runs: just commit + push (remote arg optional after first run).

set -e

COMMIT_MSG="${1:-chore: update}"
REMOTE_URL="$2"

if [ ! -d .git ]; then
  echo ">> Initializing git repo"
  git init
  git branch -M main
fi

if [ -n "$REMOTE_URL" ] && ! git remote get-url origin >/dev/null 2>&1; then
  echo ">> Adding remote origin: $REMOTE_URL"
  git remote add origin "$REMOTE_URL"
fi

git add .
git commit -m "$COMMIT_MSG" || echo ">> Nothing to commit"
git push -u origin main
