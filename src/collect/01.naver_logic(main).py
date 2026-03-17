from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pymysql
import time
import importlib.util
import os

# 현재 파일이 있는 폴더 기준으로 경로 자동 설정
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "03.naver_models.py")    # 파일경로 설정

spec   = importlib.util.spec_from_file_location("naver_models", MODEL_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

fetch_reviews_from_naver = module.fetch_reviews_from_naver
save_reviews_to_db       = module.save_reviews_to_db

# ================================================
# DB 연결 설정
# ================================================
# [읽기용] 다른 사람 DB - 주차장 이름/주소 가져오는 곳
SOURCE_DB = dict(
    host='127.0.0.1',
    port=3306,
    user='vosnuevo',
    password='vosnuevo',
    database='car_park',   # ← 가져올 DB 이름
    charset='utf8mb4'
)

# [저장용] 내 DB - 크롤링 결과 저장하는 곳
TARGET_DB = dict(
    host='127.0.0.1',
    port=3306,
    user='vosnuevo',
    password='vosnuevo',
    database='car_park',    # ← 저장할 DB 이름
    charset='utf8mb4'
)

# ================================================
# 메인 실행
# ================================================
if __name__ == "__main__":

    # 1. 다른 사람 DB에서 주차장 목록 가져오기
    source_conn = pymysql.connect(**SOURCE_DB)
    try:
        with source_conn.cursor() as cursor:
            cursor.execute("SELECT pk_code, pk_name, pk_address FROM ex_pklots")      # ← from 가져올 table 이름 
            parking_list = [
                {"pk_code": row[0], "pk_name": row[1], "pk_address": row[2]}
                for row in cursor.fetchall()
            ]
    finally:
        source_conn.close()

    print("수집할 주차장 목록:")
    for p in parking_list:
        print(f"  [{p['pk_code']}] {p['pk_name']} / {p['pk_address']}")

    # 2. 브라우저 실행
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    driver.get("https://map.naver.com/p?c=15.00,0,0,0,dh")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input.input_search"))
    )

    # 3. 주차장마다 크롤링 → DB 저장
    total_count = 0
    for parking in parking_list:
        print(f"\n검색 중: [{parking['pk_code']}] {parking['pk_name']}")

        reviews = fetch_reviews_from_naver(   # ← models에서 가져온 함수
            driver,
            parking['pk_code'],
            parking['pk_name'],
            parking['pk_address']
        )

        save_reviews_to_db(reviews, TARGET_DB)   # ← models에서 가져온 함수
        total_count += len(reviews)
        time.sleep(1)

    # 4. 브라우저 종료
    driver.quit()
    print(f"\n✅ 전체 완료! 총 {total_count}개 리뷰 수집 및 저장됨")