import feedparser
import google.generativeai as genai
import os
import datetime
import wp_utils
from urllib.parse import quote
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv('credentials.env')

# Gemini 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # sec_module과 동일한 모델명 사용
    model = genai.GenerativeModel('gemini-flash-latest')
else:
    print("⚠️ GEMINI_API_KEY가 없습니다.")
    model = None

def load_config():
    import json
    with open('bot_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_news(keyword):
    print(f"🔍 '{keyword}' 뉴스 검색 중...")
    encoded_keyword = quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        feed = feedparser.parse(rss_url)
        news_items = []
        for entry in feed.entries[:3]: # 키워드 당 상위 3개
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "source": entry.source.get('title', 'Unknown')
            })
        return news_items
    except Exception as e:
        print(f"❌ RSS 파싱 에러 ({keyword}): {e}")
        return []

def summarize_news(all_news):
    if not model:
        return "<h3>AI 요약 실패 (API 키 없음)</h3><p>환경변수를 확인해주세요.</p>"
    
    print("🧠 Gemini가 뉴스를 분석하고 있습니다...")
    
    # 뉴스 데이터를 텍스트로 변환
    news_text = ""
    for kw, items in all_news.items():
        news_text += f"\n[키워드: {kw}]\n"
        for item in items:
            news_text += f"- {item['title']} ({item['source']})\n"

    prompt = f"""
    당신은 IT/마케팅 트렌드 전문 에디터입니다.
    아래 수집된 오늘자의 주요 뉴스 기사들을 바탕으로 '일일 마케팅 & 테크 트렌드 리포트'를 작성해주세요.

    **작성 지침:**
    1. **HTML 형식**으로 출력하세요. (별도의 마크다운 태그 없이 바로 html 태그 사용. 예: <h3>, <ul>, <li>, <strong>, <p>)
    2. 키워드별로 단순히 나열하지 말고, **핵심 이슈(Topic)** 중심으로 3~4가지 인사이트를 도출하여 그룹핑하세요.
    3. 각 이슈마다 **[현황 요약]**과 **[마케터의 시각(Insight)]**을 포함하여 전문성 있게 작성하세요.
    4. 문체는 '해요'체나 '합니다'체를 사용하여 정중하고 세련되게 작성하세요.

    **뉴스 데이터:**
    {news_text}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ Gemini 에러: {e}")
        return f"<h3>AI 분석 중 오류가 발생했습니다.</h3><p>{str(e)}</p>"

import json

STATUS_FILE = "bot_status_marketing.json"

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

def run_marketing_job():
    print("📢 [마케팅 담당] 업무 시작")
    update_status("running", "[START] 뉴스 키워드 수집 시작...", 0.1)
    
    config = load_config()
    keywords = config.get('marketing', {}).get('keywords', [])
    
    all_news = {}
    total_count = 0
    
    for i, kw in enumerate(keywords):
        update_status("running", f"[SEARCH] '{kw}' 검색 중...", 0.1 + (i / len(keywords)) * 0.2)
        items = fetch_news(kw)
        if items:
            all_news[kw] = items
            total_count += len(items)
            
    if total_count == 0:
        print("⚠️ 수집된 뉴스가 없습니다.")
        update_status("idle", "[INFO] 수집된 뉴스가 없어 종료합니다.", 0.0)
        return

    print(f"✅ 총 {total_count}건의 뉴스 수집 완료. 분석 시작합니다.")
    update_status("running", f"[AI] {total_count}건의 뉴스 분석 및 요약 중...", 0.4)

    # AI 요약
    ai_summary_html = summarize_news(all_news)
    
    update_status("running", "[POST] 워드프레스 발행 중...", 0.8)

    # 워드프레스 발행
    today = datetime.date.today().strftime("%Y-%m-%d")
    title = f"📢 [트렌드] Daily Tech & AI 이슈 브리핑 ({today})"
    
    # 본문 구성 (마크다운 백틱 제거 등 정제)
    clean_html = ai_summary_html.replace("```html", "").replace("```", "")

    content = f"""
    <p>안녕하세요. <strong>MBLB 자동화 봇</strong>입니다.<br>
    {today} 기준, 주요 IT 플랫폼(구글, 메타, 네이버 등)과 생성형 AI 시장의 핵심 흐름을 정리해드립니다.</p>
    <hr>
    {clean_html}
    <hr>
    <p style="font-size:0.8em; color:gray; text-align:center;">
        ※ 본 리포트는 실시간 뉴스를 바탕으로 AI가 자동 분석/작성하였습니다.<br>
        Powered by Google Gemini & Python Automation
    </p>
    """
    
    result = wp_utils.post_article(title, content)
    
    if result:
        print("✅ [마케팅 담당] 업무 완료! 성공적으로 발행함.")
        update_status("idle", f"[DONE] 발행 완료 ({today})", 1.0)
    else:
        print("❌ [마케팅 담당] 발행 실패.")
        update_status("error", "[ERROR] 발행 실패", 0.0)

if __name__ == "__main__":
    run_marketing_job()
