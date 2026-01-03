import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv('credentials.env')

# Cloudinary 설정
cloudinary.config(
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
  api_key = os.getenv("CLOUDINARY_API_KEY"),
  api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

def upload_chart(image_buffer, public_id):
    """
    이미지 버퍼(BytesIO)를 Cloudinary에 업로드하고 URL을 반환합니다.
    """
    print("☁️ Cloudinary로 업로드 중...")
    try:
        response = cloudinary.uploader.upload(
            image_buffer, 
            public_id=public_id,
            overwrite=True
        )
        url = response['secure_url']
        print(f"✅ 업로드 성공: {url}")
        return url
    except Exception as e:
        print(f"❌ 업로드 실패: {e}")
        return None
