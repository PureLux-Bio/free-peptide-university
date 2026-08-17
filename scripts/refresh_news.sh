#!/usr/bin/env bash
# Free Peptide University — weekly "This Week in Peptides" refresh.
# Pulls latest, regenerates data/news.json, and pushes only if it changed.
# Scheduled via local cron (org policy blocks GitHub Actions from writing to the
# repo). Safe to run manually anytime: scripts/refresh_news.sh
set -uo pipefail

REPO="$HOME/Code/free-peptide-university"
cd "$REPO" || exit 0

git pull --rebase --quiet origin main 2>/dev/null || true
python3 scripts/fetch_news.py || exit 0

if ! git diff --quiet data/news.json 2>/dev/null; then
  git add data/news.json
  git commit -q -m "chore(news): refresh This Week in Peptides ($(date +%Y-%m-%d))"
  git push --quiet origin main && echo "$(date) pushed news refresh"
else
  echo "$(date) no news changes"
fi
