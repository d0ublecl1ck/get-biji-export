import os
from pathlib import Path

import pytest

from crawler.bootstrap_biji_env import ensure_biji_env
from crawler.env_file import upsert_env_file


def test_ensure_biji_env_no_capture_when_already_present(monkeypatch, tmp_path: Path):
    env_path = tmp_path / ".env"
    monkeypatch.setenv("BIJI_BEARER_TOKEN", "t")

    called = {"n": 0}

    def capture(url: str, path: Path) -> None:
        called["n"] += 1

    result = ensure_biji_env(env_path=env_path, url="x", capture_fn=capture)
    assert result.did_capture is False
    assert called["n"] == 0


def test_ensure_biji_env_calls_capture_and_loads(tmp_path: Path, monkeypatch):
    env_path = tmp_path / ".env"
    monkeypatch.delenv("BIJI_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("BIJI_REFRESH_TOKEN", raising=False)

    def capture(url: str, path: Path) -> None:
        upsert_env_file(path, {"BIJI_REFRESH_TOKEN": "rt"})

    result = ensure_biji_env(env_path=env_path, url="x", capture_fn=capture)
    assert result.did_capture is True
    assert os.getenv("BIJI_REFRESH_TOKEN") == "rt"


def test_ensure_biji_env_raises_if_capture_did_not_write(tmp_path: Path, monkeypatch):
    env_path = tmp_path / ".env"
    monkeypatch.delenv("BIJI_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("BIJI_REFRESH_TOKEN", raising=False)

    def capture(url: str, path: Path) -> None:
        pass

    with pytest.raises(RuntimeError):
        ensure_biji_env(env_path=env_path, url="x", capture_fn=capture)

