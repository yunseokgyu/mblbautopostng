
import grant_bot
import wp_utils
import sys

# Ensure UTF-8 encoding for Windows console (to avoid print errors)
sys.stdout.reconfigure(encoding='utf-8')

print("🚀 [TEST] 최신 공고 1건을 가져와서 이미지 첨부 테스트를 시작합니다...")

# 1. Fetch latest item
items = grant_bot.fetch_kstartup_announcements(limit=1)
if not items:
    print("⚠️ K-Startup 공고가 없어서 수출바우처로 시도합니다.")
    items = grant_bot.fetch_exportvoucher_announcements(limit=1)

if not items:
    print("❌ 테스트할 공고를 찾지 못했습니다.")
    sys.exit(1)

target_item = items[0]
print(f"✅ 테스트 대상: {target_item['title']}")

# 2. Modify Title for Test
# process_grant_item uses the title to generate the post title.
# We want to make sure it looks like a test.
# However, process_grant_item constructs title as "[{category_tag}] {title} - 전문가 분석"
# So we will just use a special category tag.

# 3. Get Category
cat_id = wp_utils.ensure_category("System Test")
cat_ids = [cat_id] if cat_id else []

# 4. Process (Force Post)
print("📸 process_grant_item 실행 (이미지 검색 및 Cloudinary 업로드 포함)...")
grant_bot.process_grant_item(
    item=target_item, 
    category_tag="TEST_VERIFY",  # This will appear in the title: [TEST_VERIFY] ...
    dry_run=False, 
    cat_ids=cat_ids
)

print("🏁 테스트 종료. 워드프레스를 확인하세요.")
