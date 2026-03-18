import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as mticker
import numpy as np
import plotly.graph_objects as go
import sys
import os

# ─────────────────────────────────────────────
#  경로 설정 (pages/ 안에서 실행될 때 src/ 인식)
# ─────────────────────────────────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db import Conn   # src/db.py 의 Conn 사용

# ─────────────────────────────────────────────
#  한글 폰트 설정
# ─────────────────────────────────────────────
def set_korean_font():
    """Windows / Linux 환경 모두 대응"""
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",        # Windows - 맑은 고딕
        "C:/Windows/Fonts/NanumGothic.ttf",   # Windows - 나눔
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",  # Ubuntu
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",       # macOS
    ]
    for path in candidates:
        if os.path.exists(path):
            fe = fm.FontEntry(fname=path, name="KoreanFont")
            fm.fontManager.ttflist.insert(0, fe)
            plt.rcParams["font.family"] = "KoreanFont"
            break
    plt.rcParams["axes.unicode_minus"] = False

set_korean_font()

# ─────────────────────────────────────────────
#  등급 계산 함수
# ─────────────────────────────────────────────
def calc_grade(ratio: float, q75: float = 0, q50: float = 0, q25: float = 0) -> tuple[str, str]:
    """
    차량 1대당 주차면수 비율로 등급 계산 (데이터 기반 분위수)
    상위 25% = 여유, 25~50% = 보통, 50~75% = 부족, 하위 25% = 심각
    """
    if ratio >= q75:
        return "🟢 여유", "green"
    elif ratio >= q50:
        return "🟡 보통", "goldenrod"
    elif ratio >= q25:
        return "🟠 부족", "darkorange"
    else:
        return "🔴 심각", "crimson"

# ─────────────────────────────────────────────
#  DB 데이터 로드
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    """
    car_registration × parking_lot 를 address_code 기준 JOIN
    시군구 단위 집계
    """
    query = """
        SELECT
            cr.address_code,
            cr.sd_name      AS 시도,
            cr.ssg_name     AS 시군구,
            (cr.total_gov + cr.total_prv + cr.total_com) AS 총차량수,
            cr.total_prv    AS 자가용수,
            COALESCE(pl_agg.주차면수, 0) AS 주차면수,
            COALESCE(pl_agg.주차장수, 0) AS 주차장수
        FROM car_park.car_registration cr
        LEFT JOIN (
            SELECT
                LEFT(address_code, 5) AS code_prefix,
                SUM(capacity)          AS 주차면수,
                COUNT(pl_id)           AS 주차장수
            FROM car_park.parking_lot
            GROUP BY LEFT(address_code, 5)
        ) pl_agg ON LEFT(cr.address_code, 5) = pl_agg.code_prefix
        ORDER BY cr.sd_name, cr.ssg_name
    """
    df = pd.read_sql(query, Conn)

    df["차량당주차면수"] = (df["주차면수"] / df["총차량수"].replace(0, np.nan)).round(4)

    # 데이터 기반 분위수 계산
    q25 = df["차량당주차면수"].quantile(0.25)
    q50 = df["차량당주차면수"].quantile(0.50)
    q75 = df["차량당주차면수"].quantile(0.75)

    df["등급"], df["등급색"] = zip(*df["차량당주차면수"].apply(
        lambda r: calc_grade(r, q75, q50, q25)
    ))
    df["주차장수_per_만대"] = (df["주차장수"] / df["총차량수"].replace(0, np.nan) * 10000).round(2)
    df.attrs["q25"] = q25
    df.attrs["q50"] = q50
    df.attrs["q75"] = q75
    return df

