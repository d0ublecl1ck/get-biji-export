from __future__ import annotations

import time
import base64
import json
from dataclasses import dataclass
from typing import Any, Mapping

import requests


@dataclass(frozen=True)
class TokenBundle:
    access_token: str
    access_token_expire_at: int | None
    refresh_token: str | None
    refresh_token_expire_at: int | None

    def needs_refresh(self, *, refresh_before_seconds: int = 300) -> bool:
        if not self.access_token_expire_at:
            return False
        now = int(time.time())
        return now >= (int(self.access_token_expire_at) - int(refresh_before_seconds))


def decode_jwt_exp(token: str) -> int | None:
    """
    Decode JWT payload (no verification) and return exp if present.
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1].replace("-", "+").replace("_", "/")
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.b64decode(payload_b64).decode("utf-8"))
        exp = payload.get("exp")
        return int(exp) if exp is not None else None
    except Exception:
        return None


def mask_secret(value: str, *, head: int = 12, tail: int = 6) -> str:
    if not value:
        return ""
    if len(value) <= head + tail + 1:
        return value[:2] + "…"
    return f"{value[:head]}…{value[-tail:]}"


def parse_refresh_response(payload: Mapping[str, Any]) -> TokenBundle:
    header = payload.get("h") or {}
    if header.get("c") not in (0, "0", None):
        raise ValueError(f"API error: h.c={header.get('c')} h.e={header.get('e')}")

    content = payload.get("c") or {}
    token_obj = content.get("token") or {}
    token_str = token_obj.get("token") or ""
    if not token_str:
        raise ValueError("Missing token in refresh response")

    return TokenBundle(
        access_token=token_str,
        access_token_expire_at=token_obj.get("token_expire_at"),
        refresh_token=token_obj.get("refresh_token"),
        refresh_token_expire_at=token_obj.get("refresh_token_expire_at"),
    )


def refresh_access_token(
    *,
    refresh_token: str,
    access_token: str | None = None,
    csrf_token: str | None = None,
    cookie: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
    timeout_seconds: int = 30,
) -> TokenBundle:
    headers: dict[str, str] = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }
    if user_agent:
        headers["User-Agent"] = user_agent
    if request_id:
        headers["X-Request-ID"] = request_id
    if csrf_token:
        headers["Xi-Csrf-Token"] = csrf_token
    if cookie:
        headers["Cookie"] = cookie
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    resp = requests.post(
        "https://notes-api.biji.com/account/v2/web/user/auth/refresh",
        headers=headers,
        json={"refresh_token": refresh_token},
        timeout=timeout_seconds,
    )
    resp.raise_for_status()
    return parse_refresh_response(resp.json())
