import streamlit as st
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine, URL
from db.db import Conn
from urllib.parse import quote_plus


def run_stats():
    st.title("동별 결제수단 통계")
    url = URL.create(
        drivername="mysql+mysqlconnector",
        username=Conn.user,
        password=Conn._password,  # 특수문자 걱정 없음
        host=Conn._host,
        port=Conn._port,
        database=Conn.database,
    )
    engine = create_engine(url)

    query = """
    SELECT
        ac.sd_name,
        ac.ssg_name,
        ac.gemd_name,
        pt.pay_name,
        COUNT(*) AS cnt
    FROM car_park.parking_lot p
    JOIN car_park.payment_type pt
        ON p.pl_id = pt.pl_id
    JOIN car_park.address ac
        ON p.address_code = ac.address_code
    GROUP BY
        ac.sd_name,
        ac.ssg_name,
        ac.gemd_name,
        pt.pay_name
    ORDER BY
        ac.sd_name,
        ac.ssg_name,
        ac.gemd_name,
        pt.pay_name
    """

    df = pd.read_sql(query, engine)

    df = df[df["pay_name"].isin(["카드", "현금"])]

    sd_list = sorted(df["sd_name"].dropna().unique())
    selected_sd = st.selectbox("시도 선택", sd_list)

    filtered_sd = df[df["sd_name"] == selected_sd]

    ssg_list = sorted(filtered_sd["ssg_name"].dropna().unique())
    selected_ssg = st.selectbox("시군구 선택", ssg_list)

    filtered_df = filtered_sd[filtered_sd["ssg_name"] == selected_ssg]

    if filtered_df.empty:
        st.warning("선택한 지역에 데이터가 없습니다.")
        return

    # 동별 카드/현금 피벗
    pivot_df = filtered_df.pivot_table(
        index="gemd_name",
        columns="pay_name",
        values="cnt",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    # 카드/현금 컬럼이 없는 경우 대비
    if "카드" not in pivot_df.columns:
        pivot_df["카드"] = 0
    if "현금" not in pivot_df.columns:
        pivot_df["현금"] = 0

    # 합계 컬럼 추가
    pivot_df["합계"] = pivot_df["카드"] + pivot_df["현금"]
    pivot_df = pivot_df.rename(columns={
    "gemd_name": "동/면/읍"
    })

    # KPI 계산
    total_card = pivot_df["카드"].sum()
    total_cash = pivot_df["현금"].sum()

    col1, col2 = st.columns(2)
    col1.metric("총 카드", total_card)
    col2.metric("총 현금", total_cash)

    # 긴 형태로 변환
    chart_df = pivot_df.melt(
        id_vars="동/면/읍",
        value_vars=["카드", "현금", "합계"],
        var_name="결제수단",
        value_name="개수"
    )

    st.subheader(f"{selected_sd} {selected_ssg} 동별 카드/현금/합계 현황")

    fig = px.bar(
        chart_df,
        x="동/면/읍",
        y="개수",
        color="결제수단",
        barmode="group",
        text="개수",
        color_discrete_map={
            "카드": "#065F46",
            "현금": "#10B981",
            "합계": "#D1FAE5"    
        }
    )

    fig.update_traces(
        textfont=dict(
        size=12,
        color="#374151"
    )
    )

    fig.update_layout(
        title=f"{selected_sd} {selected_ssg} 결제수단 현황",
        xaxis_title="동/면/읍",
        yaxis_title="개수",
        legend_title="구분",
        bargap=0.2,
        plot_bgcolor="white",
        paper_bgcolor="white"
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(200,200,200,0.3)")

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(pivot_df, use_container_width=True)