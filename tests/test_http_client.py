import requests

from src.utilities import http_client


def test_fetch_json_retries_common_local_ports(monkeypatch):
    calls = []

    def fake_get(url, timeout=15, headers=None):
        calls.append(url)
        if url.endswith(":8000/api/financial-markets/summary"):
            raise requests.ConnectionError("port busy")

        class Response:
            def __init__(self):
                self.headers = {"content-type": "application/json"}
                self.text = '{"ok": true}'

            def raise_for_status(self):
                return None

            def json(self):
                return {"ok": True}

        return Response()

    monkeypatch.setattr(http_client.requests, "get", fake_get)

    response = http_client.fetch_json("http://127.0.0.1:8000/api/financial-markets/summary")

    assert response == {"ok": True}
    assert calls[0].endswith(":8000/api/financial-markets/summary")
    assert calls[1].endswith(":8001/api/financial-markets/summary")
