import streamlit as st
import json
import os
import subprocess
import time

# 페이지 설정
st.set_page_config(
    page_title="MBLB 자동화 대시보드",
    page_icon="🤖",
    layout="wide"
)

CONFIG_FILE = 'bot_config.json'

def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    st.toast("설정이 저장되었습니다!", icon="💾")

def run_bot(script_name, args=[]):
    """지정된 봇 스크립트를 실행합니다."""
    with st.spinner(f"🚀 {script_name} 실행 중..."):
        try:
            # 서브프로세스로 실행하여 결과 캡처
            cmd = ["python", script_name] + args
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', # 윈도우 한글 깨짐 방지
                env=dict(os.environ, PYTHONIOENCODING='utf-8')  # 이모지/한글 출력 에러 방지
            )
            if result.returncode == 0:
                st.success(f"✅ {script_name} 실행 완료!")
                st.code(result.stdout)
            else:
                st.error(f"❌ 실행 실패")
                st.code(result.stderr)
        except Exception as e:
            st.error(f"에러 발생: {e}")


# --- UI 메인 ---
st.title("🤖 MBLB 자동화 봇 관제탑")

# 사이드바
with st.sidebar:
    st.header("상태 모니터")
    st.metric("워드프레스 연결", "정상", delta_color="normal")
    if st.button("🔄 설정 새로고침"):
        st.rerun()
    st.markdown("---")
    st.info("💡 설정을 변경하면 즉시 반영됩니다.")

# 설정 로드
try:
    config = load_config()
except Exception as e:
    st.error(f"설정 파일을 불러오지 못했습니다: {e}")
    st.stop()

# 탭 스타일링 (Big Button Style + Noto Sans KR)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }

    /* 탭 컨테이너 글자 크기 키우기 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.5rem; /* 글자 크기 */
        font-weight: 700;
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        font-family: 'Noto Sans KR', sans-serif;
    }
    /* 탭 버튼 자체 스타일링 */
    .stTabs [data-baseweb="tab-list"] button {
        flex: 1; /* 너비 꽉 채우기 */
        background-color: #f0f2f6; /* 연한 회색 배경 */
        border-radius: 5px 5px 0 0;
        margin-right: 5px;
    }
    /* 선택된 탭 강조 */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 3px solid #ff4b4b; /* Streamlit Red */
    }
