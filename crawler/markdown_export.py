from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


def _safe_filename(name: str, *, max_len: int = 120) -> str:
    name = name.strip()
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        return "untitled"
    return name[:max_len].rstrip()


@dataclass(frozen=True)
class MarkdownExportOptions:
    out_dir: Path
    only_with_details: bool = True


def _normalize_tag(tag: str) -> str:
    tag = str(tag).strip()
    tag = re.sub(r"\s+", "_", tag)
    return tag


def _yaml_escape(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def _yaml_bool(value: bool) -> str:
    return "true" if value else "false"


def _get_detail_content(detail: Mapping[str, Any]) -> str:
    raw = detail.get("raw") or {}
    if isinstance(raw, dict) and raw.get("content"):
        return str(raw.get("content") or "")
    if detail.get("content"):
        return str(detail.get("content") or "")
    return ""


def _get_note_content(note: Mapping[str, Any]) -> str:
    raw = note.get("raw") or {}
    if not isinstance(raw, dict):
        return ""

    for k in ("content", "body_text"):
        v = raw.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()

    jc = raw.get("json_content")
    if isinstance(jc, str) and jc.strip():
        return jc.strip()
    return ""


def _extract_audio_meta(note: Mapping[str, Any]) -> tuple[str, int | None]:
    raw = note.get("raw") or {}
    if not isinstance(raw, dict):
        return "", None
    attachments = raw.get("attachments") or []
    if not isinstance(attachments, list):
        return "", None
    for a in attachments:
        if not isinstance(a, dict):
            continue
        if a.get("type") == "audio":
            return str(a.get("url") or ""), a.get("duration")
    return "", None


def render_link_markdown(*, note: Mapping[str, Any], detail: Mapping[str, Any] | None) -> str:
    note_id = str(note.get("note_id") or "")
    raw_note = note.get("raw") or {}
    note_type = str(raw_note.get("note_type") or "")
    created_at = str(raw_note.get("created_at") or "")
    updated_at = str(raw_note.get("updated_at") or "")

    title = ""
    url = ""
    web_title = ""
    content = ""
    has_content = False
    if detail:
        title = str(detail.get("title") or "")
        url = str(detail.get("url") or "")
        web_title = str(detail.get("web_title") or "")
        content = _get_detail_content(detail)
        has_content = bool(detail.get("has_content")) if "has_content" in detail else bool(content)
    else:
        content = _get_note_content(note)
        has_content = bool(content)

    if not title:
        title = str(raw_note.get("title") or raw_note.get("web_title") or note_id or "Untitled")
    if not web_title:
        web_title = str(raw_note.get("web_title") or "")

    tags = raw_note.get("tags") or []
    tag_names = [t.get("name") for t in tags if isinstance(t, dict) and t.get("name")]
    tag_names = [_normalize_tag(t) for t in tag_names if _normalize_tag(t)]

    lines: list[str] = []

    exported_at = int(time.time())
    lines.append("---")
    lines.append(f'title: {_yaml_escape(title)}')
    if web_title:
        lines.append(f'web_title: {_yaml_escape(web_title)}')
    if note_id:
        lines.append(f'note_id: {_yaml_escape(note_id)}')
    if note_type:
        lines.append(f'note_type: {_yaml_escape(note_type)}')
    if url:
        lines.append(f'url: {_yaml_escape(url)}')
    if created_at:
        lines.append(f'created_at: {_yaml_escape(created_at)}')
    if updated_at:
        lines.append(f'updated_at: {_yaml_escape(updated_at)}')
    lines.append(f"has_content: {_yaml_bool(has_content)}")
    lines.append(f"exported_at: {exported_at}")
    if tag_names:
        lines.append("tags:")
        for t in tag_names:
            lines.append(f"  - {_yaml_escape(str(t))}")

    if note_type == "audio":
        audio_url, duration = _extract_audio_meta(note)
        if audio_url:
            lines.append(f'audio_url: {_yaml_escape(audio_url)}')
        if duration is not None:
            try:
                lines.append(f"audio_duration_ms: {int(duration)}")
            except Exception:
                pass

    lines.append("---")
    lines.append("")
    if content:
        if content.lstrip().startswith("{") and content.rstrip().endswith("}"):
            lines.append("```json")
            lines.append(content)
            lines.append("```")
        else:
            lines.append(content)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def export_markdown_from_records(
    *,
    notes: list[Mapping[str, Any]],
    details_by_note_id: Mapping[str, Mapping[str, Any]],
    options: MarkdownExportOptions,
) -> list[Path]:
    options.out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for note in notes:
        note_id = str(note.get("note_id") or "")
        detail = details_by_note_id.get(note_id)
        if options.only_with_details and not detail:
            continue

        raw_note = note.get("raw") or {}
        title = str((detail or {}).get("title") or raw_note.get("title") or note_id or "Untitled")
        base = _safe_filename(title) or "untitled"
        path = options.out_dir / f"{base}.md"
        if path.exists() and note_id:
            # Avoid overwriting when multiple notes share the same title.
            path = options.out_dir / f"{base} - {note_id}.md"
        path.write_text(render_link_markdown(note=note, detail=detail), encoding="utf-8")
        written.append(path)

    return written
