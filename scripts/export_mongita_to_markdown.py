from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from crawler.markdown_export import MarkdownExportOptions, export_markdown_from_records
from crawler.mongita_io import open_mongita


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongita-dir", default="data/mongita")
    parser.add_argument("--db", default="biji")
    parser.add_argument("--notes", default="notes")
    parser.add_argument("--details", default="details")
    parser.add_argument("--misc", default="misc")
    parser.add_argument("--out", default="data/markdown")
    parser.add_argument(
        "--only-details",
        action="store_true",
        help="Only export notes that have details (usually note_type=link).",
    )
    args = parser.parse_args()

    cols = open_mongita(Path(args.mongita_dir), args.db, args.notes, args.details, args.misc)
    notes = list(cols.notes.find({}))

    details_by_note_id = {}
    for d in cols.details.find({}):
        nid = str(d.get("note_id") or "")
        if nid:
            details_by_note_id[nid] = d

    written = export_markdown_from_records(
        notes=notes,
        details_by_note_id=details_by_note_id,
        options=MarkdownExportOptions(out_dir=Path(args.out), only_with_details=args.only_details),
    )
    print(f"exported: {len(written)} files -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
