import csv
from db.db import get_connection


def create_payment_type_table():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_type (
                pl_id VARCHAR(50) NOT NULL,
                pay_name VARCHAR(20) NOT NULL,
                PRIMARY KEY (pl_id, pay_name),
                CONSTRAINT fk_payment_type_parking_lot
                    FOREIGN KEY (pl_id) REFERENCES parking_lot(pl_id)
            )
            """)


def parse_payment_rows(csv_path):
    payment_rows = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            try:
                pl_id = row[0]
                pay_raw = row[24].strip() if row[24] else ""

                if not pl_id or not pay_raw:
                    continue

                if "카드" in pay_raw:
                    payment_rows.append((pl_id, "카드"))
                if "현금" in pay_raw:
                    payment_rows.append((pl_id, "현금"))

            except Exception as e:
                print(f"파싱 오류 (row[0]={row[0] if row else '?'}): {e}")

    return list(set(payment_rows))


def load_payment_type_data(csv_path):
    payment_rows = parse_payment_rows(csv_path)
    print(f"삽입할 결제 데이터 개수: {len(payment_rows)}")

    sql = """
    INSERT IGNORE INTO payment_type (pl_id, pay_name)
    VALUES (%s, %s)
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(sql, payment_rows)

    print("payment_type insert 완료")


def run(csv_path):
    create_payment_type_table()
    load_payment_type_data(csv_path)


if __name__ == "__main__":
    run('./src/data/전국주차장정보표준데이터_1.csv')