</style>
""", unsafe_allow_html=True)

# --- [Helper Function] ---
def display_bot_status(status_file, bot_name):
    """
    각 봇의 상태 파일(JSON)을 읽어서 UI 카드로 표시합니다.
    """
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status_data = json.load(f)
            
            state = status_data.get("state", "idle")
            raw_msg = status_data.get("message", "대기 중")
            progress = status_data.get("progress", 0.0)
            timestamp = status_data.get("timestamp", "")
            
            if state == "running":
                # Running UI
                st.markdown(f"""
                <div style="background-color: #ff4b4b; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    🔥 <strong>{bot_name}</strong> 작동 중... (자동 새로고침)
                </div>
                """, unsafe_allow_html=True)
                
                parts = raw_msg.split('|')
                if len(parts) >= 3:
                    display_msg = parts[0]
                else:
                    display_msg = raw_msg
                
                st.progress(progress)
                st.caption(f"📝 {display_msg} (Last: {timestamp})")
                
                # 실행 중일 때만 리런 (너무 잦은 리런 방지 위해 버튼으로 대체 가능하나, 일단 실시간성 유지)
                # time.sleep(1)
                # st.rerun() 
            
            else:
                # Idle/Error UI
                icon = "✅" if state != "error" else "❌"
                st.info(f"{icon} **{bot_name}** 상태: {state.upper()} (Last: {timestamp})")
                st.write(f"메시지: {raw_msg}")

        except Exception as e:
            st.error(f"{bot_name} 상태 로드 실패: {e}")
    else:
        st.warning(f"💤 {bot_name} 실행 기록이 없습니다.")

st.write("---")

# 탭 구성 (이모지 제거)
tab1, tab2, tab3, tab4 = st.tabs(["주식 봇", "마케팅 봇", "지원금 봇", "발행된 글"])

# --- Tab 1: 주식 봇 ---
with tab1:
    st.subheader("📊 주식 봇 상태")
    display_bot_status("bot_status_stock.json", "Stock Bot")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("분석 대상 종목 (Tickers)")
        
        # 현재 티커 리스트
        current_tickers = config['stock'].get('tickers', [])
        
        # 칩 형태로 보여주기
        st.write("현재 등록된 종목:")
        
        # 일반 종목과 그룹 분리해서 표시
        normal_tickers = [t for t in current_tickers if not t.startswith("@")]
        group_tickers = [t for t in current_tickers if t.startswith("@")]
        
        if normal_tickers:
            st.write("🔹 개별 종목: " + ", ".join([f"`{t}`" for t in normal_tickers]))
            
        if group_tickers:
            st.write("📦 **그룹 리스트** (클릭해서 내용 확인)")
            for gt in group_tickers:
                group_name = gt[1:] # @ 제거
                file_path = os.path.join("stock_data", f"{group_name.lower()}.json")
                
                member_count = 0
                members = []
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            members = json.load(f)
                            member_count = len(members)
                    except:
                        members = ["로드 실패"]
                
                with st.expander(f"👑 {group_name} ({member_count}개 종목)"):
                    st.caption(", ".join(members))

        # 추가/삭제 UI
        new_ticker = st.text_input("종목 추가 (예: TSLA 또는 @GROUP)", key="new_ticker").upper()
        if st.button("➕ 종목 추가", key="add_ticker"):
            if new_ticker and new_ticker not in current_tickers:
                current_tickers.append(new_ticker)
                config['stock']['tickers'] = current_tickers
                save_config(config)
                st.rerun()
            elif new_ticker in current_tickers:
                st.warning("이미 존재하는 종목입니다.")

        ticker_to_remove = st.selectbox("종목 삭제", ["선택하세요"] + current_tickers, key="remove_ticker_select")
        if st.button("🗑️ 종목 삭제", key="remove_ticker_btn"):
            if ticker_to_remove != "선택하세요":
                current_tickers.remove(ticker_to_remove)
                config['stock']['tickers'] = current_tickers
                save_config(config)
                st.rerun()

        st.subheader("보고서 종류 설정")
        current_types = config['stock'].get('report_types', ["10-K"])
        available_types = ["10-K", "10-Q", "8-K"]
        
        selected_types = st.multiselect(
            "분석할 보고서 종류 선택",
            available_types,
            default=current_types,
            key="report_types_select"
        )
        
        if st.button("💾 보고서 설정 저장", key="save_report_types"):
            config['stock']['report_types'] = selected_types
            save_config(config)

    with col2:
        st.subheader("수동 실행")
        st.write("지금 바로 분석을 시작합니다.")
        if st.button("🚀 주식 봇 실행 (1회)", type="primary"):
            run_bot("stock_bot.py")

        st.write("---")
        st.subheader("자동 실행 (무한 루프)")
        st.caption("1시간마다 자동으로 실행됩니다. (백그라운드)")
        
        if st.button("⚡ 주식 봇 자동모드 시작"):
            try:
                # 백그라운드 실행 (Non-blocking)
                subprocess.Popen(["python", "stock_bot.py", "--loop"], 
                                 creationflags=subprocess.CREATE_NEW_CONSOLE)
                st.toast("자동 모드가 시작되었습니다! (새 콘솔 창 확인)", icon="✅")
                # 상태 업데이트를 위해 잠시 대기
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"실행 실패: {e}")

# --- Tab 2: 마케팅 봇 ---
with tab2:
    st.subheader("📢 마케팅 봇 상태")
    display_bot_status("bot_status_marketing.json", "Marketing Bot")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("뉴스 키워드 관리")
        
        current_keywords = config['marketing'].get('keywords', [])
        
        # 데이터 에디터로 편하게 수정
        edited_keywords = st.data_editor(
            [{"키워드": k} for k in current_keywords],
            num_rows="dynamic",
            use_container_width=True
        )
        
        if st.button("💾 키워드 저장", key="save_keywords"):
            # 데이터 에디터 결과 -> 설정 포맷 변환
            new_kws = [row["키워드"] for row in edited_keywords if row["키워드"]]
            config['marketing']['keywords'] = new_kws
            save_config(config)

    with col2:
        st.subheader("수동 실행")
        st.write("AI 트렌드 리포트를 즉시 생성합니다.")
        if st.button("🚀 마케팅 봇 실행", type="primary"):
            run_bot("marketing_bot.py")

# --- Tab 3: 지원금 봇 ---
with tab3:
    st.subheader("💰 지원금 봇 상태")
    display_bot_status("bot_status_grant.json", "Grant Bot")
    st.markdown("---")

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📂 수집 카테고리 관리")
        current_categories = config.get('grant', {}).get('categories', {})
        
        # 1. 카테고리 선택 (수정/삭제용)
        cat_names = list(current_categories.keys())
        selected_cat = st.selectbox("수정할 카테고리 선택", ["(새 카테고리 추가)"] + cat_names)
        
        if selected_cat == "(새 카테고리 추가)":
            new_cat_name = st.text_input("새 카테고리 이름 입력 (예: 청년창업)").strip()
            if st.button("➕ 카테고리 생성", disabled=not new_cat_name):
                if new_cat_name in cat_names:
                    st.error("이미 존재하는 카테고리입니다.")
                else:
                    current_categories[new_cat_name] = [] # 빈 리스트로 생성
                    config['grant']['categories'] = current_categories
                    save_config(config)
                    st.rerun()
        else:
            # 2. 키워드 편집
            st.write(f"**'{selected_cat}'** 검색 키워드 편집")
            
            # 현재 키워드 가져오기
            keywords = current_categories[selected_cat]
            
            # Data Editor로 편집
            df_data = [{"키워드": k} for k in keywords]
            edited_df = st.data_editor(df_data, num_rows="dynamic", use_container_width=True, key=f"editor_{selected_cat}")
            
            col_save, col_del = st.columns([1, 1])
            with col_save:
                if st.button("💾 키워드 저장", key=f"save_{selected_cat}"):
                    new_keywords = [row["키워드"] for row in edited_df if row["키워드"].strip()]
                    current_categories[selected_cat] = new_keywords
                    config['grant']['categories'] = current_categories
                    save_config(config)
                    st.success("저장되었습니다!")
            
            with col_del:
                if st.button("🗑️ 카테고리 삭제", key=f"del_{selected_cat}", type="primary"):
                    del current_categories[selected_cat]
                    config['grant']['categories'] = current_categories
                    save_config(config)
                    st.rerun()
        
        # RSS 관리 섹션 이동됨
        pass

    with col2:
        st.subheader("🏛️ 정부 공고 사이트 관리")
        st.caption("공식 사이트 직접 수집 (On/Off)")
        
        # 크롤러 설정 (config['grant']['crawlers'])
        # 기본값: 모두 True
        defaults = {'kstartup': True, 'sbiz': True, 'export': True, 'mssd': True}
        current_crawlers = config.get('grant', {}).get('crawlers', defaults)
        
        # 4개의 토글 스위치
        c1, c2 = st.columns(2)
        with c1:
            use_kstartup = st.toggle("K-Startup (창업넷)", value=current_crawlers.get('kstartup', True))
            use_sbiz = st.toggle("소상공인24", value=current_crawlers.get('sbiz', True))
        with c2:
            use_export = st.toggle("수출바우처", value=current_crawlers.get('export', True))
            use_mssd = st.toggle("제조바우처(중기부)", value=current_crawlers.get('mssd', True))
        
        # 저장 로직
        new_state = {
            'kstartup': use_kstartup,
            'sbiz': use_sbiz,
            'export': use_export,
            'mssd': use_mssd
        }
        
        if new_state != current_crawlers:
            if 'grant' not in config: config['grant'] = {}
            config['grant']['crawlers'] = new_state
            save_config(config)
            st.rerun()

        st.markdown("---")
        st.write("**➕ 나만의 수집 사이트 추가 (RSS)**")
        st.caption("RSS 피드를 지원하는 모든 정부 기관 사이트를 추가할 수 있습니다.")
        
        current_sources = config.get('grant', {}).get('sources', [])
        
        # RSS 목록
        if current_sources:
            st.caption("RSS 피드 (XML)")
            for s_idx, source_url in enumerate(current_sources):
                rc1, rc2 = st.columns([3, 1])
                rc1.text(f"🔗 {source_url}")
                if rc2.button("삭제", key=f"del_src_{s_idx}"):
                    current_sources.pop(s_idx)
                    config['grant']['sources'] = current_sources
                    save_config(config)
                    st.rerun()
        
        # AI 수집 목록
        current_ai_sources = config.get('grant', {}).get('ai_sources', [])
        if current_ai_sources:
            st.caption("AI 스마트 수집 (Beta)")
            for a_idx, ai_url in enumerate(current_ai_sources):
                ac1, ac2 = st.columns([3, 1])
                ac1.text(f"🤖 {ai_url}")
                if ac2.button("삭제", key=f"del_ai_{a_idx}"):
                    current_ai_sources.pop(a_idx)
                    config['grant']['ai_sources'] = current_ai_sources
                    save_config(config)
                    st.rerun()

        if not current_sources and not current_ai_sources:
            st.caption("(추가된 사이트 없음)")
            
        # 추가 logic
        with st.expander("사이트 추가하기", expanded=True):
            st.info("💡 팁: 여러 사이트를 넣고 싶으면 줄바꿈으로 구분해서 입력하세요.")
            
            # 입력값 세션 상태 초기화 (bulk_input이 없으면 빈 문자열)
            if "bulk_input" not in st.session_state:
                st.session_state["bulk_input"] = ""

            new_rss_text = st.text_area("사이트 주소 입력 (여러 개 가능)", 
                                        placeholder="예:\nhttps://www.korea.kr\nhttps://www.bizinfo.go.kr", 
                                        key="bulk_input",
                                        height=100)
            
            if st.button("등록 (일괄 처리)", key="add_rss_btn"):
                urls = [u.strip() for u in new_rss_text.split('\n') if u.strip()]
                
                if urls:
                    added_count = 0
                    with st.spinner(f"{len(urls)}개 사이트 분석 중..."):
                        import requests
                        from bs4 import BeautifulSoup
                        from urllib.parse import urljoin
                        headers = {'User-Agent': 'Mozilla/5.0'}

                        for target_url in urls:
                            st.write(f"🔍 분석 중: **{target_url}**")
                            # 1. 중복 체크
                            if target_url in current_sources or target_url in current_ai_sources:
                                st.warning(f"  - 이미 등록된 URL입니다: {target_url}")
                                continue
                            
                            # 2. RSS 자동 탐지 시도
                            final_url = target_url
                            found_rss = False
                            try:
                                resp = requests.get(target_url, headers=headers, timeout=5)
                                if resp.status_code == 200:
                                    if resp.text.strip().startswith('<?xml') or '<rss' in resp.text:
                                        found_rss = True
                                        final_url = target_url
                                    else:
                                        soup = BeautifulSoup(resp.text, 'html.parser')
                                        rss_link = soup.find('link', type='application/rss+xml')
                                        if not rss_link: rss_link = soup.find('link', type='application/atom+xml')
                                        if rss_link and rss_link.get('href'):
                                            found_rss = True
                                            final_url = urljoin(target_url, rss_link.get('href'))
                                        else:
                                            # Common paths
                                            for path in ['/rss', '/feed', '/board/rss']:
                                                try_url = urljoin(target_url, path)
                                                try_resp = requests.get(try_url, headers=headers, timeout=3)
                                                if try_resp.status_code == 200 and '<rss' in try_resp.text:
                                                    found_rss = True
                                                    final_url = try_url
                                                    break
                            except:
                                pass # Error handling silent for bulk
                            
                            # 3. 등록
                            if found_rss:
                                current_sources.append(final_url)
                                st.success(f"  - RSS 발견! (RSS 목록에 추가): {final_url}")
                                added_count += 1
                            else:
                                # RSS 없으면 -> AI 목록으로 자동 배정
                                current_ai_sources.append(target_url)
                                st.info(f"  - RSS 없음 -> (AI 수집 목록에 추가): {target_url}")
                                added_count += 1
                    
                    if added_count > 0:
                        config['grant']['sources'] = current_sources
                        config['grant']['ai_sources'] = current_ai_sources
                        save_config(config)
                        st.success(f"총 {added_count}개 사이트 등록 완료!")
                        # 입력창 비우기 (Rerun 시 session_state 초기화 필요하면 여기서 처리하거나, rerun으로 해결)
                        # 여기서는 rerun하면 text_area가 session_state 값으로 유지됨.
                        # 따라서 session_state를 비워줘야 함.
                        # st.session_state["bulk_input"] = "" -> 하지만 rerun 직전에 바꾸면 적용 안될 수 있음.
                        # callback을 쓰는게 낫지만, 여기선 rerun으로 처리.
                        time.sleep(1) # 결과 읽을 시간
                        st.rerun()
                    else:
                        st.warning("추가된 사이트가 없습니다.")
                else:
                    st.warning("URL을 입력해주세요.")
        
        st.markdown("---")
        st.subheader("🚀 실행 옵션")
        
        # Dry Run 토글
        enable_posting = st.toggle("실제 워드프레스 발행하기", value=False)
        
        if enable_posting:
            st.warning("주의: 활성화 시 실제 블로그에 글이 발행됩니다.")
        else:
            st.info("안전 모드: 수집 및 분석 로그만 확인하며, 글은 발행되지 않습니다.")

        if st.button("지원금 봇 실행 (1회)", type="primary"):
            args = []
            if enable_posting:
                args.append("--post")
            
            run_bot("grant_bot.py", args)
            
        st.write("---")
        st.subheader("자동 실행 (무한 루프)")
        st.caption("6시간마다 자동으로 실행됩니다. (백그라운드)")
        
        if st.button("⚡ 지원금 봇 자동모드 시작", key="grant_auto_start"):
            try:
                # 백그라운드 실행 (Non-blocking)
                cmd = ["python", "grant_bot.py", "--loop", "--post"]
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
                st.toast("지원금 봇 자동 모드가 시작되었습니다! (새 콘솔 창 확인)", icon="✅")
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"실행 실패: {e}")

# --- Tab 4: 발행된 글 ---
with tab4:
    if st.button("🔄 전체 상태 새로고침"):
        st.rerun()

    st.subheader("📰 최신 발행 글 목록 (WordPress)")
    
    import wp_utils # 늦은 import to avoid dependency issues on start
    
    if st.button("🔄 목록 새로고침", type="secondary"):
        st.rerun()

    posts = wp_utils.get_recent_posts(limit=10)
    
    if not posts:
        st.info("발행된 글이 없거나 워드프레스에서 가져오지 못했습니다.")
    else:
        for p in posts:
            with st.expander(f"{p['date']} | {p['title']}"):
                st.write(f"**Title:** {p['title']}")
                st.write(f"**Date:** {p['date']}")
                st.link_button("🌐 글 보러가기", p['link'])
