from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class NotesPage:
    notes: Sequence[Mapping[str, Any]]
    next_since_id: str | None
    should_continue: bool


def parse_notes_page(payload: Mapping[str, Any], *, limit: int) -> NotesPage:
    header = payload.get("h") or {}
    if header.get("c") not in (0, "0", None):
        raise ValueError(f"API error: h.c={header.get('c')} h.e={header.get('e')}")

    content = payload.get("c") or {}
    notes = content.get("list") or []
    if not isinstance(notes, list):
        raise TypeError("payload.c.list must be a list")

    if notes:
        last = notes[-1]
        next_since_id = last.get("id") or last.get("note_id")
    else:
        next_since_id = None

    should_continue = len(notes) >= limit and next_since_id is not None
    return NotesPage(notes=notes, next_since_id=next_since_id, should_continue=should_continue)

