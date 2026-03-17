"""
자동차 등록 현황 정제 스크립트

처리 내용:
1. sigungu 컬럼에서 ssg_name, gemd_name 분리
   예) "전주시 덕진구" → ssg_name="전주시", gemd_name="덕진구"
       "강남구"        → ssg_name="강남구", gemd_name=""
2. sd_name 을 address 테이블 기준으로 변환
   예) "서울" → "서울특별시"
3. 예외처리
   - 세종: ssg_name, gemd_name 을 "" 로 처리
   - 경북 군위군: 대구광역시로 편입, 대구 데이터 이미 존재 → 제외
   - 충북 청원군: 청주시로 통합 → 제외
4. car_park.address 에서 address_code 매칭
5. car_park.car_registration 에 적재
"""

import pandas as pd
import pymysql
from sqlalchemy import create_engine, text

# ════════════════════════════════════════════
# ✏️  여기만 수정하세요
# ════════════════════════════════════════════
DB_USER     = "root"
DB_PASSWORD = "1234"
DB_HOST     = "localhost"
DB_PORT     = 3306
# ════════════════════════════════════════════

# 시도명 변환 매핑
SD_NAME_MAP = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
    "강원": "강원특별자치도",
    "전북": "전북특별자치도",
}


def split_sigungu(sigungu):
    """
    sigungu 값에서 ssg_name, gemd_name 분리
    "전주시 덕진구" → ("전주시", "덕진구")
    "강남구"        → ("강남구", "")
    """
    parts = sigungu.strip().split(" ")
    if len(parts) == 1:
        return parts[0], ""
    else:
        return parts[0], parts[-1]


def apply_exceptions(sido, ssg_name, gemd_name):
    """
    예외처리
    반환값: (sd_name 오버라이드, ssg_name, gemd_name)
    None, None, None 반환 시 해당 행 제외
    """
    # 세종 예외처리: ssg_name, gemd_name 을 "" 로 처리
    if sido == "세종":
        return "세종특별자치시", "", ""

    # 경북 군위군 → 대구광역시로 편입
    # 단, 대구 군위군 데이터가 이미 있으므로 제외
    if sido == "경북" and ssg_name == "군위군":
        return None, None, None

    # 충북 청원군 → 청주시로 통합, 매칭 불가 → 제외
    if sido == "충북" and ssg_name == "청원군":
        return None, None, None

    return None, ssg_name, gemd_name


def load_raw_data():
    df = pd.read_csv(
        "src/data/자동차등록현황보고_자동차등록대수현황 시도별 (202602).txt",
        encoding="utf-8", sep="\t", header=None, skiprows=2
    )
    df.columns = [
        "reg_month", "sido", "sigungu",
        "sedan_gov", "sedan_prv", "sedan_com", "sedan_tot",
        "van_gov", "van_prv", "van_com", "van_tot",
        "truck_gov", "truck_prv", "truck_com", "truck_tot",
        "spec_gov", "spec_prv", "spec_com", "spec_tot",
        "total_gov", "total_prv", "total_com", "total_tot"
    ]
    df = df[df["sigungu"].str.strip() != "계"].copy()

    # 숫자 컬럼 쉼표 제거 후 정수 변환  ← 이거 추가!
    for col in df.columns[3:]:
        df[col] = df[col].apply(lambda x: int(str(x).replace(",", "").strip()))

    return df


def get_address_code(engine, sd_name, ssg_name, gemd_name):
    """car_park.address 에서 address_code 조회"""
    query = text("""
        SELECT address_code
        FROM car_park.address
        WHERE sd_name   = :sd_name
          AND ssg_name  = :ssg_name
          AND gemd_name = :gemd_name
        LIMIT 1
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {
            "sd_name":   sd_name,
            "ssg_name":  ssg_name,
            "gemd_name": gemd_name
        }).fetchone()
    return result[0] if result else None


def main():
    print("=" * 50)
    print("  🚗 자동차 등록 현황 정제 시작")
    print("=" * 50)

    try:
        engine = create_engine(
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
            f"?charset=utf8mb4"
        )

        # STEP 1: RAW 데이터 로드
        print("\n[STEP 1] RAW 데이터 로드 중...")
        df = load_raw_data()
        print(f"  📂 로드 완료: {len(df):,}행")

        # STEP 2: 데이터 정제 및 address_code 매칭
        print("\n[STEP 2] 데이터 정제 및 address_code 매칭 중...")
        results   = []
        not_found = []
        skipped   = []

        for _, row in df.iterrows():
            # sigungu 분리
            ssg_name, gemd_name = split_sigungu(row["sigungu"])

            # sd_name 변환
            sd_name = SD_NAME_MAP.get(row["sido"], row["sido"])

            # 예외처리
            exc_sd, exc_ssg, exc_gemd = apply_exceptions(row["sido"], ssg_name, gemd_name)

            # 제외 대상
            if exc_sd is None and exc_ssg is None:
                skipped.append(f"{sd_name} {ssg_name} {gemd_name}")
                continue

            # 예외처리 적용
            if exc_sd:
                sd_name = exc_sd
            if exc_ssg is not None:
                ssg_name = exc_ssg
            if exc_gemd is not None:
                gemd_name = exc_gemd

            # address_code 매칭
            address_code = get_address_code(engine, sd_name, ssg_name, gemd_name)

            if address_code:
                results.append({
                    "address_code": address_code,
                    "sd_name":      sd_name,
                    "ssg_name":     ssg_name,
                    "gemd_name":    gemd_name,
                    "total_gov":    row["total_gov"],
                    "total_prv":    row["total_prv"],
                    "total_com":    row["total_com"],
                })
            else:
                not_found.append(f"{sd_name} {ssg_name} {gemd_name}")

        print(f"  ✅ 매칭 성공: {len(results):,}건")
        if skipped:
            print(f"  ⏭️  제외 (행정구역 통합): {len(skipped)}건")
            for item in skipped:
                print(f"     - {item}")
        if not_found:
            print(f"  ⚠️  매칭 실패: {len(not_found)}건")
            for item in not_found:
                print(f"     - {item}")

        # STEP 3: 정제 DB에 저장
        print("\n[STEP 3] car_park.car_registration 에 저장 중...")
        result_df = pd.DataFrame(results)
        result_df.to_sql(
            name      = "car_registration",
            con       = engine,
            schema    = "car_park",
            if_exists = "append",
            index     = False,
            chunksize = 500
        )
        print("  ✅ 저장 완료!")

        # STEP 4: 검증
        print("\n[STEP 4] 데이터 검증 중...")
        with engine.connect() as conn:
            total = conn.execute(text(
                "SELECT COUNT(*) FROM car_park.car_registration"
            )).scalar()
            print(f"  📊 총 레코드 수: {total:,}건")

            matched = conn.execute(text(
                "SELECT COUNT(*) FROM car_park.car_registration WHERE address_code IS NOT NULL"
            )).scalar()
            print(f"  🔗 address_code 매칭 완료: {matched:,}건")

        print("\n✅ 모든 작업 완료!")

    except pymysql.err.OperationalError as e:
        print(f"\n❌ MySQL 연결 오류: {e}")
        print("   → DB_USER, DB_PASSWORD 확인해주세요")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()
