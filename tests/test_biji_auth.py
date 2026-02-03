from crawler.biji_auth import parse_refresh_response


def test_parse_refresh_response_minimal():
    payload = {
        "h": {"c": 0, "e": ""},
        "c": {
            "token": {
                "token": "header.payload.signature",
                "token_expire_at": 123,
                "refresh_token": "rt",
                "refresh_token_expire_at": 456,
            }
        },
    }
    bundle = parse_refresh_response(payload)
    assert bundle.access_token == "header.payload.signature"
    assert bundle.access_token_expire_at == 123
    assert bundle.refresh_token == "rt"
    assert bundle.refresh_token_expire_at == 456


def test_decode_jwt_exp():
    # header={"alg":"none"}, payload={"exp": 123}
    token = "eyJhbGciOiJub25lIn0.eyJleHAiOjEyM30."
    from crawler.biji_auth import decode_jwt_exp

    assert decode_jwt_exp(token) == 123
