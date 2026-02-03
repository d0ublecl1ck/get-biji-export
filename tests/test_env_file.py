from pathlib import Path

from crawler.env_file import load_env_file, upsert_env_file


def test_upsert_env_file_creates(tmp_path: Path):
    env = tmp_path / ".env"
    result = upsert_env_file(env, {"A": "1", "B": "2"})
    assert result.changed is True
    text = env.read_text(encoding="utf-8")
    assert "A=1" in text
    assert "B=2" in text


def test_upsert_env_file_updates_existing(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("A=old\n# c\nB=keep\n", encoding="utf-8")
    result = upsert_env_file(env, {"A": "new"})
    assert result.changed is True
    text = env.read_text(encoding="utf-8")
    assert "A=new" in text
    assert "B=keep" in text


def test_load_env_file_sets_missing_only(tmp_path: Path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('A="1 2"\nB=3\n', encoding="utf-8")

    monkeypatch.delenv("A", raising=False)
    monkeypatch.setenv("B", "existing")

    result = load_env_file(env)
    assert result.changed is True
    assert result.path == env
    assert result.path.exists()
    import os

    assert result.changed is True
    assert os.environ["A"] == "1 2"
    assert os.environ["B"] == "existing"
