from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from DrissionPage import ChromiumOptions, ChromiumPage

from crawler.env_file import redact_dict, upsert_env_file


def _extract_csrf(cookie: str) -> str:
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith("csrfToken="):
            return part.split("=", 1)[1]
    return ""


def _capture_tokens(page: ChromiumPage) -> dict[str, str]:
    js = """
    (() => {
      const keys = ['token','refresh_token','token_expire_at','refresh_token_expire_at','device_id'];
      const out = {};
      for (const k of keys) out[k] = localStorage.getItem(k) || '';
      out.cookie = document.cookie || '';
      out.user_agent = navigator.userAgent || '';
      return JSON.stringify(out);
    })()
    """
    raw = page.run_js(js, as_expr=True)
    if not raw:
        raise RuntimeError("JS returned empty result")
    if isinstance(raw, str):
        data = json.loads(raw)
    else:
        # DrissionPage may return already-parsed objects in some cases
        data = raw

    token = str(data.get("token") or "").strip()
    refresh_token = str(data.get("refresh_token") or "").strip()
    cookie = str(data.get("cookie") or "").strip()
    user_agent = str(data.get("user_agent") or "").strip()
    csrf = _extract_csrf(cookie)

    return {
        "BIJI_BEARER_TOKEN": token,
        "BIJI_REFRESH_TOKEN": refresh_token,
        "BIJI_CSRF_TOKEN": csrf,
        "BIJI_COOKIE": f"csrfToken={csrf}" if csrf else "",
        "BIJI_USER_AGENT": user_agent,
    }


def capture_biji_env_to_file(*, url: str, env_path: Path) -> Mapping[str, str]:
    co = ChromiumOptions()
    co.set_argument("--start-maximized")
    co.auto_port(True)

    page: ChromiumPage | None = None
    try:
        page = ChromiumPage(addr_or_opts=co)
        page.get(url)

        input("d0ublecl1ck：请在浏览器里完成登录；完成后回到终端按回车继续…")

        captured = _capture_tokens(page)
        missing = [
            k
            for k, v in captured.items()
            if k in ("BIJI_BEARER_TOKEN", "BIJI_REFRESH_TOKEN") and not v
        ]
        if missing:
            raise RuntimeError(f"未取到关键值：{', '.join(missing)}（请确认已登录且页面已加载）")

        update = upsert_env_file(env_path, captured)
        print(f"已写入 {update.path}（changed={update.changed}）。")
        print("已捕获（脱敏）：", redact_dict(captured))
        return captured
    finally:
        if page is not None:
            try:
                page.quit(timeout=5, force=True, del_data=False)
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://www.biji.com/note")
    parser.add_argument("--env", default=".env")
    args = parser.parse_args()
    capture_biji_env_to_file(url=args.url, env_path=Path(args.env))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
