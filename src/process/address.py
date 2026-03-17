from pathlib import Path
from db.db import Conn
import csv

DATA_DIR = Path("./src/data").resolve()

# 주소 데이터베이스 전처리
def importRawAddress():
    # Fixme: 파일 경로 변경
    file_path = DATA_DIR / "주소원본.csv"
    try:
        with Conn.cursor() as cursor:
            cursor.execute("""
                           create table if not exists car_park.address(
                                address_code varchar(10) not null comment '법정동 코드',
                                sd_name varchar(100) not null comment '시/도 이름',
                                ssg_name varchar(100) not null comment '시/군/구 이름',
                                gemd_name varchar(100) not null comment '구/읍/면/동 이름',
                                CONSTRAINT pk_address PRIMARY KEY (address_code),
                                CONSTRAINT uk_address UNIQUE KEY (sd_name, ssg_name, gemd_name)
                            ) ENGINE=INNODB COMMENT '주소';
                        """)
        Conn.commit()

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

def mapping_parking_lot():
    with Conn.cursor() as cursor:
        offset = 0
        limit = 1000
        while True:       
            sql = f"select pl_id, base_address from parking_lot limit {limit} offset {offset}"
            cursor.execute(sql)
            rows = cursor.fetchall()
            if not len(rows):
                break

            for row in rows:
                if len(row) < 2:
                    continue
                parts = row[1].split(" ")
                if parts[0] == "강원도":
                    parts[0] = "강원특별자치도"

                if len(parts) < 3:
                    for _ in range(3-len(parts)):
                        parts.append('')

                addr_sql = f"select address_code from address where sd_name='{parts[0]}' and ssg_name = '{parts[1]}' and gemd_name = '{parts[2]}'"
                cursor.execute(addr_sql)
                upd_row = cursor.fetchone()
                if upd_row:
                    if len(row) < 1:
                        continue
                    addr_code = upd_row[0]
                    upd_sql = f"update parking_lot set address_code = {addr_code} where pl_id = '{row[0]}'"
                    cursor.execute(upd_sql)
            offset += limit
        Conn.commit()
                
            
            
                

                