# ─────────────────────────────────────────────
#  차트 그리기 헬퍼
# ─────────────────────────────────────────────
def draw_comparison_bar(df_filtered: pd.DataFrame):
    """차량수 vs 주차면수 비교 이중 바 차트 (Plotly 인터랙티브)"""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_filtered["시군구"],
        y=df_filtered["총차량수"],
        name="총 차량수",
        marker_color="#4C8EFF",
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>총 차량수: %{y:,}대<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df_filtered["시군구"],
        y=df_filtered["주차면수"],
        name="주차 면수",
        marker_color="#FF6B6B",
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>주차 면수: %{y:,}면<extra></extra>",
    ))

    fig.update_layout(
        barmode="group",
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font=dict(color="white", size=12),
        legend=dict(
            font=dict(size=14),
            bgcolor="#1E2130",
            bordercolor="gray",
            borderwidth=1,
        ),
        xaxis=dict(tickangle=-45, gridcolor="#333"),
        yaxis=dict(
            gridcolor="#333",
            tickformat=",",
            title="대수 / 면수 (드래그로 확대 가능)",
        ),
        hoverlabel=dict(bgcolor="#1E2130", font_size=13),
        height=500,
        margin=dict(b=100),
    )
    st.plotly_chart(fig, use_container_width=True)


def draw_ratio_bar(df_filtered: pd.DataFrame, q25: float = 0, q50: float = 0, q75: float = 0):
    """차량 1대당 주차면수 비율 바 차트 (데이터 기반 등급 색상 + 기준선)"""
    df_s = df_filtered.sort_values("차량당주차면수", ascending=True)

    # 등급별 색상 (데이터 기반 분위수 적용)
    colors = []
    for r in df_s["차량당주차면수"]:
        if r >= q75:
            colors.append("#2ECC71")   # 🟢 여유
        elif r >= q50:
            colors.append("#F1C40F")   # 🟡 보통
        elif r >= q25:
            colors.append("#E67E22")   # 🟠 부족
        else:
            colors.append("#E74C3C")   # 🔴 심각

    fig, ax = plt.subplots(figsize=(7, max(4, len(df_s) * 0.45)))
    fig.patch.set_facecolor("#0E1117")
    ax.set_facecolor("#0E1117")

    ax.barh(df_s["시군구"], df_s["차량당주차면수"], color=colors, alpha=0.88)

    # 기준선: 중앙값(q50) = 보통/부족 경계
    ax.axvline(q50, color="white", linewidth=0.8, linestyle="--", alpha=0.6,
               label=f"중앙값 {q50:.4f} (보통/부족 경계)")
    ax.axvline(q75, color="#2ECC71", linewidth=0.8, linestyle=":", alpha=0.5,
               label=f"상위25% {q75:.4f} (여유 기준)")

    ax.set_xlabel("차량 1대당 주차면수 (비율)", color="white", fontsize=10)
    ax.tick_params(colors="white")
    ax.legend(facecolor="#1E2130", labelcolor="white", fontsize=14, markerscale=2)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.grid(axis="x", color="#333", linewidth=0.5)

    st.pyplot(fig)
    plt.close(fig)


