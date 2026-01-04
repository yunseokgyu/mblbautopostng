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
        # print("HTML Preview:", response.text[:500]) # Debug
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 목록 테이블 (Select all trs in tbody)
        rows = soup.select('tbody tr')
        print(f"Rows found: {len(rows)}")
        
        if len(rows) == 0:
            print("Trying alternative selector...")
            rows = soup.select('tr')
            print(f"Total TRs: {len(rows)}")

        for row in rows[:limit]:
            # Try finding title in td.left or just any a tag
            title_tag = row.select_one('td.left a')
            if not title_tag:
                 # Fallback: find any 'a' with goDetail
                 links = row.find_all('a')
                 for l in links:
                     if 'goDetail' in l.get('onclick', ''):
                         title_tag = l
                         break
            
            if not title_tag:
                # print(f"Skipping row: {row.get_text(strip=True)[:20]}")
                continue
            
            title = title_tag.get_text(strip=True)
            onclick = title_tag.get('onclick', '')
            link = ""
            match = re.search(r"goDetail\('(\d+)'\)", onclick)
            if match:
                id_code = match.group(1)
                link = f"https://www.exportvoucher.com/portal/board/boardView?bbs_id=1&ntt_id={id_code}"
            
            print(f" - Found: {title} | {link}")
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
        # Use requests first
        resp = requests.get(rss_url, headers=headers, timeout=10)
        print(f"RSS Status: {resp.status_code}")
        
        feed = feedparser.parse(resp.content)
        print(f"Entries found: {len(feed.entries)}")
        
        if len(feed.entries) == 0 and resp.status_code == 200:
             print("RSS Content Preview:", resp.text[:200])

        for entry in feed.entries[:limit]:
            print(f" - Found: {entry.title}")
            items.append(entry.title)
    except Exception as e:
        print(f"[ERROR] Manufacturing RSS failed: {e}")
    return items
