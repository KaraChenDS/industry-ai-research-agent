#!/bin/sh
# Explicitly invoked by the repository owner; excludes local fieldwork.
set -eu
cd "$(dirname "$0")/.."
command -v gh >/dev/null 2>&1 || { echo 'Install GitHub CLI from https://cli.github.com first.'; exit 1; }
gh auth status >/dev/null 2>&1 || { echo 'Please run: gh auth login'; exit 1; }
if [ -n "$(git status --porcelain)" ]; then
  echo 'Commit the intended code changes first; no automatic upload of unreviewed files.'
  exit 1
fi
if git ls-files | grep -Eq '(^data/|(^|/)\.env$|^exports/)'; then
  echo 'Private local data is tracked. Remove it from the Git index before publishing.'
  exit 1
fi
if git remote get-url origin >/dev/null 2>&1; then
  echo 'An origin remote already exists. Review it before running git push.'
  exit 1
fi
gh repo create industry-ai-research-agent --public --source=. --remote=origin --push \
  --description 'Evidence-led industry AI research agent: planning, fieldwork, sample analysis and reports. Startup-office demo included.'
