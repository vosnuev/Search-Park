import csv
from db.db import get_connection


def safe_time(value):
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def create_operation_time_table():
    with get_connection() as conn:
        with conn.cursor() as cursor:
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


def parse_operation_time_rows(csv_path):
    operation_rows = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            try:
                pl_id = row[0]
                weekday_start  = safe_time(row[10])
                weekday_end    = safe_time(row[11])
                saturday_start = safe_time(row[12])
                saturday_end   = safe_time(row[13])
                holiday_start  = safe_time(row[14])
                holiday_end    = safe_time(row[15])

                operation_rows.append((pl_id, '평일',   weekday_start,  weekday_end))
                operation_rows.append((pl_id, '토요일', saturday_start, saturday_end))
                operation_rows.append((pl_id, '공휴일', holiday_start,  holiday_end))

            except Exception as e:
                print(f"파싱 오류 (row[0]={row[0] if row else '?'}): {e}")

    return list(set(operation_rows))


def load_operation_time_data(csv_path):
    operation_rows = parse_operation_time_rows(csv_path)
    print(f"삽입할 운영시간 데이터 개수: {len(operation_rows)}")

    sql = """
    INSERT IGNORE INTO operation_time (pl_id, op_type, start_time, end_time)
    VALUES (%s, %s, %s, %s)
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(sql, operation_rows)

    print("operation_time insert 완료")


def run(csv_path):
    create_operation_time_table()
    load_operation_time_data(csv_path)


if __name__ == "__main__":
    run('./src/data/전국주차장정보표준데이터_1.csv')
