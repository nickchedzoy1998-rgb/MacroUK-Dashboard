import requests


def extract(url):
    """Hits the API URL and returns parsed JSON response."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        raise ConnectionError(f'Extract failure: {e}')
