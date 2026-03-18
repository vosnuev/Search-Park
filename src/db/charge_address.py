import pymysql

# ---------------- DB 연결 ----------------
conn = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='0630',
    database='car_park',
    charset='utf8mb4'
)

cursor = conn.cursor(pymysql.cursors.DictCursor)

# ---------------- address 테이블 로드 ----------------
cursor.execute("""
SELECT address_code, sd_name, ssg_name, gemd_name
FROM address
WHERE gemd_name IS NOT NULL
  AND TRIM(gemd_name) <> ''
  AND gemd_name <> '전체'
  AND ssg_name IS NOT NULL
  AND TRIM(ssg_name) <> ''
  AND ssg_name <> '전체'
""")

address_list = cursor.fetchall()
print("address 로드 완료:", len(address_list))

# ---------------- ev_charger_info 조회 ----------------
cursor.execute("""
SELECT ev_id, road_address
FROM ev_charger_info
WHERE address_code IS NULL
""")

rows = cursor.fetchall()
print("매핑 대상:", len(rows))

# ---------------- 매핑 함수 ----------------
def find_address_candidates(road_address):
    candidates = []

    for addr in address_list:
        ssg = str(addr["ssg_name"]).strip()
        gemd = str(addr["gemd_name"]).strip()
        sd = str(addr["sd_name"]).strip() if addr["sd_name"] else ""

        # 시도 + 시군구 + 읍면동까지 있으면 가장 좋음
        if sd and ssg and gemd:
            if sd in road_address and ssg in road_address and gemd in road_address:
                candidates.append(addr)
                continue

        # 시군구 + 읍면동 매칭
        if ssg and gemd:
            if ssg in road_address and gemd in road_address:
                candidates.append(addr)

    return candidates

# ---------------- UPDATE ----------------
update_count = 0
skip_count = 0
multi_count = 0

for row in rows:
    road_address = str(row["road_address"]).strip()
    candidates = find_address_candidates(road_address)

    if len(candidates) == 1:
        code = candidates[0]["address_code"]

        cursor.execute("""
        UPDATE ev_charger_info
        SET address_code = %s
        WHERE ev_id = %s
        """, (code, row["ev_id"]))

        update_count += 1

    elif len(candidates) == 0:
        skip_count += 1
        print(f"[매핑실패] ev_id={row['ev_id']} / 주소={road_address}")

    else:
        multi_count += 1
        print(f"[중복후보] ev_id={row['ev_id']} / 주소={road_address}")
        print("후보:", [(c["address_code"], c["ssg_name"], c["gemd_name"]) for c in candidates[:5]])

conn.commit()

print("업데이트 완료:", update_count)
print("매핑 실패:", skip_count)
print("중복 후보:", multi_count)

cursor.close()
conn.close()