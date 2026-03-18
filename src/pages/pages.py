import sys
import os
# ▼ 파이썬이 상위 폴더(src)를 인식할 수 있도록 경로를 강제로 추가해 주는 마법의 코드입니다!
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import streamlit as st
import mysql.connector
import pandas as pd
import datetime
from .second import run_stats 
from .third import run_info
from .forth import run_new
from db.db import Conn


def load_pages():
    st.sidebar.title("메뉴")
    
    # ▼ 여기에 "새로운 메뉴"를 추가했습니다! (원하시는 이름으로 바꿔주세요)
    choice = st.sidebar.radio("페이지 선택", ["주차장 검색", "결제방식 통계", "지역별 주차장 통계", "새로운 메뉴"])

    # 1. 주차장 검색 페이지
    if choice == "주차장 검색":
        st.title("주차장 검색")
        
        search = st.text_input("검색할 주차장 이름을 입력하세요")
        
        # 필터 레이아웃 구성
        col1, col2 = st.columns([1, 2])
        with col1:
            is_open_now = st.checkbox("현재 운영 중인 주차장만 보기")
        with col2:
            pay_options = st.multiselect("결제 수단 선택", ["카드", "현금"])
            
        # 주차장 검색을 위한 DB 조회 로직
        if search:
            cursor = Conn.cursor(dictionary=True)

            now = datetime.datetime.now()
            current_time_str = now.strftime('%H:%M:%S')
            weekday = now.weekday()
            
            if weekday < 5: op_type = '평일'
            elif weekday == 5: op_type = '토요일'
            else: op_type = '공휴일'

            st.info(f"현재 조회 시각: **{now.strftime('%Y-%m-%d %H:%M:%S')}**")

            # p.has_priority 추가 완료된 단일 쿼리
            query = """
                SELECT 
                    p.pl_name, p.base_address, p.etc, p.pl_type, p.op_days,
                    p.has_priority,
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
                placeholders = ', '.join(['%s'] * len(pay_options))
                query += f" AND pay.pay_name IN ({placeholders})"
                params.extend(pay_options)

            # 운영 중 필터링 조건 추가
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

                    # 장애인 주차구역 텍스트 변환
                    priority_status = "O" if row['has_priority'] == 1 else "X"

                    processed_data.append({
                        "주차장 이름": row['pl_name'],
                        "주소": row['base_address'],
                        "현재 상태": status,
                        "마감까지 남은 시간": time_left,
                        "장애인 주차구역": priority_status,
                        "결제 수단": row['pay_methods'] if row['pay_methods'] else "정보 없음",
                        "기타 정보": row['etc']
                    })

                df = pd.DataFrame(processed_data)
                table = st.dataframe(df, use_container_width=True, on_select="rerun", selection_mode="single-row")
            else:
                st.warning("조건에 맞는 주차장이 없습니다.")

            cursor.close()

            selected_rows = table.selection.rows
            if selected_rows:
                row = df.iloc[selected_rows[0]]
                show_review(row)


    elif choice == "결제방식 통계":
        run_stats()

    # 3. 지역별 주차장 통계 페이지
    elif choice == "지역별 주차장 통계":
        run_info()
        
    # ▼ 4. 새로운 메뉴 페이지 추가!
    elif choice == "새로운 메뉴":
        run_new()

def show_review(row):
    field = (row['주차장 이름'],)
    review = []
    with Conn.cursor() as cursor:
        cursor.execute("""
            select pk_name, review_txt, review_date
            from n_pkreviews
            where pk_name = %s
        """, field)
        review = cursor.fetchall()
    if review:
        st.table(review)


if __name__ == '__main__':
    load_pages()