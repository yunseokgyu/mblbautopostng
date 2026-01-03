import schedule
import time
import os
from dotenv import load_dotenv
from stock_bot import run_stock_job
from grant_bot import run_grant_job
from marketing_bot import run_marketing_job

# 환경 변수 로드
load_dotenv('credentials.env')

def run_schedule():
    print("🤖 자동화 시스템(지휘자) 가동 시작...")
    print(f"Target WordPress: {os.getenv('WP_URL')}")

    # 스케줄 설정
    schedule.every().day.at("07:00").do(run_stock_job)      # 아침 7시
    schedule.every().day.at("13:00").do(run_grant_job)      # 오후 1시
    schedule.every().day.at("18:00").do(run_marketing_job)  # 저녁 6시
    
    # 테스트를 위해 10초마다 실행되는 코드도 추가 (실제 운영시 삭제)
    # schedule.every(10).seconds.do(run_stock_job)

    print("🕒 스케줄 모니터링 중... (Ctrl+C로 종료)")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 시스템 종료")

if __name__ == "__main__":
    run_schedule()
