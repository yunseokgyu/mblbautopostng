import os
import wp_utils
import image_factory
from sec_module import core
import yfinance as yf
import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

import json

# 환경 변수 로드 (API Key 등)
core.load_dotenv('credentials.env')

# 한글 폰트 설정 (Windows 기준)
# 폰트가 깨질 경우를 대비해 맑은 고딕 등을 시도
try:
    font_path = "C:/Windows/Fonts/malgun.ttf"
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
except:
    plt.rcParams['font.family'] = 'sans-serif' # Fallback
plt.rcParams['axes.unicode_minus'] = False

# --- 상태 알림용 함수 ---
STATUS_FILE = "bot_status_stock.json"

def update_status(state, message, progress=0.0):
    """
    state: 'running', 'idle', 'error'
    message: 사용자에게 보여줄 메시지
    progress: 0.0 ~ 1.0
    """
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
        print(f"[ERROR] 상태 저장 실패: {e}")

def load_config():
    with open('bot_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def run_stock_job():
    print("[INFO] [주식 담당] 업무 시작")
    update_status("running", "[START] 봇 초기화 및 종목 리스트 로드 중...", 0.0)
    
    config = load_config()
    tickers = config.get('stock', {}).get('tickers', [])
    report_types = config.get('stock', {}).get('report_types', ["10-K"]) # 기본값 10-K
    
    if not tickers:
        print("[WARNING] 설정된 종목이 없습니다 (bot_config.json 확인 필요).")
        return

    # --- 1. 티커 확장 로직 (그룹 정보를 포함하도록 개선) ---
    expanded_items = [] # [{'symbol': 'AAPL', 'group': '@SP500_TECH'}, ...]
    
    for t in tickers:
        group_name = t # 기본값 (개별 티커인 경우)
        if t.startswith("@"):
            group_name = t # @SP500_TECH
            filename = t[1:].lower() + ".json"
            filepath = os.path.join("stock_data", filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        group_tickers = json.load(f)
                        for sym in group_tickers:
                            expanded_items.append({'symbol': sym, 'group': group_name})
                        print(f"[INFO] 그룹 로드 완료: {t} -> {len(group_tickers)}개 종목")
                except Exception as e:
                    print(f"[ERROR] 그룹 파일 로드 실패 ({t}): {e}")
            else:
                print(f"[WARNING] 그룹 파일을 찾을 수 없습니다: {filepath}")
        else:
            expanded_items.append({'symbol': t, 'group': 'Individual'})
            
    # 중복 제거 (심볼 기준, 먼저 나온 그룹 우선)
    unique_items = {}
    for item in expanded_items:
        if item['symbol'] not in unique_items:
            unique_items[item['symbol']] = item
            
    final_items = list(unique_items.values())
    total_tickers = len(final_items)
    print(f"[INFO] 총 분석 대상: {total_tickers}개 종목")
    # --- 2. 히스토리 초기화 (User Request) ---
    # 매 실행마다 기억을 지워서, 워드프레스에서 삭제된 글을 다시 발행할 수 있게 함.
    # 단, 이번 실행 중에 중복 발행되는 것을 막기 위해 빈 딕셔너리로 시작.
    # history_file = os.path.join("stock_data", "published_history.json") # 로드 안 함
    history = {} 
    print("[INFO] 히스토리 초기화 완료 (삭제된 글 재발행 모드)")

    # --- 3. WP 최근 글 로드 (Batch Check) ---
    # 루프 안에서 매번 호출하면 API 제한 걸림. 여기서 한 번에 300개 로드 (안전하게 범위 늘림).
    print("[INFO] WP 최근 발행글 로드 중 (Batch - 300 limit)...")
    recent_posts = wp_utils.get_recent_posts(limit=300)
    print(f"[INFO] 최근 {len(recent_posts)}개 리포트 정보 로드 완료.")

    for i, item in enumerate(final_items):
        target_ticker = item['symbol']
        group_name = item['group']
        
        print(f"\n[PROGRESS {i+1}/{total_tickers}] Processing {target_ticker} ({group_name})...")
        
        # 상태 업데이트 (진행률 계산 + 그룹 정보 포함)
        progress_percent = (i / total_tickers)
        status_msg = f"[PROGRESS] [{i+1}/{total_tickers}] {target_ticker}"
        # JSON에 그룹 정보를 별도로 저장하면 좋겠지만, 일단 메시지에 포함
        # Dashboard에서 파싱하기 쉽게 포맷팅: "MSG | GROUP | TICKER"
        update_status("running", f"{status_msg} analyzing...|{group_name}|{target_ticker}", progress_percent)
        
        # [Early Deduplication Check]
        # 날짜를 아직 모르는 상태지만, 오늘 날짜 등으로 빠른 스킵이 가능하다면 좋겠지만
        # 정확성을 위해 메타데이터(날짜) 확인 후 스킵하는 로직을 유지하거나,
        # 최근 며칠 사이 history에 있다면 스킵하는 로직 추가 가능.
        # 일단은 기존대로 SEC Date 확인 후 스킵.
        
        try:
            # 1. 실제 차트 생성 (상단 부착용)
            chart_url = image_factory.create_chart_image(target_ticker)
            
            # (AI 이미지는 뒤에서 생성)
        except Exception as e:
            print(f"[ERROR] 차트 생성 중 에러 ({target_ticker}): {e}")
            chart_url = None

        for r_type in report_types:
            print(f"[TARGET] 분석 대상: {target_ticker} ({r_type})")

            # 3. SEC 데이터 수집 (최적화 적용)
            # 1단계: 메타데이터만 먼저 확인 (CIK -> URL & Date)
            cik = core.get_cik_from_ticker(target_ticker)
            if not cik:
                print(f"[ERROR] CIK 찾기 실패: {target_ticker}")
                continue
                
            filing_url, filing_date = core.get_latest_filing_url(cik, target_ticker, form_type=r_type)
            
            if not filing_url:
                print(f"[WARNING] {target_ticker}의 {r_type} 데이터를 찾을 수 없습니다.")
                continue
            
            # 2단계: 중복 검사 (다운로드 전에 실행!)
            # --- [중복 방지 체크 (Stateless for Render)] ---
            recent_posts = wp_utils.get_recent_posts(limit=20) 
            check_title_part = f"{target_ticker} {r_type} 리포트 ({filing_date})"
            
            is_duplicate = False
            for p in recent_posts:
                if check_title_part in p.get('title', ''):
                    is_duplicate = True
                    break

            if is_duplicate:
                print(f"[SKIP] 이미 발행된 리포트입니다(WP Check): {check_title_part}")
                # 이미 발행되었으므로 다운로드 하지 않음! (트래픽 절약의 핵심)
                continue
            
            # 기존 로컬 히스토리도 체크
            unique_key = f"{target_ticker}_{r_type}_{filing_date}"
            # history.get(key)가 True일 때만 스킵 (False면 재시도 허용)
            if history.get(unique_key):
                print(f"[SKIP] 이미 발행된 리포트입니다(Local Check): {unique_key}")
                continue
            
            # 3단계: 실제 다운로드 (중복이 아닐 때만)
            print(f"[NEW] 새로운 리포트 발견! ({filing_date}) -> 다운로드 시작...")
            html_content = core.download_filing_html(filing_url)
            
            if not html_content:
                print(f"[WARNING] {target_ticker} 다운로드 실패")
                continue 
            
            print(f"[INFO] {r_type} 데이터 확보 완료 ({filing_date})")

            # 4. 데이터 전처리
            text_to_analyze = core.extract_sections(html_content)

            if not text_to_analyze:
                print("[WARNING] 텍스트 추출 실패")
                continue

            # 5. Gemini 분석
            print("[INFO] Gemini 분석 시작...")
            report_markdown = core.analyze_with_gemini(
                text_to_analyze, 
                target_ticker, 
                filing_date, 
                mode="summary"
            )

            if not report_markdown:
                print("[WARNING] 분석 보고서 생성 실패")
                continue

            try:
                html_body = markdown.markdown(report_markdown)
            except ImportError:
                html_body = f"<pre>{report_markdown}</pre>"
            
            # --- [FEATURED IMAGE] 대표 이미지 생성 ---
            # 태그 정보(tag_str)를 활용 (예: [S&P500])
            featured_media_id = None
            
            # 태그 정리: "[S&P500/배당킹]" -> "S&P500 / 배당킹" 제거 후 깔끔하게
            clean_subtext = "Stock Report"
            if tag_str:
                clean_subtext = tag_str.replace("[", "").replace("]", "").replace("/", " & ")
            
            badge_path = image_factory.create_text_image(target_ticker, clean_subtext, f"badge_{target_ticker}.png")
            
            if badge_path:
                print(f"[Featured] 워드프레스에 썸네일 업로드 중...")
                media_id = wp_utils.upload_image_to_wordpress(badge_path)
                if media_id:
                    featured_media_id = media_id
                
                # 임시 파일 삭제
                try:
                    os.remove(badge_path)
                except:
                    pass
            # ------------------------------------------

            # (A) 차트 HTML (최상단)
            chart_html = ""
            if chart_url:
                chart_html = f"""
                <div style='text-align:center; margin-bottom:50px;'>
                    <img src='{chart_url}' alt='{target_ticker} Stock Chart' style='width:100%; max-width:100%; margin: 0 auto;'/>
                    <div style='font-size:0.8em; color:#999; margin-top:10px; font-family:"Noto Sans KR"; font-weight:300;'>1년 주가 추이</div>
                </div>
                """

            # (B) 추가 이미지 생성 (AI 3장 + 무료 2장 = 총 5장 정도 목표)
            additional_images = []
            
            # AI 이미지 프롬프트 목록
            ai_prompts = [
                f"{target_ticker} futuristic office, technology, 4k",
                f"{target_ticker} financial growth, graph, success, 3d render",
                f"{target_ticker} global business, map, connection, digital art"
            ]
            
            # 무료 이미지 키워드 목록
            free_keywords = ["business meeting", "financial district"]
            
            print("[INFO] 추가 이미지 생성/수집 시작...")
            
            # 1. AI 이미지 생성
            for p in ai_prompts:
                url = image_factory.create_ai_image(p)
                if url: additional_images.append(url)
            
            # 2. 무료 이미지 수집
            for k in free_keywords:
                urls = image_factory.fetch_free_images(k, count=1)
                if urls:
                    additional_images.append(urls[0])
                
            print(f"[INFO] 총 {len(additional_images)}개의 추가 이미지가 준비되었습니다.")

            # (C) 본문에 이미지 골고루 섞기
            # HTML을 <h2>(섹션) 기준으로 쪼개서 그 사이에 이미지를 하나씩 집어넣음
            
            sections = html_body.split("<h2>")
            new_html_body = sections[0] # 첫 번째 덩어리 (보통 개요)
            
            img_idx = 0
            for i, section in enumerate(sections[1:]):
                # 이미지 태그 준비
                img_tag = ""
                if img_idx < len(additional_images):
                    img_url = additional_images[img_idx]
                    img_tag = f"""
                    <div style='text-align:center; margin: 60px 0;'>
                        <img src='{img_url}' style='width:100%; max-width:100%; border:none; box-shadow:none;' loading='lazy'/>
                    </div>
                    """
                    img_idx += 1
                
                # 섹션 다시 붙이기 (<h2> 복구)
                new_html_body += f"{img_tag}<h2>{section}"
            
            # 남은 이미지가 있다면 맨 아래에 갤러리처럼 추가
            if img_idx < len(additional_images):
                new_html_body += "<h3>Gallery</h3><div style='display:flex; flex-wrap:wrap; gap:10px; justify-content:center;'>"
                while img_idx < len(additional_images):
                    new_html_body += f"<img src='{additional_images[img_idx]}' style='width:45%; max-width:300px; border-radius:5px;'/>"
                    img_idx += 1
                new_html_body += "</div>"

            # --- [타이틀 태그 생성] ---
            # 티커가 어느 그룹에 속하는지 확인
            tags = []
            
            # S&P500 확인
            sp500_path = os.path.join("stock_data", "sp500.json")
            if os.path.exists(sp500_path):
                with open(sp500_path, 'r', encoding='utf-8') as f:
                    if target_ticker in json.load(f):
                        tags.append("S&P500")
            
            # 배당킹 확인
            div_kings_path = os.path.join("stock_data", "dividend_kings.json")
            if os.path.exists(div_kings_path):
                with open(div_kings_path, 'r', encoding='utf-8') as f:
                    if target_ticker in json.load(f):
                        tags.append("배당킹")
            
            # 태그 문자열 조합 (예: "[S&P500/배당킹]")
            tag_str = ""
            if tags:
                tag_str = "[" + "/".join(tags) + "]"

            # 폰트 적용을 위한 HTML 래퍼 (Brunch Style: Narrow, Nanum Myeongjo, Whitespace)
            font_style = """
            <link href="https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700&family=Noto+Sans+KR:wght@300;400;700&display=swap" rel="stylesheet">
            <style>
                .sec-report-content { 
                    max-width: 720px; /* 좁은 본문 폭 (가독성 최적화) */
                    margin: 0 auto;   /* 중앙 정렬 */
                    font-family: 'Noto Sans KR', sans-serif; 
                    line-height: 2.0; /* 넉넉한 줄간격 */
                    font-size: 17px;  /* 편안한 글자 크기 */
                    color: #222;
                    padding: 20px 0;
                }
                /* 제목: 나눔명조 (감성적 권위) */
                .sec-report-content h1, 
                .sec-report-content h2, 
                .sec-report-content h3 { 
                    font-family: 'Nanum Myeongjo', serif; 
                    font-weight: 700; 
                    color: #111;
                    margin-top: 70px;    /* 극강의 여백 */
                    margin-bottom: 30px;
                    letter-spacing: -0.03em;
                    word-break: keep-all;
                }
                .sec-report-content p, .sec-report-content li {
                    margin-bottom: 24px;
                    word-break: keep-all;
                    letter-spacing: -0.02em;
                }
                /* 이미지: 테두리/그림자 제거, 여백 강조 */
                .sec-report-content img {
                    display: block;
                    margin: 60px auto;
                    max-width: 100%;
                    border: none !important;
                    box-shadow: none !important;
                    border-radius: 0 !important;
                }
                hr {
                    border: 0;
                    height: 1px;
                    background: #eee;
                    margin: 100px 0;
                }
            </style>
            """

            # --- [광고 주입: Native Ad] ---
            # utils/ads.py 에서 가져옴
            from utils.ads import get_course_ad_html
            ad_block = get_course_ad_html(target_ticker)

            final_content = f"""
            {font_style}
            <div class="sec-report-content">
                <h3>{target_ticker} {r_type} 분석 보고서 ({filing_date})</h3>
                {chart_html}
                <p>AI(Gemini)가 분석한 공시 요약입니다.</p>
                <p><strong>{tag_str}</strong>에 해당하는 기업입니다.</p>
                <hr>
                {new_html_body}
                {ad_block}
            </div>
            """ 

            title = f"{tag_str} [SEC] {target_ticker} {r_type} 리포트 ({filing_date})"
            
            # 카테고리 설정 (stock)
            cat_id = wp_utils.ensure_category("stock")
            cat_ids = [cat_id] if cat_id else []
            
            result = wp_utils.post_article(title, final_content, category_ids=cat_ids, featured_media=featured_media_id)
            
            if result:
                print(f"[SUCCESS] [{target_ticker} {r_type}] 발행 완료.")
                # 히스토리 업데이트
                history[unique_key] = True
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=4, ensure_ascii=False)
            else:
                print(f"[FAILURE] [{target_ticker} {r_type}] 발행 실패.")
                # 히스토리 업데이트 (실패 시에도 기록)
                history[unique_key] = False # 또는 다른 실패 상태를 나타내는 값
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=4, ensure_ascii=False)


