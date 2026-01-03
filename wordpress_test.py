import requests
import base64
import json

# ==========================================
# [수정할 부분 1] 내 사이트 주소 (마지막에 / 빼세요)
site_url = "https://mblb2025.mycafe24.com"

# [수정할 부분 2] 워드프레스 로그인 아이디
user = "master-mblb"

# [수정할 부분 3] 아까 메모장에 적은 비밀번호 (띄어쓰기 포함해도 됨)
password = "uNkR nmKz SCSb xBds PI81 PE2d"
# ==========================================

# 1. 인증 정보 암호화 (출입증 만들기)
credential = f"{user}:{password}"
token = base64.b64encode(credential.encode()).decode("utf-8")

# 2. 보낼 글 내용
headers = {
    'Authorization': f'Basic {token}',
    'Content-Type': 'application/json'
}

post_data = {
    'title': '🚀 파이썬 연결 성공!',
    'content': '<h3>축하합니다.</h3><p>이 글이 보인다면 자동화 시스템을 구축할 준비가 끝난 것입니다.</p>',
    'status': 'publish'  # 즉시 발행
}

# 3. 전송 (API 호출)
print("서버에 노크하는 중...")
response = requests.post(f"{site_url}/wp-json/wp/v2/posts", headers=headers, json=post_data)

# 4. 결과 확인
if response.status_code == 201:
    print("✅ 성공! 글이 발행되었습니다.")
    print(f"확인하러 가기: {response.json()['link']}")
else:
    print("❌ 실패했습니다.")
    print(f"에러 코드: {response.status_code}")
    print(response.text)
