import replicate
import cloudinary
import cloudinary.uploader
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import yfinance as yf
import io
import os
from dotenv import load_dotenv

load_dotenv('credentials.env')

# Cloudinary 설정
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# 한글 폰트 설정 (Windows/Linux)
font_path = None
if os.path.exists("C:/Windows/Fonts/malgun.ttf"):
    font_path = "C:/Windows/Fonts/malgun.ttf"
elif os.path.exists("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
elif os.path.exists("/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"):
    font_path = "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"

if font_path:
    try:
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
        plt.rcParams['axes.unicode_minus'] = False
        print(f"✅ Font loaded: {font_path}")
    except Exception as e:
        print(f"⚠️ Font loading failed: {e}")
else:
    print("⚠️ No suitable Korean font found. Using default.")

# 1. 실제 주식 차트 생성 함수 (Matplotlib)
def create_chart_image(ticker, period="1y"):
    print(f"📈 [{ticker}] 실제 차트 그리는 중... (기간: {period})")
    try:
        # 데이터 수집
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            print(f"⚠️ [{ticker}] 데이터가 비어있습니다.")
            return None

        # 그래프 그리기
        plt.figure(figsize=(10, 6))
        plt.plot(hist.index, hist['Close'], label='Close Price', color='#003366')
        plt.title(f"{ticker} Stock Price Trend ({period})", fontsize=16, fontweight='bold')
        plt.xlabel("Date")
        plt.ylabel("Price ($)")
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend()
        plt.tight_layout()
        
        # 메모리에 저장 (파일 생성 X)
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        plt.close()

        # Cloudinary 업로드
        print("☁️ Cloudinary로 차트 업로드 중...")
        upload_result = cloudinary.uploader.upload(
            img_buffer, 
            public_id=f"chart_{ticker}",
            overwrite=True
        )
        url = upload_result['secure_url']
        print(f"✅ 차트 업로드 완료: {url}")
        return url
        
    except Exception as e:
        print(f"❌ 차트 생성 실패: {e}")
        return None

# 2. AI 일러스트 생성 함수 (Replicate)
def create_ai_image(prompt):
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        print("⚠️ REPLICATE_API_TOKEN이 없습니다. AI 이미지를 건너뜁니다.")
        return None

    print(f"🎨 [{prompt}] AI 이미지 생성 중 (Replicate)...")
    try:
        # Replicate로 생성 (SDXL 모델 사용 - 고퀄리티/가성비)
        # stability-ai/sdxl 모델 사용
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": f"financial illustration, {prompt}, high quality, digital art, 4k", 
                "width": 1024, 
                "height": 1024
            }
        )
        # output is usually a list of URLs
        if isinstance(output, list) and len(output) > 0:
            temp_url = output[0]
        else:
            temp_url = output

        print(f"🎨 이미지 생성 완료. Cloudinary로 이동 중...")
        
        # Cloudinary 업로드 (영구 저장)
        upload_result = cloudinary.uploader.upload(temp_url)
        url = upload_result['secure_url']
        print(f"✅ AI 이미지 업로드 완료: {url}")
        return url

    except Exception as e:
        print(f"❌ AI 이미지 실패: {e}")
        return None

def fetch_free_images(query, count=1):
    """
    Pexels API를 사용하여 무료 이미지를 검색하고, Cloudinary에 업로드한 후 URL 리스트를 반환합니다.
    (WP 용량 최적화를 위해 외부 호스팅 URL 사용)
    :param query: 검색 키워드
    :param count: 가져올 이미지 개수
    :return: Cloudinary 이미지 URL 리스트
    """
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("⚠️ PEXELS_API_KEY가 없습니다. 무료 이미지를 건너뜁니다.")
        return []

    print(f"📷 [{query}] 무료 이미지 {count}장 검색 중 (Pexels)...")
    try:
        import requests
        headers = {'Authorization': api_key}
        params = {'query': query, 'per_page': count, 'orientation': 'landscape'}
        response = requests.get('https://api.pexels.com/v1/search', headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            cloudinary_urls = []
            
            if data['photos']:
                print(f"   -> Pexels에서 {len(data['photos'])}장 발견. Cloudinary 업로드 시작...")
                for photo in data['photos']:
                    try:
                        # 원본(original) 대신 large2x나 large 사용
                        img_url = photo['src']['large']
                        
                        # Cloudinary 업로드
                        upload = cloudinary.uploader.upload(img_url)
                        c_url = upload['secure_url']
                        cloudinary_urls.append(c_url)
                        print(f"      ☁️ Uploaded: {c_url}")
                    except Exception as e:
                        print(f"      ❌ Cloudinary upload failed: {e}")

                print(f"✅ 총 {len(cloudinary_urls)}장 Cloudinary 준비 완료")
                return cloudinary_urls
            else:
                print("⚠️ 검색 결과가 없습니다.")
                return []
        else:
            print(f"❌ Pexels API 오류: {response.text}")
            return []
    except Exception as e:
        print(f"❌ 무료 이미지 검색 실패: {e}")
        return []

def create_text_image(text, subtext, output_filename="temp_featured.png"):
    """
    텍스트 기반의 대표 이미지를 생성하고 로컬 파일로 저장합니다.
    :param text: 메인 텍스트 (예: TSLA)
    :param subtext: 서브 텍스트 (예: S&P500)
    :param output_filename: 저장할 파일명
    :return: 저장된 파일 경로 (str) 또는 None
    """
    print(f"🎨 대표 이미지 생성 중... ({text} | {subtext})")
    try:
        # 배경색 및 텍스트 색상
        bg_color = '#1a237e' # Deep Blue
        text_color = 'white'
        
        plt.figure(figsize=(10, 6))
        
        # 배경 채우기
        plt.gca().set_facecolor(bg_color)
        
        # 텍스트 그리기 (중앙 정렬)
        plt.text(0.5, 0.6, text, 
                 fontsize=60, color=text_color, fontweight='bold',
                 ha='center', va='center')
                 
        plt.text(0.5, 0.3, subtext, 
                 fontsize=30, color='#ffab00', fontweight='normal', # Amber accent
                 ha='center', va='center')
        
        # 축 제거
        plt.axis('off')
        plt.tight_layout()
        
        # 여백 없이 저장 (facecolor 저장 시 적용)
        plt.savefig(output_filename, facecolor=bg_color, bbox_inches='tight', pad_inches=0.5)
        plt.close()
        
        return os.path.abspath(output_filename)
        
    except Exception as e:
        print(f"❌ 대표 이미지 생성 실패: {e}")
        return None
