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
            current_time_str = now.strftime('%H:%M:%S')
            display_time = now.strftime('%Y-%m-%d %H:%M:%S')
            weekday = now.weekday()
            
            if weekday < 5: op_type = '평일'
            elif weekday == 5: op_type = '토요일'
            else: op_type = '공휴일'

            st.info(f"🕒 현재 조회 시각: **{display_time}**")

            # 2. 데이터 가져오기 (시간 계산은 파이썬에서 진행하기 위해 필드 유지)
            query = f"""
                SELECT 
                    p.pl_name, p.base_address, p.etc, p.pl_type, p.op_days,
                    h.start_time, h.end_time
                FROM parking_lot p
                JOIN operation_time h ON p.pl_id = h.pl_id
                WHERE p.pl_name LIKE %s
                  AND h.op_type = %s
            """
            
            if is_open_now:
                # 운영 중인 조건 필터링 (SQL에서 먼저 걸러냄)
                query += f"""
                  AND NOT (h.start_time = '00:00:00' AND h.end_time = '00:00:00')
                  AND (
                      (h.start_time < h.end_time AND '{current_time_str}' BETWEEN h.start_time AND h.end_time)
                      OR 
                      (h.start_time > h.end_time AND ('{current_time_str}' >= h.start_time OR '{current_time_str}' <= h.end_time))
                  )
                """

            cursor.execute(query, (f"%{search}%", op_type))
            results = cursor.fetchall()

            if results:
                # 3. 파이썬에서 남은 시간 계산 로직 처리
                processed_data = []
                current_now = now # 계산용 기준 시간

                for row in results:
                    start = row['start_time']
                    end = row['end_time']
                    
                    # 상태 및 남은 시간 초기화
                    status = "❌ 운영 종료"
                    time_left = "-"

                    # 24시간 운영 여부 체크 (00:00~23:59 등)
                    if start == datetime.timedelta(0) and end >= datetime.timedelta(hours=23, minutes=59):
                        status = "✅ 24시간 운영"
                        time_left = "여유로움"
                    else:
                        # timedelta를 오늘 날짜의 datetime 객체로 변환하여 계산
                        today = datetime.date.today()
                        dt_start = datetime.datetime.combine(today, (datetime.datetime.min + start).time())
                        dt_end = datetime.datetime.combine(today, (datetime.datetime.min + end).time())
                        
                        # 종료 시간이 다음날인 경우 (야간 운영)
                        if dt_end <= dt_start:
                            dt_end += datetime.timedelta(days=1)
                        
                        # 현재 운영 중인지 확인
                        if dt_start <= current_now <= dt_end:
                            status = "✅ 운영 중"
                            diff = dt_end - current_now
                            hours, remainder = divmod(diff.seconds, 3600)
                            minutes, _ = divmod(remainder, 60)
                            time_left = f"{hours}시간 {minutes}분 남음"
                        elif current_now < dt_start:
                            status = "❌ 운영 전"
                    
                    # 새로운 행 데이터 구성
                    processed_data.append({
                        "주차장 이름": row['pl_name'],
                        "주소": row['base_address'],
                        "현재 상태": status,
                        "마감까지 남은 시간": time_left,
                        "운영 시간": f"{start} ~ {end}",
                        "기타 정보": row['etc']
                    })

                df = pd.DataFrame(processed_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("결과가 없습니다.")

            cursor.close()
            conn.close()

if __name__ == '__main__':
    load_pages()