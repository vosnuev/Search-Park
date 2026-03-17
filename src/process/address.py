from pathlib import Path
from db.db import Conn
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
                        insert ignore into address(address_code, sd_name, ssg_name, gemd_name)
                        values(%s,%s,%s,%s)
                    """
                    if row['is_use'] == '존재':
                        full_address = row['value']
                        parts = full_address.split(" ")
                        if len(parts) == 0:
                            continue

                        sd = parts[0]
                        ssg = ''
                        gemd = ''
                        if len(parts) > 1:
                            ssg = parts[1]
                        if len(parts) > 2:
                            gemd = parts[2]

                        cursor.execute(sql, (row['code'],sd, ssg, gemd))
            Conn.commit()
    except Exception as e:
        print(e)
