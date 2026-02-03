from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

from feapder.pipelines import BasePipeline


class NotesJsonlPipeline(BasePipeline):
    def __init__(self):
        self.output_path = Path(os.getenv("BIJI_EXPORT_PATH", "data/notes.jsonl"))
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def save_items(self, table, items: List[Dict]) -> bool:
        with self.output_path.open("a", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        return True

