import mysql.connector
import os
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트에서 자동 탐색)
load_dotenv()

Conn = mysql.connector.connect(
    host=os.getenv('DB_HOST','localhost'),
    port=os.getenv('DB_PORT', 3306),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME', 'car_park')
)

def init_review_table():
    with Conn.cursor() as cursor:
        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS n_pkreviews (
                            category_code  INT             NOT NULL AUTO_INCREMENT COMMENT '카테고리코드',  -- 리뷰 고유 ID (자동 증가)
                            pk_code        VARCHAR(255)    NOT NULL COMMENT '주차장코드',                   -- 주차장 코드 (parking_lots 참조용)
                            pk_name        VARCHAR(255)    NOT NULL COMMENT '주차장이름',                   -- 주차장 이름
                            pk_address     VARCHAR(255)    NOT NULL COMMENT '주소',                        -- 지역 (주소 전체)
                            review_txt     TEXT            NOT NULL COMMENT '리뷰',                        -- 댓글 텍스트
                            review_date    VARCHAR(20)     DEFAULT NULL COMMENT '리뷰날짜',                 -- 리뷰 날짜 (네이버 표기 그대로, 예: 25.3.17.월)
                            crawled_at     DATETIME        NOT NULL DEFAULT NOW(),                         -- 수집 시각 (크롤링한 시간)
                            PRIMARY KEY (category_code)
                        ) ENGINE=InnoDB
                        DEFAULT CHARSET=utf8mb4
                        COMMENT='네이버_주차장_리뷰_수집_테이블';
                       """)
    Conn.commit()