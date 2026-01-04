import wp_utils
import os
from dotenv import load_dotenv

load_dotenv('credentials.env')

print(f"WP_URL: {os.getenv('WP_URL')}")
print(f"WP_USER: {os.getenv('WP_USER')}")
# 비밀번호는 길이만 체크
pw = os.getenv('WP_PASSWORD')
print(f"WP_PASSWORD Length: {len(pw) if pw else 0}")

print("\n[TEST] Posting a dummy article...")
title = "[TEST] 워드프레스 발행 테스트"
content = "<p>이 글은 봇이 정상적으로 작동하는지 확인하는 테스트 글입니다.</p>"

link = wp_utils.post_article(title, content)

if link:
    print(f"\n[SUCCESS] 글이 발행되었습니다! 링크: {link}")
else:
    print("\n[FAILURE] 글 발행에 실패했습니다.")
