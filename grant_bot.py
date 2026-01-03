import wp_utils
import requests
import xml.etree.ElementTree as ET
import datetime
import os
import json
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


def fetch_custom_rss(url):
    """
    지정된 RSS URL에서 XML 데이터를 가져옵니다.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"[ERROR] Custom RSS Fetch failed ({url}): {e}")
        return None

def run_grant_job(dry_run=True):
    """
    dry_run=True: 포스팅은 하지 않고 수집/분석만 수행 (로그 확인용)
    """
    print(f"[INFO] [Grant Bot] Started. (Dry Run: {dry_run})")
    update_status("running", "[START] 지원사업 공고 수집 시작...", 0.1)
    
    config = load_config()
    grant_config = config.get('grant', {})
    categories = grant_config.get('categories', {})
    sources = grant_config.get('sources', [])
    
    total_published = 0
    total_found = 0
    
    # 1. 키워드 검색 (Google News)
    if categories:
        cat_keys = list(categories.keys())
        for c_idx, (category_name, keywords) in enumerate(categories.items()):
            
            # 진행률 업데이트
            progress = 0.1 + (c_idx / len(cat_keys)) * 0.3
            update_status("running", f"[SEARCH] '{category_name}' 관련 공고 찾는 중...", progress)
            
            if not keywords: continue
            query = " OR ".join(keywords)
            print(f"\n[CATEGORY] {category_name} (Query: {query})")
            
            rss_xml = fetch_google_news_rss(query)
            if not rss_xml: continue
                
            grant_items = parse_rss_items(rss_xml, limit=3) 
            total_found += len(grant_items)
            
            for item in grant_items:
                process_grant_item(item, category_name, dry_run)
                if not dry_run: total_published += 1 # Note: Logic simplification needed? process_item returns success?
                # Let's refactor process_item out or keep it simple. 
                # To keep it simple in this edit, I will inline the logic or make a helper.
                # Actually, let's keep the previous logic but updated.
                
    # 2. 맞춤 RSS 소스 (Custom Sources)
    if sources:
        update_status("running", "[RSS] 맞춤 소스 수집 중...", 0.5)
        for s_idx, source_url in enumerate(sources):
            print(f"\n[SOURCE] {source_url}")
            rss_xml = fetch_custom_rss(source_url)
            if not rss_xml: continue
            
            # 소스 이름은 URL 도메인 등으로 간단히? 아니면 그냥 [RSS] 태그
            source_tag = "기타공고" 
            
            grant_items = parse_rss_items(rss_xml, limit=5)
            total_found += len(grant_items)
            
            for item in grant_items:
                 # RSS 아이템 처리 (중복 코드 방지를 위해 내부 함수나 헬퍼 필요하지만 일단 인라인)
                 process_grant_item(item, source_tag, dry_run)


def process_grant_item(item, category_tag, dry_run):
    """
    공통 아이템 처리 로직 (분석 -> 포스팅)
    """
    title = item['title']
    print(f"[Item] {title}")
    
    if dry_run:
        print("   -> [Dry Run] Posting skipped.")
        return

    # 전문가 분석
    expert_analysis = analyze_grant_as_expert(item['title'], item['description'], item['link'])
    if "오류 발생" in expert_analysis:
        return

    # 태그 붙여서 포스팅
    wp_title = f"[{category_tag}] {title} - 전문가 분석"
    
    wp_content = f"""
    <p><i>이 글은 정부지원금 데이터와 AI 전문가의 분석을 바탕으로 작성되었습니다.</i></p>
    <hr>
    <h2>📢 공고 요약</h2>
    <p><strong>제목</strong>: {title}</p>
    <p><strong>발행일</strong>: {item['pub_date']}</p>
    <p><a href="{item['link']}">👉 원문 기사/공고 보러가기</a></p>
    <hr>
    {expert_analysis}
    <hr>
    <p>※ 본 분석은 AI에 의해 작성되었으며, 정확한 내용은 반드시 공식 기관의 공고를 재확인하시기 바랍니다.</p>
    """
    
    res = wp_utils.post_article(wp_title, wp_content)
    if res:
        print(f"[SUCCESS] Posted: {wp_title}")
    else:
        print(f"[FAILURE] Failed to post: {wp_title}")


def load_config():
    with open('bot_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

if __name__ == "__main__":
    import sys
    
    # 기본은 Dry Run (포스팅 안함)
    # python grant_bot.py --post 로 실행 시 실제 포스팅
    
    is_dry_run = True
    if len(sys.argv) > 1 and "--post" in sys.argv:
        is_dry_run = False
        
    run_grant_job(dry_run=is_dry_run)
