from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from mongita import MongitaClientDisk


@dataclass(frozen=True)
class MongitaCollections:
    notes: Any
    details: Any
    misc: Any


def open_mongita(dir_path: Path, db_name: str, notes: str, details: str, misc: str) -> MongitaCollections:
    dir_path.mkdir(parents=True, exist_ok=True)
    client = MongitaClientDisk(str(dir_path))
    db = client[db_name]
    return MongitaCollections(notes=db[notes], details=db[details], misc=db[misc])


def upsert_by_note_id(collection, *, note_id: str, doc: Mapping[str, Any], now: int | None = None) -> None:
    """
    Mongita doesn't support `$setOnInsert`, so we implement upsert with a
    find-then-update/insert flow.
    """
    now = int(time.time()) if now is None else int(now)
    existing = collection.find_one({"note_id": note_id})
    if existing is None:
        to_insert = dict(doc)
        to_insert.setdefault("_created_at", now)
        to_insert.setdefault("_ts", now)
        collection.insert_one(to_insert)
        return
    to_update = dict(doc)
    to_update.setdefault("_ts", now)
    collection.update_one({"note_id": note_id}, {"$set": to_update}, upsert=False)

