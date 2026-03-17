import csv
import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="0630"
)

cursor = conn.cursor()

cursor.execute("USE car_park")

cursor.execute("""
CREATE TABLE IF NOT EXISTS parking_lot (
    `pl_id` varchar(50) NOT NULL,
    `pl_name` varchar(255) ,
    `pl_geom` point ,
    `is_free` boolean ,
    `capacity` int ,
    `road_address` varchar(255) ,
    `base_address` varchar(255) ,
    `is_public` boolean,
    `etc` text ,
    `pl_type` varchar(10) ,
    `has_priority` boolean ,
    `op_days` varchar(50) ,
    `base_time` DECIMAL(10,2),
    `base_fee` int,
    `unit_time` DECIMAL(10,2),
    `unit_fee` int,
    PRIMARY KEY (pl_id)
)
""")

rows = []

with open('./src/data/전국주차장정보표준데이터_1.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)

    def safe_int(value):
        try:
            return int(value)
        except:
            return None

    def safe_float(value):
        try:
            return float(value)
        except:
            return None

    for row in reader:
        try:
            # 좌표 없으면 skip
            if not row[28] or not row[29]:
                continue

            lat = safe_float(row[28])
            lon = safe_float(row[29])

            if lat is None or lon is None:
                continue

            point = f"POINT({lon} {lat})"

            is_free = 1 if "무료" in row[16] else 0
            is_public = 1 if row[2] == "공영" else 0
            has_priority = 1 if row[30] == "Y" else 0

            new_row = (
                row[0],                      # pl_id
                row[1],                      # pl_name
                point,
                is_free,
                safe_int(row[6]),            # capacity
                row[4],                      # road_address
                row[5],                     # base_address
                is_public,
                row[25],                     # etc
                row[3],                      # pl_type
                has_priority,
                row[9],                      # op_days
                safe_float(row[17]),         # base_time
                safe_int(row[18]),           # base_fee
                safe_float(row[19]),         # unit_time
                safe_int(row[20])            # unit_fee 
            )

            rows.append(new_row)

        except Exception as e:
            print("에러 row:", row, e)
sql = """
INSERT IGNORE INTO parking_lot (
    pl_id, pl_name, pl_geom, is_free, capacity,
    road_address, base_address, is_public, etc,
    pl_type, has_priority, op_days,
    base_time, base_fee, unit_time, unit_fee
)
VALUES (
    %s, %s, ST_GeomFromText(%s), %s, %s,
    %s, %s, %s, %s,
    %s, %s, %s,
    %s, %s, %s, %s
)
"""

cursor.executemany(sql, rows)
conn.commit()

cursor.close()
conn.close()