import time

if __name__ == "__main__":
    import sys
    
    # 기본은 1회 실행 (대시보드 수동 실행 호환용)
    # python stock_bot.py --loop 로 실행 시 무한 루프
    
    if len(sys.argv) > 1 and sys.argv[1] == "--loop":
        mode = "loop"
    else:
        mode = "once"
        
    print(f"[SYSTEM] Stock Bot Starting (Mode: {mode})")
    
    if mode == "loop":
        while True:
            try:
                run_stock_job()
                print("[SYSTEM] Cycle finished. Sleeping for 1 hour...")
                update_status("idle", "[WAIT] 다음 사이클 대기 중 (1시간)", 1.0)
                time.sleep(3600) 
            except KeyboardInterrupt:
                print("[SYSTEM] Bot stopped by user.")
                break
            except Exception as e:
                print(f"[CRITICAL ERROR] Bot crashed: {e}")
                update_status("error", f"[ERROR] 봇 크래시: {str(e)}", 0.0)
                print("[SYSTEM] Restarting in 60 seconds...")
                time.sleep(60)
    else:
        # 1회 실행
        try:
            run_stock_job()
            print("[SYSTEM] Job finished.")
        except Exception as e:
            print(f"[ERROR] Execution failed: {e}")
            update_status("error", f"[ERROR] 실행 실패: {str(e)}", 0.0)
