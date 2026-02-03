from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from crawler.env_file import load_env_file


@dataclass(frozen=True)
class EnsureEnvResult:
    env_path: Path
    did_capture: bool


def has_biji_tokens() -> bool:
    return bool(os.getenv("BIJI_BEARER_TOKEN") or os.getenv("BIJI_REFRESH_TOKEN"))


def ensure_biji_env(
    *,
    env_path: Path = Path(".env"),
    url: str = "https://www.biji.com/note",
    capture_fn: Callable[[str, Path], None] | None = None,
) -> EnsureEnvResult:
    load_env_file(env_path)
    if has_biji_tokens():
        return EnsureEnvResult(env_path=env_path, did_capture=False)

    if capture_fn is None:
        from scripts.capture_biji_env import capture_biji_env_to_file

        def capture_fn(url: str, env_path: Path) -> None:
            capture_biji_env_to_file(url=url, env_path=env_path)

    capture_fn(url, env_path)
    load_env_file(env_path)
    if not has_biji_tokens():
        raise RuntimeError("已完成登录捕获，但环境中仍缺少 BIJI_BEARER_TOKEN/BIJI_REFRESH_TOKEN")

    return EnsureEnvResult(env_path=env_path, did_capture=True)

