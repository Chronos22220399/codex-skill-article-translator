#!/usr/bin/env bash
# Publish a paper-reader project into the khronos-hub site and push.
#
# Usage:
#   publish_to_site.sh [--dry-run] PROJECT_DIR [SITE_REPO]
#
#   --dry-run, -n  copy + build only; do NOT commit or push (for preview)
#   PROJECT_DIR    the paper reader project (must contain translation-reading.html)
#   SITE_REPO      path to a khronos-hub clone (default: $KHRONOS_HUB or ~/khronos-hub)
set -euo pipefail

dry_run=0
args=()
for arg in "$@"; do
    case "$arg" in
        --dry-run|-n) dry_run=1 ;;
        -h|--help)
            sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) args+=("$arg") ;;
    esac
done
set -- "${args[@]:-}"

proj="${1:-}"
site="${2:-${KHRONOS_HUB:-$HOME/khronos-hub}}"

if [ -z "$proj" ]; then
    echo "usage: $0 [--dry-run] PROJECT_DIR [SITE_REPO]" >&2
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
m = re.search(r'href="(\.\./[^"]+\.pdf)"', html)
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

if [ "$dry_run" = "1" ]; then
    echo
    echo "dry-run: copied + built, NOT committed or pushed."
    echo "preview locally:  (cd \"$site\" && python3 -m http.server 8080 -d dist)"
    echo "                  then open http://localhost:8080"
    echo "when happy, run again without --dry-run to commit and push."
    exit 0
fi

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
