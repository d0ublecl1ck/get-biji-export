from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class LinkDetail:
    title: str
    web_title: str
    content: str
    url: str
    has_content: bool
    raw: Mapping[str, Any]


def parse_link_detail(payload: Mapping[str, Any]) -> LinkDetail:
    header = payload.get("h") or {}
    if header.get("c") not in (0, "0", None):
        raise ValueError(f"API error: h.c={header.get('c')} h.e={header.get('e')}")

    content = payload.get("c") or {}
    if not isinstance(content, dict):
        raise TypeError("payload.c must be an object")

    return LinkDetail(
        title=str(content.get("title") or ""),
        web_title=str(content.get("web_title") or ""),
        content=str(content.get("content") or ""),
        url=str(content.get("url") or ""),
        has_content=bool(content.get("has_content")),
        raw=content,
    )

