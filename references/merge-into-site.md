# Merging a Paper Reader into the Site

This skill renders a standalone interactive reader. The **public site**
(`khronos-hub`) is what publishes it: the site auto-lists every
`papers/<name>-paper-reader/` folder, injects the annotation/bookmark widget, and
(after a push) the server rebuilds within ~10 minutes.

## One-time setup per device

```bash
# skill (this repo)
git clone git@github.com:Chronos22220399/codex-skill-article-translator.git ~/code/skill/paper_reader
ln -s ~/code/skill/paper_reader ~/.config/opencode/skills/paper_reader

# site
git clone git@github.com:Chronos22220399/khronos-hub.git ~/khronos-hub
```

Requirements: `python3`, `git`, `rsync`, and a GitHub SSH key on the device
(Settings -> SSH and GPG keys).

Keep the skill on the **same commit** on every device; otherwise the generated
HTML can differ (for example missing `data-block-id`). Update with
`git -C ~/code/skill/paper_reader pull`.

## Translate

Run the `paper_reader` skill on the PDF. It produces a project folder (see
`SKILL.md` -> Project Layout) and renders `translation-reading.html`.

## Publish (one command)

```bash
# from the skill repo, or use the absolute path
~/code/skill/paper_reader/scripts/publish_to_site.sh /path/to/<name>-paper-reader ~/khronos-hub
```

Preview without committing (copy + build only):

```bash
~/code/skill/paper_reader/scripts/publish_to_site.sh --dry-run /path/to/<name>-paper-reader ~/khronos-hub
# then: (cd ~/khronos-hub && python3 -m http.server 8080 -d dist)
```

It will:
1. copy the project into `papers/<name>-paper-reader/` (skipping `.venv`,
   `source-pages/`, `assets/page-renders/`, `.git`);
2. copy the original PDF referenced by the reader's `打开原 PDF` link into
   `papers/` (the site build renames it to `<slug>-source.pdf` and serves it);
3. run `python3 site/build.py` (lists the reader, injects the widget);
4. commit and push.

Nothing else is needed; the server pulls and rebuilds on its own.

Manual equivalent:

```bash
cp -r <project> ~/khronos-hub/papers/<name>-paper-reader
cp <original>.pdf ~/khronos-hub/papers/
cd ~/khronos-hub && python3 site/build.py
git add -A && git commit -m "papers: add <name>" && git push
```

## Conventions

- Folder name: `papers/<name>-paper-reader/` (the folder name is the module id).
- The reader's `打开原 PDF` link must be `../<pdf>` and the PDF must live in
  `papers/` next to the folders.
- Commit the project's `alignment.json`, `glossary.md`, `style-guide.md`,
  `translation/`, `references.json`, `figure-map.json`, `summary.md` so the
  reader stays reproducible and another session can continue the work.
- Never hand-edit `translation-reading.html`; regenerate it with
  `scripts/build_reader.py`.

## What the site adds on top of the skill output

- Invite-only login gate and the annotation/bookmark widget, injected at build
  time by `khronos-hub/site/build.py`. The raw skill output has no widget.
- Home-page listing of the reader.

## New device checklist

1. Install `git`, `python3`, `rsync`; add the device's SSH key to GitHub.
2. Clone the skill and the site (see above), and symlink the skill.
3. `git -C ~/code/skill/paper_reader pull` to match the pinned commit.
4. Translate, then run `scripts/publish_to_site.sh`.

## Notes

- `source-pages/`, `assets/page-renders/`, `.venv/` are derived and git-ignored;
  they are not synced and can be regenerated.
- If a push is rejected because another device pushed first, run `git pull
  --rebase` then `git push` again.
