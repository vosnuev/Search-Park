import streamlit as st
import mysql.connector
import pandas as pd
import datetime
from .second import run_stats 
from .third import run_info
from db.db import Conn

def load_pages():
    st.set_page_config(page_title="주차장 서비스", layout="wide")
    st.sidebar.title("메뉴")
    choice = st.sidebar.radio("페이지 선택", ["주차장 검색", "결제방식 통계", "지역별 주차장 통계"])

    if choice == "주차장 검색":
        st.title("주차장 검색")
        
        search = st.text_input("검색할 주차장 이름을 입력하세요")
        
        # 필터 레이아웃 구성
        col1, col2 = st.columns([1, 2])
        with col1:
            is_open_now = st.checkbox("현재 운영 중인 주차장만 보기")
        with col2:
            # [추가] 결제 수단 선택 필터
            pay_options = st.multiselect("결제 수단 선택", ["카드", "현금"])

        if search:
            cursor = Conn.cursor(dictionary=True)

            now = datetime.datetime.now()
            current_time_str = now.strftime('%H:%M:%S')
            weekday = now.weekday()
            
            if weekday < 5: op_type = '평일'
            elif weekday == 5: op_type = '토요일'
            else: op_type = '공휴일'

            st.info(f"현재 조회 시각: **{now.strftime('%Y-%m-%d %H:%M:%S')}**")

            # [수정] 결제 수단 정보를 가져오기 위해 GROUP_CONCAT 사용
            query = f"""
                SELECT 
                    p.pl_name, p.base_address, p.etc, p.pl_type, p.op_days,
                    h.start_time, h.end_time,
                    GROUP_CONCAT(DISTINCT pay.pay_name) AS pay_methods
                FROM parking_lot p
                JOIN operation_time h ON p.pl_id = h.pl_id
                LEFT JOIN payment_type pay ON p.pl_id = pay.pl_id
                WHERE p.pl_name LIKE %s
                  AND h.op_type = %s
            """
            
            params = [f"%{search}%", op_type]

            # 결제 수단 필터링 조건 추가
            if pay_options:
                # 선택한 결제 수단 중 하나라도 포함된 주차장 검색
                placeholders = ', '.join(['%s'] * len(pay_options))
                query += f" AND pay.pay_name IN ({placeholders})"
                params.extend(pay_options)

            if is_open_now:
                query += f"""
                  AND NOT (h.start_time = '00:00:00' AND h.end_time = '00:00:00')
                  AND (
                      (h.start_time < h.end_time AND '{current_time_str}' BETWEEN h.start_time AND h.end_time)
                      OR 
                      (h.start_time > h.end_time AND ('{current_time_str}' >= h.start_time OR '{current_time_str}' <= h.end_time))
                  )
                """

            query += " GROUP BY p.pl_id" # 주차장별로 그룹화

            cursor.execute(query, tuple(params))
            results = cursor.fetchall()

            if results:
                processed_data = []
                for row in results:
                    start = row['start_time']
                    end = row['end_time']
                    status = "❌ 운영 종료"
                    time_left = "-"

                    # 시간 계산 로직
                    today = datetime.date.today()
                    dt_start = datetime.datetime.combine(today, (datetime.datetime.min + start).time())
                    dt_end = datetime.datetime.combine(today, (datetime.datetime.min + end).time())
                    if dt_end <= dt_start: dt_end += datetime.timedelta(days=1)
                    
                    if dt_start <= now <= dt_end:
                        status = "✅ 운영 중"
                        diff = dt_end - now
                        hours, remainder = divmod(diff.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        time_left = f"{hours}시간 {minutes}분 남음"

                    processed_data.append({
                        "주차장 이름": row['pl_name'],
                        "주소": row['base_address'],
                        "현재 상태": status,
                        "마감까지 남은 시간": time_left,
                        "결제 수단": row['pay_methods'] if row['pay_methods'] else "정보 없음",
                        "기타 정보": row['etc']
                    })

                df = pd.DataFrame(processed_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("조건에 맞는 주차장이 없습니다.")

            cursor.close()
    elif choice == "결제방식 통계":
        run_stats()
    elif choice == "지역별 주차장 통계":
        run_info()
        

if __name__ == '__main__':
    load_pages()