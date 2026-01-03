def get_course_ad_html(ticker):
    """
    주식 종목명(ticker)을 받아서 문맥에 맞는 광고 HTML을 반환
    (Toss Style Application)
    """
    return f"""
    <div style="
        background-color: #f2f4f6; 
        padding: 24px; 
        border-radius: 16px; 
        margin: 60px 0; 
        text-align: center; 
        border: none;
        font-family: 'Noto Sans KR', sans-serif;">
        
        <h3 style="margin: 0 0 10px 0; font-size: 18px; color: #333; font-weight: 700; font-family: 'Noto Sans KR', sans-serif;">
            📉 '{ticker}' 같은 종목, 직접 발굴하고 싶다면?
        </h3>
        <p style="margin: 0 0 20px 0; font-size: 15px; color: #6b7684; line-height: 1.5;">
            월스트리트 플랜의 <b>실전 투자 강의</b>에서<br>
            재무제표 분석부터 차트 보는 법까지 3시간 만에 마스터하세요.
        </p>
        <a href="https://wallstreetplan.com/course" target="_blank" style="
            display: inline-block;
            background-color: #3182f6;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            font-size: 15px;
            transition: background 0.2s;">
            강의 커리큘럼 확인하기 👉
        </a>
    </div>
    """
