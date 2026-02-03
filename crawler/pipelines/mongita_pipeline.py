from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from feapder.pipelines import BasePipeline
from mongita import MongitaClientDisk


@dataclass(frozen=True)
class MongitaConfig:
    dir_path: Path
    db_name: str
    notes_collection: str
    link_details_collection: str
    misc_collection: str


def _default_config() -> MongitaConfig:
    return MongitaConfig(
        dir_path=Path(os.getenv("BIJI_MONGITA_DIR", "data/mongita")),
        db_name=os.getenv("BIJI_MONGITA_DB", "biji"),
        notes_collection=os.getenv("BIJI_MONGITA_NOTES_COLLECTION", "notes"),
        link_details_collection=os.getenv(
            "BIJI_MONGITA_DETAILS_COLLECTION", "details"
        ),
        misc_collection=os.getenv("BIJI_MONGITA_MISC_COLLECTION", "misc"),
    )


class MongitaPipeline(BasePipeline):
    """
    Store all exported items in a local Mongita (embedded, MongoDB-like) database.

    - `kind="note"` -> notes collection (upsert by note_id)
    - `kind="link_detail"` -> link_details collection (upsert by note_id)
    - else -> misc collection (insert)
    """

    def __init__(self, config: MongitaConfig | None = None):
        self._config = config or _default_config()
        self._config.dir_path.mkdir(parents=True, exist_ok=True)
        self._client = MongitaClientDisk(str(self._config.dir_path))
        db = self._client[self._config.db_name]
        self._notes = db[self._config.notes_collection]
        self._link_details = db[self._config.link_details_collection]
        self._misc = db[self._config.misc_collection]

    def save_items(self, table, items: List[Dict]) -> bool:
        now = int(time.time())
        for item in items:
            kind = item.get("kind")
            note_id = item.get("note_id")

            doc: Dict[str, Any] = dict(item)
            doc.setdefault("_ts", now)

            if kind == "note" and note_id:
                self._upsert(self._notes, {"note_id": note_id}, doc, now)
                continue

            if kind == "link_detail" and note_id:
                self._upsert(self._link_details, {"note_id": note_id}, doc, now)
                continue

            self._misc.insert_one(doc)
        return True

    @staticmethod
    def _upsert(collection, query: Dict[str, Any], doc: Dict[str, Any], now: int) -> None:
        """
        Mongita currently doesn't support `$setOnInsert`, so we do a simple
        find-then-update/insert flow.
        """
        existing = collection.find_one(query)
        if existing is None:
            doc = dict(doc)
            doc.setdefault("_created_at", now)
            collection.insert_one(doc)
            return
        collection.update_one(query, {"$set": doc}, upsert=False)
