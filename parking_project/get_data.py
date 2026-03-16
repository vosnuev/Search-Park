import requests
import pymysql

url = "http://apis.data.go.kr/B553881/Parking/PrkSttusInfo"

params = {
"serviceKey": "804ec72db7947bff79f52f9af78103873f832ba3537765d56762f1f0210f48ea",
"pageNo": 1,
"numOfRows": 10,
"format": 2
}

response = requests.get(url, params=params)

data = response.json()

items = data["PrkRealtimeInfo"]

conn = pymysql.connect(
   host="localhost",
   user="root",
   password="1234",
   database="parking_db"
)

cursor = conn.cursor()

for item in items:
    prk_center_id = item["prk_center_id"]
    total = item["pkfc_ParkingLots_total"]
    available = item["pkfc_Available_ParkingLots_total"]

sql = """
INSERT INTO parking_realtime
(prk_center_id, total_lots, available_lots)
VALUES (%s, %s, %s)
"""

cursor.execute(sql, (prk_center_id, total, available))

conn.commit()
conn.close()

print("데이터 저장 완료") 