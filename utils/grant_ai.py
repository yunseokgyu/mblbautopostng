import google.generativeai as genai
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv('credentials.env')

# Gemini 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def analyze_grant_as_expert(grant_title, grant_description, grant_link):
    """
    지원금 공고를 '정부지원금 전문 컨설턴트'의 관점에서 분석합니다.
    단순 요약이 아니라, 인사이트와 전략을 제공합니다.
    """
    
    if not GEMINI_API_KEY:
        return "⚠️ Gemini API Key가 설정되지 않았습니다."

    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    prompt = f"""
    당신은 20년 경력의 '정부지원금 전문 컨설턴트'이자 '스타트업 전략가'입니다.
    아래의 지원사업 공고(또는 뉴스)를 분석하여, 독자(소상공인, 창업자)를 위한 "돈이 되는 전문 분석 리포트"를 작성해주세요.

    [분석 대상]
    - 제목: {grant_title}
    - 내용/요약: {grant_description}
    - 링크: {grant_link}

    [작성 가이드]
    1.  **어조**: 전문적이지만 이해하기 쉽게. "~~입니다", "~~해야 합니다"체 사용. 신뢰감 있는 톤.
    2.  **형식**: 가독성 좋은 마크다운(Markdown).
    3.  **필수 포함 섹션**:
        *   **🔍 전문가의 한 줄 평**: 이 사업이 왜 지금 중요한지 핵심을 찌르는 통찰.
        *   **💡 숨겨진 기회 (Don't Miss)**: 공고문에는 없지만 전문가 눈에 보이는 활용법 (예: 이 자금 받아서 마케팅보다는 R&D에 쓰세요 등).
        *   **⚠️ 독소조항 및 주의사항**: 탈락하기 쉬운 포인트나 나중에 문제될 수 있는 조건 경고.
        *   **🏆 합격 확률 높이는 Tip**: 심사위원이 좋아할 만한 키워드나 준비 서류 팁.
        *   **📊 추천 등급**: (★ 5개 만점 주관적 평가)
    
    [주의사항]
    - 내용을 지어내지 마세요. 주어진 정보가 부족하면 "상세 공고 확인 필요"라고 명시하세요.
    - 너무 뻔한 말(열심히 하세요 등)은 빼고, 실질적인 조언을 주세요.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ 분석 중 오류 발생: {str(e)}"
