import mysql.connector
from mysql.connector import pooling
import os
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

_pool = pooling.MySQLConnectionPool(
    pool_name="car_park_pool",
    pool_size=5,
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 3306)),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME', 'car_park'),
)


@contextmanager
def get_connection():
    """커넥션 풀에서 연결을 가져와 사용 후 자동 반환하는 context manager.
    정상 종료 시 자동 commit, 예외 발생 시 자동 rollback."""
    conn = _pool.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()  # 풀에 반환


def init_review_table():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS n_pkreviews (
                    category_code  INT             NOT NULL AUTO_INCREMENT COMMENT '카테고리코드',
                    pk_code        VARCHAR(255)    NOT NULL COMMENT '주차장코드',
                    pk_name        VARCHAR(255)    NOT NULL COMMENT '주차장이름',
                    pk_address     VARCHAR(255)    NOT NULL COMMENT '주소',
                    review_txt     TEXT            NOT NULL COMMENT '리뷰',
                    review_date    VARCHAR(20)     DEFAULT NULL COMMENT '리뷰날짜',
                    crawled_at     DATETIME        NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (category_code)
                ) ENGINE=InnoDB
                DEFAULT CHARSET=utf8mb4
                COMMENT='네이버_주차장_리뷰_수집_테이블';
            """)