def draw_parking_lot_bar(df_filtered: pd.DataFrame, q25: float = 0, q50: float = 0, q75: float = 0):
    """만대당 주차장 수 바 차트 (Plotly 인터랙티브)"""
    df_s = df_filtered.sort_values("주차장수_per_만대", ascending=False)

    colors = []
    for r in df_s["차량당주차면수"]:
        if r >= q75:
            colors.append("#2ECC71")
        elif r >= q50:
            colors.append("#F1C40F")
        elif r >= q25:
            colors.append("#E67E22")
        else:
            colors.append("#E74C3C")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_s["시군구"],
        y=df_s["주차장수_per_만대"],
        marker_color=colors,
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>만대당 주차장 수: %{y:.2f}개<extra></extra>",
        showlegend=False,
    ))

    fig.update_layout(
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font=dict(color="white", size=12),
        xaxis=dict(tickangle=-45, gridcolor="#333"),
        yaxis=dict(gridcolor="#333", title="주차장 수 (차량 만 대당)"),
        hoverlabel=dict(bgcolor="#1E2130", font_size=13),
        height=450,
        margin=dict(b=100),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
#  메인 페이지 함수 (pages.py 에서 run_info() 로 호출)
# ─────────────────────────────────────────────
def run_stats():
    # ── 타이틀 & 서비스 안내 ───────────────────────
    st.title("🅿️ 지역별 차량수 대비 주차장 통계")
    st.caption("공공데이터 기반 · 자동차 등록 현황(2026.02) + 전국 주차장 표준 데이터")
    st.info("SKN 28기 1차 프로젝트 2팀의 결과물입니다.")
    st.write("- 데이터 출처: 공공데이터포털, 국가교통부 통계누리")
    st.write("- 업데이트 주기: 실시간")

    # ── 데이터 로드 ──────────────────────────────
    with st.spinner("데이터를 불러오는 중입니다..."):
        try:
            df = load_data()
        except Exception as e:
            st.error(f"DB 연결 오류: {e}")
            st.info("`.env` 파일의 DB 접속 정보를 확인해주세요.")
            return

    # ── 지역 필터 (메인 상단) ────────────────────────
    q25 = df.attrs.get("q25", 0)
    q50 = df.attrs.get("q50", 0)
    q75 = df.attrs.get("q75", 0)

    st.subheader("🔍 지역 필터")
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        sido_list = sorted(df["시도"].unique().tolist())
        selected_sido = st.selectbox("시/도 선택", ["전체"] + sido_list)
    with col_f2:
        if selected_sido != "전체":
            sgg_list = sorted(df[df["시도"] == selected_sido]["시군구"].unique().tolist())
            selected_sgg = st.multiselect(
                "시/군/구 선택 (복수 선택 가능)",
                sgg_list,
                default=sgg_list[:10] if len(sgg_list) > 10 else sgg_list,
            )
        else:
            selected_sgg = []
            st.empty()

    st.divider()

    # ── 데이터 필터링 ─────────────────────────────
    if selected_sido == "전체":
        # 시도 단위 집계
        df_view = (
            df.groupby("시도")
            .agg(총차량수=("총차량수", "sum"),
                 주차면수=("주차면수", "sum"),
                 주차장수=("주차장수", "sum"))
            .reset_index()
            .rename(columns={"시도": "시군구"})
        )
        df_view["차량당주차면수"] = (
            df_view["주차면수"] / df_view["총차량수"].replace(0, np.nan)
        ).round(4)
        q25 = df.attrs.get("q25", 0)
        q50 = df.attrs.get("q50", 0)
        q75 = df.attrs.get("q75", 0)
        df_view["등급"], df_view["등급색"] = zip(
            *df_view["차량당주차면수"].apply(lambda r: calc_grade(r, q75, q50, q25))
        )
        df_view["주차장수_per_만대"] = (
            df_view["주차장수"] / df_view["총차량수"].replace(0, np.nan) * 10000
        ).round(2)
        level_label = "시/도"
    else:
        if selected_sgg:
            df_view = df[
                (df["시도"] == selected_sido) & (df["시군구"].isin(selected_sgg))
            ].copy()
        else:
            df_view = df[df["시도"] == selected_sido].copy()
        level_label = "시/군/구"

    # ── KPI 카드 ──────────────────────────────────
    total_car   = int(df_view["총차량수"].sum())
    total_space = int(df_view["주차면수"].sum())
    total_lot   = int(df_view["주차장수"].sum())
    overall_ratio = total_space / total_car if total_car > 0 else 0
    q25 = df.attrs.get("q25", 0)
    q50 = df.attrs.get("q50", 0)
    q75 = df.attrs.get("q75", 0)
    overall_grade, _ = calc_grade(overall_ratio, q75, q50, q25)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🚗 총 차량수",     f"{total_car/10000:.0f}만 대")
    c2.metric("🅿️ 총 주차면수",  f"{total_space/10000:.0f}만 면")
    c3.metric("🏢 총 주차장수",   f"{total_lot/1000:.1f}천개소")
    c4.metric("📊 종합 주차 등급", overall_grade)

    st.divider()

    # ── 탭 구성 ───────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 차량수 vs 주차면수",
        "📉 차량당 주차면수 비율",
        "🏢 만대당 주차장 수",
        "📋 상세 테이블",
    ])

    with tab1:
        st.subheader(f"📊 {level_label}별 차량수 vs 주차면수 비교")
        total_cars_view  = int(df_view["총차량수"].sum())
        total_space_view = int(df_view["주차면수"].sum())
        gap = total_cars_view - total_space_view
        c_a, c_b, c_c = st.columns(3)
        c_a.markdown(f"<div style='background:#1E2130;border-radius:8px;padding:10px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:12px'>🚗 총 등록 차량수</span><br>"
                     f"<b style='color:#4C8EFF;font-size:18px'>{total_cars_view/10000:.0f}만 대</b></div>",
                     unsafe_allow_html=True)
        c_b.markdown(f"<div style='background:#1E2130;border-radius:8px;padding:10px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:12px'>🅿️ 총 주차 면수</span><br>"
                     f"<b style='color:#FF6B6B;font-size:18px'>{total_space_view/10000:.0f}만 면</b></div>",
                     unsafe_allow_html=True)
        ratio_pct = total_space_view / total_cars_view * 100
        c_c.markdown(f"<div style='background:#1E2130;border-radius:8px;padding:10px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:12px'>📊 주차면 확보율</span><br>"
                     f"<b style='color:#FFD700;font-size:18px'>차량 대비 {ratio_pct:.1f}%</b></div>",
                     unsafe_allow_html=True)
        st.markdown("")
        if df_view.empty:
            st.warning("선택한 지역 데이터가 없습니다.")
        else:
            draw_comparison_bar(df_view)

    with tab2:
        st.subheader(f"📉 {level_label}별 차량 1대당 주차면수 비율")
        c_a, c_b, c_c = st.columns(3)
        c_a.markdown(f"<div style='background:#1E2130;border-radius:8px;padding:10px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:12px'>🔴 심각 기준</span><br>"
                     f"<b style='color:#E74C3C;font-size:18px'>100대당 {q25*100:.0f}개 미만</b></div>",
                     unsafe_allow_html=True)
        c_b.markdown(f"<div style='background:#1E2130;border-radius:8px;padding:10px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:12px'>📊 전국 평균</span><br>"
                     f"<b style='color:#FFD700;font-size:18px'>100대당 {q50*100:.0f}개</b></div>",
                     unsafe_allow_html=True)
        c_c.markdown(f"<div style='background:#1E2130;border-radius:8px;padding:10px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:12px'>🟢 여유 기준</span><br>"
                     f"<b style='color:#2ECC71;font-size:18px'>100대당 {q75*100:.0f}개 이상</b></div>",
                     unsafe_allow_html=True)
        st.markdown("")
        if df_view.empty:
            st.warning("선택한 지역 데이터가 없습니다.")
        else:
            draw_ratio_bar(df_view, q25, q50, q75)

    with tab3:
        st.subheader(f"🏢 {level_label}별 차량 만 대당 주차장 수")
        lot_per_10k = df_view["주차장수_per_만대"]
        lot_q25 = round(lot_per_10k.quantile(0.25), 1)
        lot_q50 = round(lot_per_10k.quantile(0.50), 1)
        lot_q75 = round(lot_per_10k.quantile(0.75), 1)
        c_a, c_b, c_c = st.columns(3)
        c_a.markdown(f"<div style='background:#1E2130;border-radius:8px;padding:10px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:12px'>🔴 심각 기준</span><br>"
                     f"<b style='color:#E74C3C;font-size:18px'>만대당 {lot_q25}개 미만</b></div>",
                     unsafe_allow_html=True)
        c_b.markdown(f"<div style='background:#1E2130;border-radius:8px;padding:10px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:12px'>📊 전국 중앙값</span><br>"
                     f"<b style='color:#FFD700;font-size:18px'>만대당 {lot_q50}개</b></div>",
                     unsafe_allow_html=True)
        c_c.markdown(f"<div style='background:#1E2130;border-radius:8px;padding:10px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:12px'>🟢 여유 기준</span><br>"
                     f"<b style='color:#2ECC71;font-size:18px'>만대당 {lot_q75}개 이상</b></div>",
                     unsafe_allow_html=True)
        st.markdown("")
        if df_view.empty:
            st.warning("선택한 지역 데이터가 없습니다.")
        else:
            draw_parking_lot_bar(df_view, q25, q50, q75)

    with tab4:
        st.subheader(f"📋 {level_label}별 상세 통계")
        c_a, c_b, c_c, c_d = st.columns(4)
        c_a.markdown(f"<div style='background:#3D1010;border-radius:8px;padding:8px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:11px'>🔴 심각</span><br>"
                     f"<b style='color:#E74C3C;font-size:14px'>100대당 {q25*100:.0f}개 미만</b></div>",
                     unsafe_allow_html=True)
        c_b.markdown(f"<div style='background:#3D2A0A;border-radius:8px;padding:8px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:11px'>🟠 부족</span><br>"
                     f"<b style='color:#E67E22;font-size:14px'>{q25*100:.0f} ~ {q50*100:.0f}개</b></div>",
                     unsafe_allow_html=True)
        c_c.markdown(f"<div style='background:#2E2E0A;border-radius:8px;padding:8px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:11px'>🟡 보통</span><br>"
                     f"<b style='color:#F1C40F;font-size:14px'>{q50*100:.0f} ~ {q75*100:.0f}개</b></div>",
                     unsafe_allow_html=True)
        c_d.markdown(f"<div style='background:#0A2E12;border-radius:8px;padding:8px;text-align:center'>"
                     f"<span style='color:#aaa;font-size:11px'>🟢 여유</span><br>"
                     f"<b style='color:#2ECC71;font-size:14px'>100대당 {q75*100:.0f}개 이상</b></div>",
                     unsafe_allow_html=True)
        st.markdown("")

        display_cols = {
            "시군구":          level_label,
            "총차량수":        "총 차량수",
            "주차면수":        "주차 면수",
            "주차장수":        "주차장 수",
            "차량당주차면수":  "차량 1대당 주차면수",
            "주차장수_per_만대": "만대당 주차장 수",
            "등급":            "주차 등급",
        }
        df_display = df_view[list(display_cols.keys())].rename(columns=display_cols)
        df_display = df_display.sort_values("차량 1대당 주차면수")

        # 등급별 색상 하이라이트
        def highlight_grade(row):
            grade = row["주차 등급"]
            if "심각" in grade:
                return ["background-color: #3D1010"] * len(row)
            elif "부족" in grade:
                return ["background-color: #3D2A0A"] * len(row)
            elif "보통" in grade:
                return ["background-color: #2E2E0A"] * len(row)
            else:
                return ["background-color: #0A2E12"] * len(row)

        st.dataframe(
            df_display.style.apply(highlight_grade, axis=1).format({
                "총 차량수": "{:,.0f}",
                "주차 면수": "{:,.0f}",
                "주차장 수": "{:,.0f}",
                "차량 1대당 주차면수": "{:.4f}",
                "만대당 주차장 수": "{:.2f}",
            }),
            use_container_width=True,
            height=500,
        )

        # CSV 다운로드
        csv = df_display.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name="주차_통계_데이터.csv",
            mime="text/csv",
        )




# ─────────────────────────────────────────────
#  직접 실행 시
# ─────────────────────────────────────────────
if __name__ == "__main__":
    run_stats()

