import streamlit as st
import mysql.connector
import pandas as pd
from second import run_stats 
from third import run_info

def load_pages():
    st.set_page_config(page_title="주차장 서비스", layout="wide")
    st.sidebar.title("메뉴")
    choice = st.sidebar.radio("페이지 선택", ["주차장 검색", "통계", "안내"])

    if choice == "주차장 검색":
        st.title("주차장 검색")
        
        # [중요] 사용자가 검색어를 입력할 칸이 먼저 있어야 함!
        search = st.text_input("검색할 주차장 이름을 입력하세요")

        if search: # 사용자가 검색어를 입력하고 Enter를 쳤을 때만 실행
            conn = mysql.connector.connect(
                host="localhost", user="root", password="1234", database="car_park"
            )
            cursor = conn.cursor(dictionary=True)

            # LIKE 문법: %를 써서 앞뒤 포함 검색
            # 현재 작성하신 코드
            query = "SELECT pl_name, base_address, etc, pl_type, op_days FROM parking_lot WHERE pl_name LIKE %s"
            cursor.execute(query, (f"%{search}%",)) 
            
            results = cursor.fetchall()

            if results:
                # 1. 가져온 데이터를 표(데이터프레임) 형태로 만듭니다.
                df = pd.DataFrame(results)
                
                # 2. 영문 컬럼명을 원하는 한글 이름으로 바꿔줍니다.
                df = df.rename(columns={
                    "pl_name": "주차장 이름",
                    "base_address": "주소",
                    "etc": "기타 정보",
                    "pl_type": "주차장 종류",
                    "op_days": "운영 요일"
                })
                
                # 3. 이름이 바뀐 표를 화면에 띄웁니다.
                st.dataframe(df)
            else:
                st.warning("결과가 없습니다.")

            cursor.close()
            conn.close()
load_pages()
    


