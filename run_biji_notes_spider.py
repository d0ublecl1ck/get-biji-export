from pathlib import Path

import feapder.setting as setting

from crawler.spiders.biji_notes_spider import BijiNotesSpider
from crawler.bootstrap_biji_env import ensure_biji_env


if __name__ == "__main__":
    ensure_biji_env(env_path=Path(".env"), url="https://www.biji.com/note")
    setting.ITEM_PIPELINES = ["crawler.pipelines.mongita_pipeline.MongitaPipeline"]
    BijiNotesSpider().start()
