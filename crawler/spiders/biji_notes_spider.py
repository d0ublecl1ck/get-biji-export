from __future__ import annotations

import os
import time

import feapder.setting as setting
from feapder import AirSpider
from feapder.network.item import Item
from feapder.network.request import Request
from feapder.utils.log import log

from crawler.biji_notes_logic import parse_notes_page
from crawler.biji_auth import TokenBundle, decode_jwt_exp, refresh_access_token
from crawler.biji_detail_logic import parse_link_detail


class BijiNotesSpider(AirSpider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_agent = os.getenv(
            "BIJI_USER_AGENT",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        )

        bearer = os.getenv("BIJI_BEARER_TOKEN", "").strip()
        refresh_token = os.getenv("BIJI_REFRESH_TOKEN", "").strip()
        csrf_token = os.getenv("BIJI_CSRF_TOKEN", "").strip() or None
        cookie = os.getenv("BIJI_COOKIE", "").strip() or None

        bearer_exp = decode_jwt_exp(bearer) if bearer else None

        if refresh_token:
            # Prefer ensuring a fresh token upfront when refresh_token exists.
            if (not bearer) or (bearer_exp is not None and int(time.time()) >= bearer_exp - 300):
                self._token_bundle = refresh_access_token(
                    refresh_token=refresh_token,
                    access_token=bearer or None,
                    csrf_token=csrf_token,
                    cookie=cookie,
                    user_agent=self._user_agent,
                    request_id=str(int(time.time() * 1000)),
                )
            else:
                self._token_bundle = TokenBundle(
                    access_token=bearer,
                    access_token_expire_at=bearer_exp,
                    refresh_token=refresh_token,
                    refresh_token_expire_at=None,
                )
        elif bearer:
            self._token_bundle = TokenBundle(
                access_token=bearer,
                access_token_expire_at=bearer_exp,
                refresh_token=None,
                refresh_token_expire_at=None,
            )
        else:
            self._token_bundle = refresh_access_token(
                refresh_token=refresh_token,
                access_token=None,
                csrf_token=csrf_token,
                cookie=cookie,
                user_agent=self._user_agent,
                request_id=str(int(time.time() * 1000)),
            )
            # (unreachable)

        self._csrf_token = csrf_token
        self._cookie = cookie

        self._limit = int(os.getenv("BIJI_LIMIT", "100"))
        self._sort = os.getenv("BIJI_SORT", "create_desc")
        self._since_id = os.getenv("BIJI_SINCE_ID", "")
        self._fetch_detail = os.getenv("BIJI_FETCH_DETAIL", "1").strip() not in ("0", "false", "False")

    def start_requests(self):
        yield self._make_notes_request(self._since_id)

    def _ensure_access_token(self) -> str:
        bundle = self._token_bundle
        if not bundle.refresh_token and bundle.access_token_expire_at and bundle.needs_refresh(refresh_before_seconds=0):
            raise RuntimeError("Access token expired and no refresh token; please re-login to refresh env.")

        if bundle.refresh_token and bundle.needs_refresh():
            try:
                self._token_bundle = refresh_access_token(
                    refresh_token=bundle.refresh_token,
                    access_token=bundle.access_token,
                    csrf_token=self._csrf_token,
                    cookie=self._cookie,
                    user_agent=self._user_agent,
                    request_id=str(int(time.time() * 1000)),
                )
            except Exception:
                self._token_bundle = refresh_access_token(
                    refresh_token=bundle.refresh_token,
                    access_token=None,
                    csrf_token=self._csrf_token,
                    cookie=self._cookie,
                    user_agent=self._user_agent,
                    request_id=str(int(time.time() * 1000)),
                )
        return self._token_bundle.access_token

    def _make_notes_request(self, since_id: str, *, auth_retry: bool = False):
        token = self._ensure_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": self._user_agent,
            "X-Request-ID": str(int(time.time() * 1000)),
        }
        if self._csrf_token:
            headers["Xi-Csrf-Token"] = self._csrf_token
        if auth_retry:
            headers["X-Auth-Retry"] = "1"
        return Request(
            "https://get-notes.luojilab.com/voicenotes/web/notes",
            headers=headers,
            params={"limit": str(self._limit), "since_id": since_id, "sort": self._sort},
            filter_repeat=False,
        )

    def _make_link_detail_request(self, note_id: str):
        token = self._ensure_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": self._user_agent,
            "X-Request-ID": str(int(time.time() * 1000)),
        }
        if self._csrf_token:
            headers["Xi-Csrf-Token"] = self._csrf_token
        return Request(
            f"https://get-notes.luojilab.com/voicenotes/web/notes/{note_id}/links/detail",
            headers=headers,
            callback="parse_link_detail",
            filter_repeat=False,
        )

    def parse(self, request, response):
        payload = None
        try:
            payload = response.json
        except Exception:
            payload = None

        if response.status_code == 403 or (isinstance(payload, dict) and payload.get("message") == "LoginRequired"):
            since_id = ""
            try:
                since_id = (getattr(request, "params", None) or {}).get("since_id", "")  # type: ignore[union-attr]
            except Exception:
                since_id = ""

            log.error(
                "notes page rejected: status=%s since_id=%s body=%s",
                response.status_code,
                since_id,
                (response.text or "")[:200],
            )

            if self._token_bundle.refresh_token and not (getattr(request, "headers", {}) or {}).get("X-Auth-Retry"):
                log.info("attempting token refresh and retry notes page once...")
                self._token_bundle = refresh_access_token(
                    refresh_token=self._token_bundle.refresh_token,
                    access_token=self._token_bundle.access_token,
                    csrf_token=self._csrf_token,
                    cookie=self._cookie,
                    user_agent=self._user_agent,
                    request_id=str(int(time.time() * 1000)),
                )
                yield self._make_notes_request(since_id, auth_retry=True)
            return

        if not isinstance(payload, dict) or "c" not in payload:
            log.error(
                "notes page unexpected response: status=%s body=%s",
                response.status_code,
                (response.text or "")[:200],
            )
            return

        page = parse_notes_page(payload, limit=self._limit)

        since_id = ""
        try:
            since_id = (getattr(request, "params", None) or {}).get("since_id", "")  # type: ignore[union-attr]
        except Exception:
            since_id = ""

        log.info(
            "notes page fetched: count=%s limit=%s since_id=%s next_since_id=%s should_continue=%s",
            len(page.notes),
            self._limit,
            since_id,
            page.next_since_id,
            page.should_continue,
        )

        link_count = 0
        for note in page.notes:
            note_id = note.get("id") or note.get("note_id")
            yield Item(kind="note", note_id=note_id, raw=note)

            if self._fetch_detail and note_id and note.get("note_type") == "link":
                link_count += 1
                yield self._make_link_detail_request(str(note_id))

        if self._fetch_detail:
            log.info("notes page detail scheduled: link_notes=%s", link_count)

        if page.should_continue:
            yield self._make_notes_request(page.next_since_id or "")

    def parse_link_detail(self, request, response):
        note_id = ""
        try:
            note_id = request.url.split("/voicenotes/web/notes/", 1)[1].split("/", 1)[0]
        except Exception:
            note_id = ""

        detail = parse_link_detail(response.json)
        yield Item(
            kind="link_detail",
            note_id=note_id,
            title=detail.title,
            web_title=detail.web_title,
            url=detail.url,
            has_content=detail.has_content,
            raw=detail.raw,
        )


if __name__ == "__main__":
    setting.ITEM_PIPELINES = ["crawler.pipelines.notes_jsonl_pipeline.NotesJsonlPipeline"]
    BijiNotesSpider().start()
