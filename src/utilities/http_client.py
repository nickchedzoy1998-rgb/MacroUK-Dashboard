import requests
from requests.exceptions import JSONDecodeError


def _request(url, *, headers=None, timeout=15):
    return requests.get(url, headers=headers, timeout=timeout)


def fetch_json(url, user_agent=False):
    """Hits the API URL and returns parsed JSON response."""
    if user_agent is False:
        urls_to_try = [url]
        if url.startswith("http://127.0.0.1:8000"):
            urls_to_try.append(url.replace(":8000", ":8001", 1))
        elif url.startswith("http://127.0.0.1:8001"):
            urls_to_try.append(url.replace(":8001", ":8000", 1))

        last_error = None
        for candidate in urls_to_try:
            try:
                response = _request(candidate)
                response.raise_for_status()
                return response.json()
            except JSONDecodeError as e:
                content_type = response.headers.get("content-type", "unknown")
                body_preview = response.text[:120].replace("\n", " ").strip()
                raise ConnectionError(
                    f"Extract failure: non-JSON response from {candidate} "
                    f"(content-type: {content_type}, body: {body_preview!r})"
                ) from e
            except Exception as e:
                last_error = e

        raise ConnectionError(f"Extract failure: {last_error}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
    }

    try:
        response = _request(url, headers=headers)
        response.raise_for_status()
        return response.url

    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"Extract failure: {e}")
