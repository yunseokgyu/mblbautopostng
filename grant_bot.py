import wp_utils
import requests
import xml.etree.ElementTree as ET
import datetime
import os
import json
import re
from bs4 import BeautifulSoup
from utils.grant_ai import analyze_grant_as_expert
# from bot_status import update_status # Removed invalid import
# Since bot_status.json is shared, let's redefine update_status here locally to avoid circular imports or just import if available. 
# Actually stock_bot.py had it locally. Let's make a shared util later. For now, local is fine.

STATUS_FILE = "bot_status_grant.json"

def update_status(state, message, progress=0.0):
    data = {
        "state": state,
        "message": message,
        "progress": progress,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Status save failed: {e}")

def fetch_google_news_rss(query):
    """
    Google News RSS를 통해 관련 키워드의 최신 뉴스를 가져옵니다.
    (API Key 필요 없음, Real Data)
    """
    base_url = "https://news.google.com/rss/search"
    params = {
        "q": query,
        "hl": "ko",
        "gl": "KR",
        "ceid": "KR:ko"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"[ERROR] RSS Fetch failed: {e}")
        return None

def parse_rss_items(xml_content, limit=3):
    """
    XML을 파싱하여 아이템 리스트를 반환합니다.
    """
    items = []
    try:
        root = ET.fromstring(xml_content)
        # channel -> item
        for item in root.findall('.//item')[:limit]:
            title = item.find('title').text if item.find('title') is not None else "No Title"
            link = item.find('link').text if item.find('link') is not None else ""
            description = item.find('description').text if item.find('description') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            
            # HTML 태그 제거 (간단하게)
            # description에 HTML이 섞여 있을 수 있음.
            
            items.append({
                "title": title,
                "link": link,
                "description": description,
                "pub_date": pub_date
            })
    except Exception as e:
        print(f"[ERROR] XML Parsing failed: {e}")
        
    return items


    return items

def fetch_exportvoucher_announcements(limit=5):
    """
    수출바우처 사업공고 크롤링
    URL: https://www.exportvoucher.com/portal/board/boardList?bbs_id=1
    """
    url = "https://www.exportvoucher.com/portal/board/boardList?bbs_id=1"
    items = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 목록 테이블
        rows = soup.select('tbody tr')
        if not rows:
            rows = soup.select('tr') # Fallback

        for row in rows[:limit]:
            # 제목
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
            
            # 링크 (onclick="goDetail('3524')")
            onclick = title_tag.get('onclick', '')
            link = ""
            match = re.search(r"goDetail\(['\"]?(\d+)['\"]?\)", onclick)
            if match:
                id_code = match.group(1)
                link = f"https://www.exportvoucher.com/portal/board/boardView?bbs_id=1&ntt_id={id_code}"
            
            # 날짜 (3번째 td)
            tds = row.find_all('td')
            date_text = tds[2].get_text(strip=True) if len(tds) > 2 else ""
            
            items.append({
                "title": title,
                "link": link,
                "description": title,
                "pub_date": date_text,
                "source_tag": "수출바우처"
            })
    except Exception as e:
        print(f"[ERROR] ExportVoucher Crawling failed: {e}")
    return items

def fetch_manufacturing_mssd(limit=5):
    """
    중소벤처기업부(제조혁신바우처 등) RSS 파싱
    URL: https://mss.go.kr/rss/smba/board/90.do
    """
    rss_url = "https://mss.go.kr/rss/smba/board/90.do"
    items = []
    try:
        import feedparser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # requests로 먼저 가져옴 (차단 방지)
        resp = requests.get(rss_url, headers=headers, timeout=10)
        
        feed = feedparser.parse(resp.content)
        
        # Feedparser가 못 찾으면 BS4로 시도
        entries = feed.entries
        if len(entries) == 0:
            soup = BeautifulSoup(resp.content, 'xml')
            xml_items = soup.find_all(['item', 'entry'])
            for x in xml_items[:limit]:
                 t = x.find('title')
                 l = x.find('link')
                 if t:
                     items.append({
                        "title": t.get_text(strip=True),
                        "link": l.get_text(strip=True) if l else "",
                        "description": t.get_text(strip=True),
                        "pub_date": "", 
                        "source_tag": "제조바우처(중기부)"
                     })
            return items # BS4 결과 반환
            
        for entry in entries[:limit]:
            items.append({
                "title": entry.title,
                "link": entry.link,
                "description": entry.description if 'description' in entry else entry.title,
                "pub_date": entry.published if 'published' in entry else "",
                "source_tag": "제조바우처(중기부)"
            })
    except Exception as e:
        print(f"[ERROR] Manufacturing RSS failed: {e}")
    return items

def fetch_sbiz24_announcements(limit=5):
    """
    소상공인24 (SPA) 크롤링 - 현재 API 엔드포인트 추정이 필요함.
    임시로 requests로 되는지 시도해보고 안되면 스킵.
    """
    # SPA라서 단순 requests로는 안될 확률 높음. 
    # 하지만 일단 플레이스홀더로 둠.
    print("[WARNING] 소상공인24는 SPA 구조라 현재 직접 크롤링이 어렵습니다. (API 분석 필요)")
    return []

def fetch_kstartup_announcements(limit=5):
    """
    K-Startup 사업공고(진행중) 페이지를 크롤링합니다.
    URL: https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do
    """
    url = "https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do"
    items = []
    
    try:
        # User-Agent 설정 (차단 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 공고 리스트 (div#bizPbancList > ul > li)
        list_container = soup.find('div', id='bizPbancList')
        if not list_container:
            print("[WARNING] K-Startup 리스트 컨테이너(div)를 찾지 못했습니다.")
            # 혹시 모르니 class로도 시도
            list_container = soup.find('ul', class_='board_list')
            
        if not list_container:
             # 최후의 수단: 전체에서 li.notice 찾기
             li_list = soup.find_all('li', class_='notice')
        else:
             li_list = list_container.find_all('li', class_='notice')
        
        for li in li_list[:limit]:
            # 1. 제목 & 링크 ID 추출
            title_tag = li.find('p', class_='tit')
            if not title_tag: 
                title_tag = li.find('a') # p가 없으면 a태그 자체가 제목일 수 있음
                
            title = title_tag.get_text(strip=True) if title_tag else "제목 없음"
            
            # 링크 (javascript:go_view(123456))
            link_tag = li.find('a', href=True)
            link = ""
            if link_tag:
                href = link_tag['href']
                # go_view( 숫자 ) 추출
                match = re.search(r"go_view\('?(\d+)'?\)", href)
                if match:
                    id_code = match.group(1)
                    # 상세 페이지 URL 조합
                    # pbancClssCd는 보통 중앙부처(PBC010)이나, 없어도 view 모드에서 작동하는지 확인 필요.
                    # 안전하게 param에 넣어서 이동
                    link = f"https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do?schM=view&pbancSn={id_code}"
            
            # 2. 날짜 추출 (span.list 안에 "등록일자 yyyy-mm-dd")
            date_text = ""
            bottom_div = li.find('div', class_='bottom')
            if bottom_div:
                spans = bottom_div.find_all('span', class_='list')
                for sp in spans:
                    txt = sp.get_text(strip=True)
                    if "등록일자" in txt:
                        # "등록일자 2024-01-01" -> "2024-01-01"
                        date_text = txt.replace("등록일자", "").strip()
                        break
            
            # 설명은 목록에 없으므로 제목과 동일하게 or 빈값
            
            items.append({
                "title": title,
                "link": link,
                "description": title, # K-Startup 목록에는 본문 요약이 없음
                "pub_date": date_text,
                "source_tag": "K-Startup"
            })
            
    except Exception as e:
        print(f"[ERROR] K-Startup Crawling failed: {e}")
        
    return items

def run_grant_job(dry_run=True, limit=None):
    """
    dry_run=True: 포스팅은 하지 않고 수집/분석만 수행 (로그 확인용)
    limit: 처리할 최대 공고 수 (None이면 전체)
    """
    print(f"[INFO] [Grant Bot] Started. (Dry Run: {dry_run}, Limit: {limit})")
    update_status("running", "[START] 지원사업 공고 수집 시작...", 0.1)
    
    config = load_config()
    grant_config = config.get('grant', {})
    categories = grant_config.get('categories', {})
    sources = grant_config.get('sources', [])
    
    total_published = 0
    total_found = 0
    
    # Merge items significantly or process one by one
    # Let's collect all items first to deduplicate based on link/title
    all_items = []
    
    # 0. 특수 크롤러 (Direct Crawling)
    crawlers_config = grant_config.get('crawlers', {'kstartup': True, 'export': True, 'mssd': True, 'sbiz': True})
    
    # K-Startup
    if crawlers_config.get('kstartup', True):
        update_status("running", "[CRAWL] K-Startup 공고 수집 중...", 0.15)
        print("\n[SOURCE] K-Startup")
        k_items = fetch_kstartup_announcements(limit=5)
        print(f"   -> {len(k_items)}개 발견")
        all_items.extend(k_items)

    # 수출바우처
    if crawlers_config.get('export', True):
        print("\n[SOURCE] 수출바우처 (ExportVoucher)")
        ex_items = fetch_exportvoucher_announcements(limit=5)
        print(f"   -> {len(ex_items)}개 발견")
        all_items.extend(ex_items)

    # 제조바우처 (중기부 RSS)
    if crawlers_config.get('mssd', True):
        print("\n[SOURCE] 제조바우처 (중기부 RSS)")
        ms_items = fetch_manufacturing_mssd(limit=5)
        print(f"   -> {len(ms_items)}개 발견")
        all_items.extend(ms_items)

    # 소상공인24
    if crawlers_config.get('sbiz', True):
        # sbiz = fetch_sbiz24_announcements() # 아직 미완성
        pass
    
    # 0-2. AI 스마트 수집 (사용자 정의 HTML 사이트)
    ai_sources = grant_config.get('ai_sources', [])
    if ai_sources:
        print("\n[SOURCE] AI 스마트 수집 (Beta)")
        from utils.grant_ai import extract_announcements_from_html
        
        for ai_url in ai_sources:
            update_status("running", f"[AI] {ai_url} 분석 중...", 0.3)
            print(f"   -> Analyzing: {ai_url}")
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                resp = requests.get(ai_url, headers=headers, timeout=15)
                if resp.status_code == 200:
                    extracted = extract_announcements_from_html(resp.text, base_url=ai_url)
                    print(f"      Found {len(extracted)} items (by Gemini)")
                    
                    for item in extracted:
                        # AI가 추출한 데이터를 key mapping
                        all_items.append({
                            "title": item.get('title'),
                            "link": item.get('link'),
                            "description": f"AI 수집: {item.get('title')}",
                            "pub_date": item.get('date', ''),
                            "source_tag": "AI수집"
                        })
                else:
                    print(f"      [Fail] Status {resp.status_code}")
            except Exception as e:
                print(f"      [Error] {e}")
    
    # 1. 키워드 검색 (Google News) - 사용자가 비활성화 요청함
    # if categories:
    #     cat_keys = list(categories.keys())
    #     for c_idx, (category_name, keywords) in enumerate(categories.items()):
    #         progress = 0.2 + (c_idx / len(cat_keys)) * 0.3
    #         update_status("running", f"[SEARCH] '{category_name}' 관련 공고 (Google News)", progress)
    #         
    #         if not keywords: continue
    #         query = " OR ".join(keywords)
    #         
    #         rss_xml = fetch_google_news_rss(query)
    #         if rss_xml:
    #             items = parse_rss_items(rss_xml, limit=3)
    #             for item in items:
    #                 item['source_tag'] = category_name 
    #                 all_items.append(item)

    # 2. 맞춤 RSS 소스
    if sources:
        update_status("running", "[RSS] 맞춤 소스 수집 중...", 0.5)
        for s_idx, source_url in enumerate(sources):
            rss_xml = fetch_custom_rss(source_url)
            if rss_xml:
                items = parse_rss_items(rss_xml, limit=5)
                for item in items:
                    item['source_tag'] = "맞춤공고"
                    all_items.append(item)
    
    # 중복 제거 (링크 기준)
    unique_items = {item['link']: item for item in all_items}.values()
    print(f"[INFO] 총 {len(unique_items)}개의 공고 수집됨.")
    
    # WP 최근 글 가져오기 (중복 방지용)
    recent_posts = wp_utils.get_recent_posts(limit=30)
    
    # 카테고리 ID 확보 ('government subsidies')
    cat_id = wp_utils.ensure_category("government subsidies")
    cat_ids = [cat_id] if cat_id else []

    target_items = []
    
    for item in unique_items:
        if limit and len(target_items) >= limit:
            break
            
        title = item['title']
        
        # 중복 체크
        is_duplicate = False
        # 1. WP 체크
        for p in recent_posts:
            # 제목의 일부가 겹치거나 링크(본문에 있을 수 있음) 체크는 어렵지만 제목으로 1차 필터
            # 비슷하면 스킵 (간단 매칭)
            if title[:len(title)//2] in p['title']: # 제목 앞 절반이 같으면 의심
                is_duplicate = True
                break
        
        if is_duplicate:
            print(f"[SKIP] 이미 발행된 공고(WP): {title}")
            continue
            
        target_items.append(item)
        
    print(f"[INFO] 분석 대상: {len(target_items)}개")
    update_status("running", f"[ANALYSIS] {len(target_items)}개 공고 분석 시작...", 0.6)

    count = 0
    total = len(target_items)
    
    for i, item in enumerate(target_items):
        process_grant_item(item, item.get('source_tag', '기타'), dry_run, cat_ids)
        update_status("running", f"[POSTING] {i+1}/{total} 처리 중...", 0.6 + (i/total)*0.4)

    update_status("idle", f"완료. (수집: {len(all_items)}, 최종: {len(target_items)})", 1.0)


def process_grant_item(item, category_tag, dry_run, cat_ids):
    """
    공통 아이템 처리 로직 (분석 -> 포스팅)
    """
    title = item['title']
    link = item['link']
    description = item['description']
    pub_date = item['pub_date']
    
    print(f"\n[Item] {title}")
    
    if dry_run:
        print("   -> [Dry Run] Posting skipped. (Analyzed internally)")
        # Dry Run이어도 분석 퀄리티 테스트를 위해 한번 찍어볼 수 있음
        # analysis = analyze_grant_as_expert(title, description, link)
        # print(analysis[:200] + "...")
        return

    # 전문가 분석
    expert_analysis = analyze_grant_as_expert(title, description, link)
    if "오류 발생" in expert_analysis:
        print("[SKIP] 분석 오류")
        return

    # 이미지 첨부 (무료 이미지 5개)
    images_html = ""
    try:
        from image_factory import fetch_free_images
        
        # 1. 제목으로 검색 시도
        search_query = title
        # 제목이 너무 길면 핵심 단어 추출이 어렵지만, Pexels는 긴 쿼리도 대충 처리함.
        # 정 안되면 'Startup' 같은걸로 Fallback
        
        img_urls = fetch_free_images(search_query, count=5)
        if not img_urls:
            print("   -> 제목 검색 실패, 'Startup' 키워드로 대체 검색")
            img_urls = fetch_free_images("Startup business team", count=5)
            
        if img_urls:
            print(f"   -> {len(img_urls)}개 이미지 준비됨 (Cloudinary Optimized)")
            
            # HTML 생성 (2열 그리드)
            if img_urls:
                images_html += '<div style="margin-top: 30px;"><h3>📷 관련 이미지</h3>'
                images_html += '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
                for u in img_urls:
                    images_html += f'<img src="{u}" style="width: 48%; height: auto; object-fit: cover; border-radius: 5px; margin-bottom: 10px;" loading="lazy">'
                images_html += '</div></div>'
                
    except Exception as e:
        print(f"   [Image Attachment Error] {e}")

    # 태그 붙여서 포스팅
    wp_title = f"[{category_tag}] {title} - 전문가 분석"
    
    wp_content = f"""
    <p><i>이 글은 정부지원금 데이터와 AI 전문가의 분석을 바탕으로 작성되었습니다.</i></p>
    <div style="background-color: #f6f8fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3>📢 공고 요약</h3>
        <ul>
            <li><strong>제목:</strong> {title}</li>
            <li><strong>카테고리:</strong> {category_tag}</li>
            <li><strong>발행일:</strong> {pub_date}</li>
        </ul>
        <p style="text-align: center; margin-top: 15px;">
            <a href="{link}" target="_blank" style="background-color: #2ea44f; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">👉 공식 공고문 보러가기</a>
        </p>
    </div>
    <hr>
    {expert_analysis}
    {images_html}
    <hr>
    <p style="color: #666; font-size: 0.9em;">※ 본 분석은 AI에 의해 작성되었으며, 정확한 내용은 반드시 공식 기관의 공고를 재확인하시기 바랍니다.</p>
    """
    
    res = wp_utils.post_article(wp_title, wp_content, category_ids=cat_ids)
    if res:
        print(f"[SUCCESS] Posted: {wp_title}")
    else:
        print(f"[FAILURE] Failed to post: {wp_title}")

def load_config():
    try:
        with open('bot_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Grant Bot')
    parser.add_argument('--post', action='store_true', help='Actually post to WordPress')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of posts')
    
    parser.add_argument('--loop', action='store_true', help='Run in infinite loop mode')
    
    args = parser.parse_args()
    
    if args.loop:
        print("[SYSTEM] Grant Bot Starting (Loop Mode)")
        import time
        while True:
            try:
                run_grant_job(dry_run=not args.post, limit=args.limit)
                print("[SYSTEM] Cycle finished. Sleeping for 6 hours...")
                update_status("idle", "[WAIT] 다음 사이클 대기 중 (6시간)", 1.0)
                time.sleep(6 * 3600)
            except KeyboardInterrupt:
                print("[SYSTEM] Bot stopped by user.")
                break
            except Exception as e:
                print(f"[CRITICAL ERROR] Bot crashed: {e}")
                update_status("error", f"[ERROR] 봇 크래시: {str(e)}", 0.0)
                print("[SYSTEM] Restarting in 60 seconds...")
                time.sleep(60)
    else:
        run_grant_job(dry_run=not args.post, limit=args.limit)
