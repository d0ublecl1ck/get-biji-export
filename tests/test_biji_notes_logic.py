from crawler.biji_notes_logic import parse_notes_page


def _payload_with_ids(ids):
    return {"h": {"c": 0, "e": ""}, "c": {"list": [{"id": i} for i in ids]}}


def test_parse_notes_page_continue_when_len_eq_limit():
    page = parse_notes_page(_payload_with_ids(["a", "b", "c"]), limit=3)
    assert page.should_continue is True
    assert page.next_since_id == "c"


def test_parse_notes_page_stop_when_len_lt_limit():
    page = parse_notes_page(_payload_with_ids(["a", "b"]), limit=3)
    assert page.should_continue is False
    assert page.next_since_id == "b"


def test_parse_notes_page_stop_when_empty():
    page = parse_notes_page(_payload_with_ids([]), limit=100)
    assert page.should_continue is False
    assert page.next_since_id is None

