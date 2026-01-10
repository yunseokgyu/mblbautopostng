import os
import base64
import requests
import json
from dotenv import load_dotenv

# 환경 변수 로드 (이 모듈을 import하는 곳에서 load_dotenv가 호출되어 있어야 안전하지만, 여기서도 한번 더 호출)
load_dotenv('credentials.env')

def get_auth_header():
    """env 파일에서 ID/PW를 읽어 Basic Auth 헤더를 생성합니다."""
    user = os.getenv("WP_USER")
    password = os.getenv("WP_PASSWORD")
    
    if not user or not password:
        raise ValueError("credentials.env 파일에 WP_USER 또는 WP_PASSWORD가 없습니다.")

    credential = f"{user}:{password}"
    token = base64.b64encode(credential.encode()).decode("utf-8")
    return {
        'Authorization': f'Basic {token}',
        'Content-Type': 'application/json'
    }

def post_article(title, content, category_ids=None, featured_media=None):
    """
    워드프레스에 글을 발행합니다.
    :param title: 글 제목
    :param content: 글 본문 (HTML 가능)
    :param category_ids: 카테고리 ID 리스트 (Optional)
    :return: 업로드된 글의 링크 (실패 시 None)
    """
    site_url = os.getenv("WP_URL")
    if not site_url:
        print("❌ Error: WP_URL 환경변수가 설정되지 않았습니다.")
        return None

    headers = get_auth_header()
    post_data = {
        'title': title,
        'content': content,
        'status': 'publish'
    }
    
    if category_ids:
        post_data['categories'] = category_ids

    if featured_media:
        try:
            f_id = int(featured_media)
            if f_id > 0:
                post_data['featured_media'] = f_id
        except ValueError:
            print(f"⚠️ Warning: Invalid featured_media ID: {featured_media}")

    print(f"📤 워드프레스 전송 중... 제목: {title}")
    # print(f"   [Debug payload] featured_media: {post_data.get('featured_media')}")
    
    try:
        response = requests.post(f"{site_url}/wp-json/wp/v2/posts", headers=headers, json=post_data)
        
        if response.status_code == 201:
            link = response.json().get('link')
            print(f"✅ 발행 성공! 링크: {link}")
            return link
        else:
            print(f"❌ 발행 실패. API 응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 전송 중 에러 발생: {e}")
        return None

def upload_image_to_wordpress(image_path):
    """
    워드프레스 미디어 라이브러리에 이미지를 업로드합니다.
    :param image_path: 로컬 이미지 파일 경로
    :return: 업로드된 이미지의 URL (실패 시 None)
    """
    site_url = os.getenv("WP_URL")
    if not site_url:
        print("❌ Error: WP_URL 환경변수가 설정되지 않았습니다.")
        return None

    media_url = f"{site_url}/wp-json/wp/v2/media"
    headers = get_auth_header()
    # Content-Type은 request 라이브러리가 files 파라미터를 보고 자동으로 설정하므로 헤더에서 제거하거나 조정 필요
    # get_auth_header()는 Content-Type: application/json을 포함할 수 있으므로, 
    # 파일 업로드 시에는 이를 제외해야 함.
    
    # 인증 헤더만 남기기 (기존 get_auth_header가 Content-Type을 포함한다면, 여기서 새로 만드는 게 안전)
    if 'Content-Type' in headers:
        del headers['Content-Type']
    
    # 파일명 추출 (Content-Disposition용)
    filename = os.path.basename(image_path)
    headers['Content-Disposition'] = f'attachment; filename={filename}'

    print(f"📤 이미지 업로드 중... ({filename})")

    try:
        with open(image_path, 'rb') as img_file:
            files = {'file': img_file}
            response = requests.post(media_url, headers=headers, files=files)
        
        if response.status_code == 201:
            image_info = response.json()
            image_id = image_info.get('id')
            image_url = image_info.get('source_url')
            print(f"✅ 이미지 업로드 성공! ID: {image_id}, URL: {image_url}")
            return image_id # Return ID for featured_media
        else:
            print(f"❌ 이미지 업로드 실패. 응답: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 이미지 업로드 중 에러: {e}")
        return None

def get_recent_posts(limit=10):
    """
    최신 발행된 글 목록을 가져옵니다.
    :param limit: 가져올 글 개수
    :return: 글 목록 리스트 (Dictionary: id, title, date, link)
    """
    site_url = os.getenv("WP_URL")
    if not site_url:
        return []

    endpoint = f"{site_url}/wp-json/wp/v2/posts"
    params = {
        'per_page': limit,
        'status': 'publish',
        'orderby': 'date',
        'order': 'desc'
    }
    
    headers = get_auth_header()
    
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        if response.status_code == 200:
            posts = response.json()
            results = []
            for p in posts:
                results.append({
                    'id': p.get('id'),
                    'title': p.get('title', {}).get('rendered', '제목 없음'),
                    'date': p.get('date'),
                    'link': p.get('link')
                })
            return results
        else:
            print(f"❌ 글 목록 조회 실패: {response.text}")
            return []
    except Exception as e:
        print(f"❌ 글 목록 조회 중 에러: {e}")
        return []

def ensure_category(category_name):
    """
    워드프레스에 카테고리가 존재하는지 확인하고, 없으면 생성합니다.
    :param category_name: 카테고리 이름 (예: 'stock')
    :return: 카테고리 ID (int) 또는 None
    """
    site_url = os.getenv("WP_URL")
    if not site_url: return None
    
    headers = get_auth_header()
    
    # 1. 검색
    try:
        search_url = f"{site_url}/wp-json/wp/v2/categories"
        params = {'search': category_name}
        
        resp = requests.get(search_url, headers=headers, params=params)
        if resp.status_code == 200:
            categories = resp.json()
            for cat in categories:
                if cat['name'].lower() == category_name.lower():
                    print(f"[Category] 기존 카테고리 '{category_name}' 찾음 (ID: {cat['id']})")
                    return cat['id']
    except Exception as e:
        print(f"[Category] 검색 실패: {e}")
        
    # 2. 생성 (없으면)
    print(f"[Category] 카테고리 '{category_name}' 생성 시도...")
    try:
        create_url = f"{site_url}/wp-json/wp/v2/categories"
        data = {'name': category_name}
        resp = requests.post(create_url, headers=headers, json=data)
        
        if resp.status_code == 201:
            new_cat = resp.json()
            print(f"[Category] '{category_name}' 생성 완료 (ID: {new_cat['id']})")
            return new_cat['id']
        else:
            print(f"[Category] 생성 실패: {resp.text}")
            return None
    except Exception as e:
        print(f"[Category] 생성 중 에러: {e}")
        return None
