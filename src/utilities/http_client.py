import requests


def fetch_json(url, user_agent=False):
    """Hits the API URL and returns parsed JSON response."""
    if user_agent == False:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            raise ConnectionError(f'Extract failure: {e}')
    
    else:
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.url
        
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"Extract failure: {e}")