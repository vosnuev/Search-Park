from dataclasses import dataclass, field
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pymysql
import time
import re


# ================================================
# 1. 데이터 클래스 - 리뷰 1건을 담는 그릇
# ================================================
@dataclass
class NaverReview:
    """
    네이버 지도에서 수집한 주차장 리뷰 1건을 담는 클래스.
    car_park.n_pkreviews 테이블의 컬럼과 1:1 대응됨.

    사용 예시:
        review = NaverReview(
            pk_code=1,
            pk_name="강남공영주차장",
            pk_address="서울 관악구 신림동 1675-8",
            review_txt="편해요",
            review_date="24.2.8.목"
        )
    """
    pk_code    : int
    pk_name    : str
    pk_address : str
    review_txt : str
    review_date: str = ""
    crawled_at : datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """DB INSERT에 쓸 딕셔너리로 변환"""
        return {
            "pk_code"    : self.pk_code,
            "pk_name"    : self.pk_name,
            "pk_address" : self.pk_address,
            "review_txt" : self.review_txt,
            "review_date": self.review_date,
            "crawled_at" : self.crawled_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __str__(self):
        return (
            f"[{self.pk_code}] {self.pk_name} | "
            f"{self.review_date} | {self.review_txt[:20]}"
        )


# ================================================
# 2. 주소 정규화 함수
# ================================================
def normalize_address(addr: str) -> str:
    """서울특별시 → 서울 등 광역시/특별시 정규화"""
    addr = addr.strip()
    addr = re.sub(r'서울특별시', '서울', addr)
    addr = re.sub(r'부산광역시', '부산', addr)
    addr = re.sub(r'대구광역시', '대구', addr)
    addr = re.sub(r'인천광역시', '인천', addr)
    addr = re.sub(r'광주광역시', '광주', addr)
    addr = re.sub(r'대전광역시', '대전', addr)
    addr = re.sub(r'울산광역시', '울산', addr)
    return addr.strip()


def is_address_match(db_addr: str, naver_addr: str) -> bool:
    """주소 일치 확인 - 정규화 후 텍스트 + 숫자까지 비교"""
    db_norm    = normalize_address(db_addr)
    naver_norm = normalize_address(naver_addr)
    text_match    = (db_norm in naver_norm or naver_norm in db_norm)
    db_numbers    = re.findall(r'\d+', db_norm)
    naver_numbers = re.findall(r'\d+', naver_norm)
    numbers_match = all(n in naver_numbers for n in db_numbers) if db_numbers else True
    return text_match and numbers_match


# ================================================
# 3. 검색창 초기화 함수
# ================================================
def clear_search_box(driver, search_box):
    """네이버 지도 검색창을 완전히 비우는 함수"""
    search_box.click()
    search_box.send_keys(Keys.CONTROL + "a")
    search_box.send_keys(Keys.DELETE)
    time.sleep(0.3)
    current_value = search_box.get_attribute("value")
    if current_value:
        driver.execute_script("""
            var input = arguments[0];
            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            nativeInputValueSetter.call(input, '');
            input.dispatchEvent(new Event('input', { bubbles: true }));
        """, search_box)
        time.sleep(0.3)


# ================================================
# 4. 크롤링 함수 - NaverReview 객체 리스트 반환
# ================================================
def fetch_reviews_from_naver(driver, pk_code: int, parking_name: str, parking_address: str) -> list:
    """
    네이버 지도에서 주차장 리뷰를 크롤링해서
    NaverReview 객체 리스트로 반환하는 함수
    """
    wait    = WebDriverWait(driver, 10)
    results = []

    try:
        # [STEP 1] 메인 컨텍스트 초기화
        driver.switch_to.default_content()

        # [STEP 2] 검색창 입력
        search_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.input_search"))
        )
        clear_search_box(driver, search_box)
        search_box.send_keys(parking_name)
        time.sleep(0.3)

        # [STEP 3] 입력값 검증
        if search_box.get_attribute("value") != parking_name:
            clear_search_box(driver, search_box)
            search_box.send_keys(parking_name)
            time.sleep(0.3)

        search_box.send_keys(Keys.ENTER)
        time.sleep(2)

        # [STEP 4] searchIframe 전환 + 검색결과 로딩 대기
        driver.switch_to.frame("searchIframe")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.VLTHu")))
        result_items = driver.find_elements(By.CSS_SELECTOR, "li.VLTHu")

        # [STEP 5] 이름 일치 후보 수집
        candidate_links = []
        for item in result_items:
            try:
                name_text = item.find_element(By.CSS_SELECTOR, "span.YwYLL").text.strip()
                link_el   = item.find_element(By.CSS_SELECTOR, "a.U70Fj")
                if name_text == parking_name.strip():
                    candidate_links.append(link_el)
                    print(f"  이름 일치: [{name_text}]")
            except:
                continue

        if not candidate_links:
            print(f"  [{parking_name}] 이름 일치 없음 → 첫 번째 결과 사용")
            candidate_links = [result_items[0].find_element(By.CSS_SELECTOR, "a.U70Fj")]

        # [STEP 6] 후보 클릭 → entryIframe에서 주소 검증
        target_confirmed = False
        for idx, link in enumerate(candidate_links):
            print(f"  [{parking_name}] {idx+1}번째 후보 클릭")

            driver.switch_to.default_content()
            driver.switch_to.frame("searchIframe")
            driver.execute_script("arguments[0].click();", link)
            time.sleep(3)

            driver.switch_to.default_content()
            driver.switch_to.frame("entryIframe")

            try:
                pz7wy_els       = driver.find_elements(By.CSS_SELECTOR, "span.pz7wy")
                naver_addresses = [
                    el.text.strip().rstrip(',').strip()
                    for el in pz7wy_els if el.text.strip()
                ]
                print(f"  네이버 주소: {naver_addresses}")
            except:
                naver_addresses = []

            if any(is_address_match(parking_address, na) for na in naver_addresses):
                print(f"  [{parking_name}] ✅ 주소 일치!")
                target_confirmed = True
                break
            else:
                print(f"  [{parking_name}] ❌ 주소 불일치 → 다음 후보")

        if not target_confirmed:
            print(f"  [{parking_name}] ⚠️ 주소 일치 없음 → 마지막 결과로 진행")

        # [STEP 7] entryIframe 재진입
        driver.switch_to.default_content()
        driver.switch_to.frame("entryIframe")

        # [STEP 8] 리뷰 탭 찾기 및 클릭
        try:
            all_tabs  = driver.find_elements(By.CSS_SELECTOR, "a.tpj9w span.I2hj8")
            tab_texts = [t.text for t in all_tabs]
            print(f"  [{parking_name}] 탭 목록: {tab_texts}")

            if "리뷰" not in tab_texts:
                print(f"  [{parking_name}] 리뷰 탭 없음 → 스킵")
                return results

            review_span = next((s for s in all_tabs if s.text.strip() == "리뷰"), None)
            if review_span is None:
                return results

            review_tab = driver.execute_script(
                "return arguments[0].closest('a.tpj9w');", review_span
            )
            driver.execute_script("arguments[0].click();", review_tab)
            time.sleep(2)

            try:
                wait.until(EC.presence_of_element_located((By.ID, "_review_list")))
                print(f"  [{parking_name}] 리뷰 목록 로딩 완료")
            except:
                print(f"  [{parking_name}] 리뷰 목록 로딩 실패 → 스킵")
                return results

        except Exception as e:
            print(f"  [{parking_name}] 리뷰 탭 오류: {e}")
            return results

        # [STEP 9] 리뷰 수집 → NaverReview 객체로 변환
        collected = set()

        while True:
            try:
                review_list = driver.find_element(By.ID, "_review_list")
            except:
                break

            cards = review_list.find_elements(By.CSS_SELECTOR, "li.EjjAW")
            if not cards:
                break

            for card in cards:
                try:
                    comment = card.find_element(
                        By.CSS_SELECTOR, "a[data-pui-click-code='rvshowmore']"
                    ).text.strip()
                except:
                    comment = ""

                try:
                    review_date = card.find_element(
                        By.CSS_SELECTOR, "time[aria-hidden='true']"
                    ).text.strip()
                except:
                    review_date = ""

                key = (comment, review_date)
                if comment and key not in collected:
                    collected.add(key)
                    results.append(NaverReview(
                        pk_code     = pk_code,
                        pk_name     = parking_name,
                        pk_address  = parking_address,
                        review_txt  = comment,
                        review_date = review_date
                    ))

            try:
                more_btn = driver.find_element(
                    By.XPATH, "//a[contains(text(),'더보기') or contains(text(),'리뷰 더보기')]"
                )
                driver.execute_script("arguments[0].click();", more_btn)
                wait.until(EC.presence_of_element_located((By.ID, "_review_list")))
            except:
                break

        print(f"  [{parking_name}] {len(results)}개 리뷰 수집 완료")

    except Exception as e:
        print(f"  [{parking_name}] 오류: {e}")

    finally:
        driver.switch_to.default_content()

    return results


# ================================================
# 5. DB 저장 함수
# ================================================
def save_reviews_to_db(reviews: list, db_config: dict):
    """
    수집한 NaverReview 객체 리스트를
    car_park.n_pkreviews 테이블에 저장하는 함수.                                # ← 가져올 table 이름 
    중복은 INSERT IGNORE로 무시.
    """
    if not reviews:
        print("  저장할 리뷰가 없습니다.")
        return

    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:       
            sql = """                                
                INSERT IGNORE INTO n_pkreviews                               # ← 가져올 table 이름 
                    (pk_code, pk_name, pk_address, review_txt, review_date, crawled_at)
                VALUES
                    (%(pk_code)s, %(pk_name)s, %(pk_address)s,
                     %(review_txt)s, %(review_date)s, %(crawled_at)s)
            """
            for review in reviews:
                cursor.execute(sql, review.to_dict())
        conn.commit()
        print(f"  ✅ {len(reviews)}개 DB 저장 완료")
    except Exception as e:
        conn.rollback()
        print(f"  ❌ DB 저장 실패: {e}")
    finally:
        conn.close()