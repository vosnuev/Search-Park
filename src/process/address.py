from pathlib import Path
from db.raw.raw_db import Conn
import csv

DATA_DIR = Path("./src/data").resolve()


def importRawAddress():
    # Fixme: 파일 경로 변경
    file_path = DATA_DIR / "주소원본.csv"
    try:
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile)

            if reader.fieldnames is None:
                raise ValueError("CSV 파일에 헤더(첫 줄)가 없습니다.")
            
            with Conn.cursor() as cursor:
                for row in reader:
                    sql = """
                        insert into address(address_code, val)
                        values(%s,%s)
                    """
                    if row['is_use'] == '존재':                        
                        cursor.execute(sql, (row['code'], row['value']))
                        print(row)
                
            Conn.commit()
    except Exception as e:
        print(e)
