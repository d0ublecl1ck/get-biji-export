import json
from pathlib import Path

from crawler.markdown_export import MarkdownExportOptions, export_markdown_from_records
from crawler.mongita_io import open_mongita, upsert_by_note_id


def test_migrate_like_jsonl_and_export_markdown(tmp_path: Path):
    # Prepare mongita
    cols = open_mongita(tmp_path / "mongita", "biji", "notes", "details", "misc")

    # Simulate old jsonl objects
    note = {
        "kind": "note",
        "note_id": "n1",
        "raw": {"note_type": "link", "title": "T", "tags": [{"name": "tag 1"}]},
    }
    detail = {
        "kind": "link_detail",
        "note_id": "n1",
        "title": "DT",
        "url": "https://example.com",
        "content": "Hello",
        "has_content": True,
        "raw": {"title": "DT", "url": "https://example.com", "content": "Hello", "has_content": True},
    }

    upsert_by_note_id(cols.notes, note_id="n1", doc=note)
    upsert_by_note_id(cols.details, note_id="n1", doc={"kind": "details", **detail})

    notes = list(cols.notes.find({}))
    details_by_note_id = {d["note_id"]: d for d in cols.details.find({})}

    out_dir = tmp_path / "md"
    written = export_markdown_from_records(
        notes=notes,
        details_by_note_id=details_by_note_id,
        options=MarkdownExportOptions(out_dir=out_dir, only_with_details=True),
    )
    assert len(written) == 1
    text = written[0].read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert 'title: "DT"' in text
    assert '  - "tag_1"' in text
    assert "https://example.com" in text
    assert "Hello" in text
