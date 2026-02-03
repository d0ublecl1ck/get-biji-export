from crawler.biji_detail_logic import parse_link_detail


def test_parse_link_detail_ok():
    payload = {
        "h": {"c": 0, "e": ""},
        "c": {
            "title": "t",
            "web_title": "wt",
            "content": "c",
            "url": "u",
            "has_content": True,
        },
    }
    detail = parse_link_detail(payload)
    assert detail.title == "t"
    assert detail.web_title == "wt"
    assert detail.content == "c"
    assert detail.url == "u"
    assert detail.has_content is True

