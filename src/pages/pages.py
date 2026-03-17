import streamlit as st
from .second import run_stats  # second.py 가져오기
from .third import run_info # third.py 가져오기

def load_pages():
    # 페이지 기본 설정
    st.set_page_config(page_title="주차장 서비스", layout="wide")

    # 사이드바에서 페이지 이동 메뉴 만들기
    st.sidebar.title("메뉴")
    choice = st.sidebar.radio("페이지를 선택하세요", ["주차장 검색", "통계 분석", "안내 사항"])

    # 1번 페이지: 주차장 검색 (여기에 코드 직접 작성)
    if choice == "주차장 검색":
        st.title("주차장 실시간 검색")
        search = st.text_input("주차장 이름이나 지역을 입력하세요.")
        
        if search:
            st.write(f"'{search}' 검색 결과 화면입니다.")
            # 여기에 데이터 필터링 로직 추가

    # 2번 페이지: 통계 (second.py의 함수 실행)
    elif choice == "통계 분석":
        run_stats()

    # 3번 페이지: 안내 (third.py의 함수 실행)
    elif choice == "안내 사항":
        run_info()