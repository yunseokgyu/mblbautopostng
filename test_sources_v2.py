import requests
from bs4 import BeautifulSoup
import re
import feedparser

def fetch_exportvoucher_announcements(limit=5):
    url = "https://www.exportvoucher.com/portal/board/boardList?bbs_id=1"
    print(f"Testing ExportVoucher: {url}")
    items = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 목록 테이블
        rows = soup.select('tbody tr')
        print(f"Rows found: {len(rows)}")
        
        for row in rows[:limit]:
            title_tag = row.select_one('td.left a')
            if not title_tag:
                 # Fallback
                 links = row.find_all('a')
                 for l in links:
                     if 'goDetail' in l.get('onclick', ''):
                         title_tag = l
                         break
            
            if not title_tag: continue
            
            title = title_tag.get_text(strip=True)
            onclick = title_tag.get('onclick', '')
            link = ""
            # Regex to handle '123' or "123" or 123
            match = re.search(r"goDetail\(['\"]?(\d+)['\"]?\)", onclick)
            if match:
                id_code = match.group(1)
                link = f"https://www.exportvoucher.com/portal/board/boardView?bbs_id=1&ntt_id={id_code}"
            
            print(f" - Found: {title} | {link}")
            if not link: print(f"   (Onclick content: {onclick})") # Debug
            items.append(title)
            
    except Exception as e:
        print(f"[ERROR] ExportVoucher failed: {e}")
    return items

def fetch_manufacturing_mssd(limit=5):
    rss_url = "https://mss.go.kr/rss/smba/board/90.do"
    print(f"\nTesting Manufacturing RSS: {rss_url}")
    items = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = requests.get(rss_url, headers=headers, timeout=10)
        print(f"RSS Status: {resp.status_code}")
        
        # Check if it's really XML
        if not resp.text.strip().startswith("<?xml") and not "<rss" in resp.text:
            print("WARNING: Content does NOT look like XML/RSS.")
            print("Preview:", resp.text[:500])
        
        feed = feedparser.parse(resp.content)
        print(f"Entries found: {len(feed.entries)}")
        
        if len(feed.entries) == 0:
             print("feedparser found 0 entries. Trying BeautifulSoup...")
             # BS4 Fallback
             soup = BeautifulSoup(resp.content, 'xml') # or 'lxml-xml'
             items_xml = soup.find_all('item')
             print(f"BS4 found items: {len(items_xml)}")
             
             for item in items_xml[:limit]:
                 t = item.find('title').get_text(strip=True) if item.find('title') else "No Title"
                 l = item.find('link').get_text(strip=True) if item.find('link') else ""
                 print(f" - Found (BS4): {t} | {l}")
                 items.append(t)
        
        else:
            for entry in feed.entries[:limit]:
                print(f" - Found: {entry.title}")
                items.append(entry.title)
    except Exception as e:
        print(f"[ERROR] Manufacturing RSS failed: {e}")
    return items

if __name__ == "__main__":
    fetch_exportvoucher_announcements()
    fetch_manufacturing_mssd()
