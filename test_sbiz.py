import requests
from bs4 import BeautifulSoup

def test_sbiz():
    url = "https://www.sbiz24.kr/"
    print(f"Testing {url}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print("Preview:")
        print(resp.text[:500])
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Try to find the list
        # Selector from browser agent: tbody tr
        rows = soup.select('tbody tr')
        print(f"Rows found: {len(rows)}")
    except Exception as e:
        print(f"Error: {e}")

test_sbiz()
