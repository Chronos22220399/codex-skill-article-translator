#!/usr/bin/env bash
# Publish a paper-reader project into the khronos-hub site and push.
#
# Usage:
#   publish_to_site.sh PROJECT_DIR [SITE_REPO]
#
#   PROJECT_DIR  the paper reader project (must contain translation-reading.html)
#   SITE_REPO    path to a khronos-hub clone (default: $KHRONOS_HUB or ~/khronos-hub)
set -euo pipefail

proj="${1:-}"
site="${2:-${KHRONOS_HUB:-$HOME/khronos-hub}}"

if [ -z "$proj" ]; then
    echo "usage: $0 PROJECT_DIR [SITE_REPO]" >&2
    exit 2
fi
proj="$(cd "$proj" && pwd)"
site="$(cd "$site" && pwd)"

if [ ! -f "$proj/translation-reading.html" ]; then
    echo "error: no translation-reading.html in $proj" >&2
    exit 1
fi
if [ ! -d "$site/papers" ]; then
    echo "error: $site does not look like khronos-hub (no papers/)" >&2
    exit 1
fi

name="$(basename "$proj")"
dest="$site/papers/$name"
mkdir -p "$dest"
rsync -a --delete \
    --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
    --exclude 'source-pages' --exclude 'page-renders' \
    "$proj/" "$dest/"
echo "copied project -> papers/$name"

# Copy the original PDF referenced by the reader's "open original PDF" link.
pdf_rel="$(python3 - "$dest/translation-reading.html" <<'PY'
import re, sys
html = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'href="(\.\./[^"]+)"[^>]*>\s*打开原 PDF', html)
print(m.group(1)[3:] if m else "")
PY
)"
if [ -n "$pdf_rel" ]; then
    if [ -f "$site/papers/$pdf_rel" ]; then
        echo "PDF already present: papers/$pdf_rel"
    elif [ -f "$proj/../$pdf_rel" ]; then
        cp "$proj/../$pdf_rel" "$site/papers/"
        echo "copied PDF -> papers/$pdf_rel"
    else
        echo "warn: original PDF not found ($pdf_rel); the open-PDF link may 404" >&2
    fi
fi

( cd "$site" && python3 site/build.py )

( cd "$site"
  git add -A
  if git diff --cached --quiet; then
      echo "nothing to commit"
  else
      git commit -m "papers: add $name"
      git push
      echo "pushed"
  fi
)

echo "done: $name is published (server rebuilds within ~10 min)"
