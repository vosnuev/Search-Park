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