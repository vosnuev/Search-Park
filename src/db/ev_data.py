import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path


def main():
    # ===== 1) DB 접속 정보 수정 =====
    DB_USER = "root"
    DB_PASSWORD = "0630"
    DB_HOST = "127.0.0.1"
    DB_PORT = "3306"
    DB_NAME = "car_park"

    # ===== 2) 엑셀 파일 경로 =====
    # 이 파일(.py)과 같은 폴더에 data/ev_charger.xlsx 가 있다고 가정
    BASE_DIR = Path(__file__).resolve().parent
    file_path = r"./src/data/전기차 충전소 설치현황_20260318.xlsx"


    # ===== 3) MySQL 엔진 생성 =====
    engine = create_engine(
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )

    # ===== 4) 엑셀 읽기 =====
    # 첫 줄은 제목이라 skiprows=1
    df = pd.read_excel(file_path, skiprows=1)

    # 컬럼명 정리
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\n", "", regex=False)
        .str.replace("\r", "", regex=False)
    )

    print("현재 컬럼명:", df.columns.tolist())

    # ===== 5) 컬럼명 변경 =====
    # 엑셀 컬럼명에 맞게 rename
    df = df.rename(columns={
        "시구": "region_name",
        "설치장소": "station_name",
        "주소": "road_address",
        "급속충전기(대)": "fast_cnt",
        "완속충전기(대)": "slow_cnt",
        "지원차종": "support_car"
    })

    required_cols = [
        "region_name",
        "station_name",
        "road_address",
        "fast_cnt",
        "slow_cnt",
        "support_car"
    ]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"필요한 컬럼이 없습니다: {missing_cols}\n"
            f"현재 컬럼: {df.columns.tolist()}"
        )

    # 필요한 컬럼만 선택
    df = df[required_cols].copy()

    # ===== 6) 데이터 정리 =====
    df["region_name"] = df["region_name"].fillna("").astype(str).str.strip()
    df["station_name"] = df["station_name"].fillna("").astype(str).str.strip()
    df["road_address"] = df["road_address"].fillna("").astype(str).str.strip()
    df["support_car"] = df["support_car"].fillna("").astype(str).str.strip()

    df["fast_cnt"] = pd.to_numeric(df["fast_cnt"], errors="coerce").fillna(0).astype(int)
    df["slow_cnt"] = pd.to_numeric(df["slow_cnt"], errors="coerce").fillna(0).astype(int)

    # 불필요한 행 제거
    df = df[df["station_name"] != ""]
    df = df[df["road_address"] != ""]

    print(f"정제 후 데이터 개수: {len(df)}")
    print(df.head())

    # ===== 7) 테이블 생성 =====
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS ev_charger_info (
        charger_id INT AUTO_INCREMENT PRIMARY KEY,
        region_name VARCHAR(100),
        station_name VARCHAR(200),
        road_address VARCHAR(255),
        fast_cnt INT,
        slow_cnt INT,
        support_car TEXT
    );
    """

    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()

    # ===== 8) 데이터 적재 =====
    # replace: 기존 테이블 덮어쓰기
    # append: 기존 테이블에 이어붙이기
    df.to_sql(
        name="ev_charger_info",
        con=engine,
        if_exists="replace",
        index=False
    )

    print("ev_charger_info 테이블 생성 및 데이터 적재 완료")


if __name__ == "__main__":
    main()