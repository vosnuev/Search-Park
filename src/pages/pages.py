import streamlit as st
import mysql.connector
import pandas as pd
import datetime
from second import run_stats 
from third import run_info

def load_pages():
    st.set_page_config(page_title="주차장 서비스", layout="wide")
    st.sidebar.title("메뉴")
    choice = st.sidebar.radio("페이지 선택", ["주차장 검색", "통계", "안내"])

    if choice == "주차장 검색":
        st.title("주차장 검색")
        
        search = st.text_input("검색할 주차장 이름을 입력하세요")
        is_open_now = st.checkbox("현재 운영 중인 주차장만 보기")

        if search:
            conn = mysql.connector.connect(
                host="localhost", user="root", password="1234", database="car_park"
            )
            cursor = conn.cursor(dictionary=True)

            # 1. 현재 시간 및 요일 설정
            now = datetime.datetime.now()
            current_time = now.strftime('%H:%M:%S')
            weekday = now.weekday()
            
            if weekday < 5: op_type = '평일'
            elif weekday == 5: op_type = '토요일'
            else: op_type = '공휴일'

            # 2. 기본 쿼리 (현재 상태를 CASE WHEN으로 계산)
            # - 0시~0시는 '정보 없음' 또는 '운영 종료'로 표시
            # - 그 외는 시간에 따라 '운영 중' / '운영 종료' 표시
            query = f"""
                SELECT 
                    p.pl_name, p.base_address, p.etc, p.pl_type, p.op_days,
                    CASE 
                        WHEN h.start_time = '00:00:00' AND h.end_time = '00:00:00' THEN '운영 종료'
                        WHEN (h.start_time < h.end_time AND '{current_time}' BETWEEN h.start_time AND h.end_time) OR
                             (h.start_time > h.end_time AND ('{current_time}' >= h.start_time OR '{current_time}' <= h.end_time))
                        THEN '✅ 운영 중'
                        ELSE '❌ 운영 종료'
                    END AS status
                FROM parking_lot p
                JOIN operation_time h ON p.pl_id = h.pl_id
                WHERE p.pl_name LIKE %s
                  AND h.op_type = %s
            """

            # 3. 체크박스 선택 시 운영 중인 데이터만 필터링 추가
            if is_open_now:
                query += """
                  AND NOT (h.start_time = '00:00:00' AND h.end_time = '00:00:00')
                  AND (
                      (h.start_time < h.end_time AND %s BETWEEN h.start_time AND h.end_time)
                      OR 
                      (h.start_time > h.end_time AND (%s >= h.start_time OR %s <= h.end_time))
                  )
                """
                params = (f"%{search}%", op_type, current_time, current_time, current_time)
            else:
                params = (f"%{search}%", op_type)

            cursor.execute(query, params)
            results = cursor.fetchall()

            if results:
                df = pd.DataFrame(results)
                
                # 컬럼명 매핑 (status 추가)
                df = df.rename(columns={
                    "pl_name": "주차장 이름",
                    "base_address": "주소",
                    "etc": "기타 정보",
                    "pl_type": "주차장 종류",
                    "op_days": "운영 요일",
                    "status": "현재 상태"
                })
                
                # 표 출력
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("결과가 없습니다.")

            cursor.close()
            conn.close()

if __name__ == '__main__':
    load_pages()