#!/usr/bin/env bash
# deploy-game.sh <game-slug>
# Copies the game's dist/ artifacts into the repo, regenerates landing + about pages, commits + pushes.
# Idempotent — safe to re-run.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <game-slug>" >&2
  exit 1
fi

SLUG="$1"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_DIST="${STUDIO_PROJECTS:-$HOME/.openclaw/workspace/studio/projects}/$SLUG/game/dist"

if [[ ! -d "$SOURCE_DIST" ]]; then
  echo "error: source dist not found at $SOURCE_DIST" >&2
  exit 2
fi

cd "$REPO_ROOT"

# Verify slug is in the manifest
if ! python3 -c "import json,sys; data=json.load(open('games.json')); sys.exit(0 if any(g['slug']=='$SLUG' for g in data['games']) else 1)"; then
  echo "error: slug '$SLUG' is not in games.json" >&2
  exit 3
fi

echo "[deploy-game] $SLUG ← $SOURCE_DIST"
python3 scripts/render.py --copy-dist "$SLUG" "$SOURCE_DIST"

if git diff --quiet && git diff --cached --quiet; then
  echo "[deploy-game] no changes — nothing to commit"
  exit 0
fi

git add -A
git -c user.email="thebott@brotatotes.local" -c user.name="The Bott" \
  commit -m "deploy: $SLUG → arcade"
git push origin main
echo "[deploy-game] pushed"
