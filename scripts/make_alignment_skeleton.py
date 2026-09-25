#!/usr/bin/env python3
"""Create an alignment.json skeleton from the translated-block inventory.

This enforces the stable record shape (`id`, `section`, `type`, ids, `source`,
`translation`) so different models do not drift on structure. The model then fills
`source` with the real source text (canonical LaTeX for equations). Existing
`source`/`notes` values are preserved when re-running against an existing
alignment.json.

Usage:
    python scripts/make_alignment_skeleton.py --blocks translation-blocks.json \
        --output alignment.json
    python scripts/make_alignment_skeleton.py --blocks translation-blocks.json \
        --output alignment.json --merge
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def record_from_block(block: dict) -> dict:
    block_id = block["id"]
    record = {
        "id": block_id,
        "section": block.get("section", ""),
        "type": block.get("type", "paragraph"),
        "source_ids": [f"src-{block_id}"],
        "translation_ids": [block_id],
        "source": "",
        "translation": block.get("translation", ""),
        "notes": "",
    }
    for key in ("level", "table", "figure"):
        if key in block and block[key] is not None:
            record[key] = block[key]
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an alignment.json skeleton.")
    parser.add_argument("--blocks", required=True, help="Path to translation-blocks.json.")
    parser.add_argument("--output", required=True, help="Path to write alignment.json.")
    parser.add_argument("--merge", action="store_true",
                        help="Preserve source/notes from an existing alignment.json.")
    args = parser.parse_args()

    blocks = json.loads(Path(args.blocks).read_text(encoding="utf-8"))
    existing: dict[str, dict] = {}
    output = Path(args.output)
    if args.merge and output.exists():
        for record in json.loads(output.read_text(encoding="utf-8")):
            existing[record.get("id", "")] = record

    records = []
    for block in blocks:
        record = record_from_block(block)
        previous = existing.get(record["id"])
        if previous:
            if previous.get("source"):
                record["source"] = previous["source"]
            if previous.get("notes"):
                record["notes"] = previous["notes"]
        records.append(record)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")

    missing = sum(1 for record in records if record["type"] == "equation" and not record["source"])
    print(f"Wrote {len(records)} records to {output}")
    print(f"Equation records still needing source: {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
