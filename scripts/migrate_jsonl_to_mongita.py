from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from crawler.mongita_io import open_mongita, upsert_by_note_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", default="data/notes.jsonl")
    parser.add_argument("--mongita-dir", default="data/mongita")
    parser.add_argument("--db", default="biji")
    parser.add_argument("--notes", default="notes")
    parser.add_argument("--details", default="details")
    parser.add_argument("--misc", default="misc")
    args = parser.parse_args()

    jsonl_path = Path(args.jsonl)
    if not jsonl_path.exists():
        raise SystemExit(f"jsonl not found: {jsonl_path}")

    cols = open_mongita(Path(args.mongita_dir), args.db, args.notes, args.details, args.misc)

    n_notes = 0
    n_details = 0
    n_misc = 0

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            kind = obj.get("kind")
            note_id = obj.get("note_id")

            if kind == "note" and note_id:
                upsert_by_note_id(cols.notes, note_id=str(note_id), doc=obj)
                n_notes += 1
            elif kind == "link_detail" and note_id:
                obj = dict(obj)
                obj["kind"] = "details"
                upsert_by_note_id(cols.details, note_id=str(note_id), doc=obj)
                n_details += 1
            else:
                cols.misc.insert_one(obj)
                n_misc += 1

    print(f"migrated: notes={n_notes} details={n_details} misc={n_misc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
