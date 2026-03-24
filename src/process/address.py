from pathlib import Path
from db.db import get_connection

DATA_DIR = Path("./src/data").resolve()


def importRawAddress():
    file_path = DATA_DIR / "주소원본.csv"
    import csv

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS car_park.address(
                        address_code varchar(10) not null comment '법정동 코드',
                        sd_name varchar(100) not null comment '시/도 이름',
                        ssg_name varchar(100) not null comment '시/군/구 이름',
                        gemd_name varchar(100) not null comment '구/읍/면/동 이름',
                        CONSTRAINT pk_address PRIMARY KEY (address_code),
                        CONSTRAINT uk_address UNIQUE KEY (sd_name, ssg_name, gemd_name)
                    ) ENGINE=INNODB COMMENT '주소';
                """)

            with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csvfile:
                reader = csv.DictReader(csvfile)

                if reader.fieldnames is None:
                    raise ValueError("CSV 파일에 헤더(첫 줄)가 없습니다.")

                with conn.cursor() as cursor:
                    for row in reader:
                        if row['is_use'] == '존재':
                            full_address = row['value']
                            parts = full_address.split(" ")
                            if len(parts) == 0:
                                continue

                            sd = parts[0]
                            ssg = parts[1] if len(parts) > 1 else ''
                            gemd = parts[2] if len(parts) > 2 else ''

                            cursor.execute(
                                "INSERT IGNORE INTO address(address_code, sd_name, ssg_name, gemd_name) VALUES(%s,%s,%s,%s)",
                                (row['code'], sd, ssg, gemd)
                            )
    except Exception as e:
        print(f"importRawAddress 오류: {e}")
        raise


def mapping_parking_lot():
    with get_connection() as conn:
        # address_code 컬럼 추가 (이미 존재하면 무시)
        try:
            with conn.cursor() as cursor:
                cursor.execute("ALTER TABLE parking_lot ADD COLUMN address_code varchar(11)")
        except Exception:
            pass  # 컬럼이 이미 존재하는 경우 무시

        with conn.cursor() as cursor:
            offset = 0
            limit = 1000
            while True:
                cursor.execute(
                    "SELECT pl_id, base_address FROM parking_lot LIMIT %s OFFSET %s",
                    (limit, offset)
                )
                rows = cursor.fetchall()
                if not rows:
                    break

                for row in rows:
                    if len(row) < 2:
                        continue
                    parts = row[1].split(" ")
                    if parts[0] == "강원도":
                        parts[0] = "강원특별자치도"

                    while len(parts) < 3:
                        parts.append('')

                    try:
                        cursor.execute(
                            "SELECT address_code FROM address WHERE sd_name=%s AND ssg_name=%s AND gemd_name=%s",
                            (parts[0], parts[1], parts[2])
                        )
                        upd_row = cursor.fetchone()
                        if upd_row:
                            cursor.execute(
                                "UPDATE parking_lot SET address_code=%s WHERE pl_id=%s",
                                (upd_row[0], row[0])
                            )
                    except Exception as e:
                        print(f"주소 매핑 오류 (pl_id={row[0]}): {e}")

                offset += limit
