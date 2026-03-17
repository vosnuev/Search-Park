import csv
from db.db import Conn


def safe_time(value):
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    return value


def create_operation_time_table():
    cursor = Conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operation_time (
        pl_id VARCHAR(50) NOT NULL,
        op_type ENUM('평일', '토요일', '공휴일') NOT NULL,
        start_time TIME,
        end_time TIME,
        PRIMARY KEY (pl_id, op_type),
        CONSTRAINT fk_operation_time_parking_lot
            FOREIGN KEY (pl_id) REFERENCES parking_lot(pl_id)
    )
    """)

    Conn.commit()
    cursor.close()


def parse_operation_time_rows(csv_path):
    operation_rows = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # 헤더 스킵

        for row in reader:
            try:
                pl_id = row[0]

                weekday_start = safe_time(row[10])   # 평일운영시작시각
                weekday_end = safe_time(row[11])     # 평일운영종료시각
                saturday_start = safe_time(row[12])  # 토요일운영시작시각
                saturday_end = safe_time(row[13])    # 토요일운영종료시각
                holiday_start = safe_time(row[14])   # 공휴일운영시작시각
                holiday_end = safe_time(row[15])     # 공휴일운영종료시각

                operation_rows.append((pl_id, '평일', weekday_start, weekday_end))
                operation_rows.append((pl_id, '토요일', saturday_start, saturday_end))
                operation_rows.append((pl_id, '공휴일', holiday_start, holiday_end))

            except Exception as e:
                print("에러 row:", row, e)

    return list(set(operation_rows))


def load_operation_time_data(csv_path):
    cursor = Conn.cursor()

    operation_rows = parse_operation_time_rows(csv_path)
    print("삽입할 운영시간 데이터 개수:", len(operation_rows))

    sql = """
    INSERT IGNORE INTO operation_time (
        pl_id, op_type, start_time, end_time
    )
    VALUES (%s, %s, %s, %s)
    """

    cursor.executemany(sql, operation_rows)
    Conn.commit()

    print("operation_time insert 완료")

    cursor.close()


def run(csv_path):
    create_operation_time_table()
    load_operation_time_data(csv_path)


if __name__ == "__main__":
    run('./src/data/전국주차장정보표준데이터_1.csv')