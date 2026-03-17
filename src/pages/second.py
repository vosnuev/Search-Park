import streamlit as st

def run_stats():
    st.title("데이터 통계 분석")
    st.write("수집된 70만 개 데이터를 시각화하는 공간입니다.")
    # 예시 막대 그래프
    st.bar_chart({"강남구": 20, "서초구": 15, "송파구": 25})