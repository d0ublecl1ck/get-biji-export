from pathlib import Path

from mongita import MongitaClientDisk

from crawler.pipelines.mongita_pipeline import MongitaConfig, MongitaPipeline


def test_mongita_pipeline_writes_two_collections(tmp_path: Path):
    config = MongitaConfig(
        dir_path=tmp_path / "mongita",
        db_name="biji",
        notes_collection="notes",
        link_details_collection="details",
        misc_collection="misc",
    )
    pipe = MongitaPipeline(config=config)

    pipe.save_items(
        "ignored",
        [
            {"kind": "note", "note_id": "n1", "raw": {"id": "n1"}},
            {"kind": "link_detail", "note_id": "n1", "title": "t"},
            {"kind": "other", "x": 1},
        ],
    )

    client = MongitaClientDisk(str(config.dir_path))
    db = client[config.db_name]
    assert db[config.notes_collection].count_documents({}) == 1
    assert db[config.link_details_collection].count_documents({}) == 1
    assert db[config.misc_collection].count_documents({}) == 1
