import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="서울 기온 역사 분석기",
    page_icon="🌡️",
    layout="wide"
)

# --- 2. 데이터 로드 함수 (캐싱 적용) ---
@st.cache_data
def load_data(file_path_or_buffer):
    try:
        # 기상청 데이터는 보통 상단 7줄이 메타데이터이므로 skiprows=7
        # 탭(\t) 문자가 포함된 날짜 처리를 위해 정제 과정 필요
        df = pd.read_csv(file_path_or_buffer, skiprows=7, encoding='utf-8')
        
        # 컬럼명 정리 (공백 제거)
        df.columns = df.columns.str.strip()
        
        # '날짜' 컬럼 전처리: 앞의 탭(\t) 제거 및 datetime 변환
        if '날짜' in df.columns:
            df['날짜'] = df['날짜'].astype(str).str.strip()
            df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        
        # 결측치 제거 (분석 정확도를 위해)
        df = df.dropna(subset=['평균기온(℃)', '최저기온(℃)', '최고기온(℃)'])
        
        return df
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# --- 3. 메인 UI 및 로직 ---
def main():
    st.title("🌡️ 오늘은 예전에 비해 얼마나 더울까?")
    st.markdown("과거 100년 넘는 데이터를 통해 **오늘의 기온이 역사적으로 어떤 위치**에 있는지 분석합니다.")

    # 사이드바: 파일 업로드 및 설정
    st.sidebar.header("설정")
    
    # 기본 파일 사용 vs 사용자 업로드
    uploaded_file = st.sidebar.file_uploader("새로운 기상 데이터 업로드 (CSV)", type=['csv'])
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        st.sidebar.success("업로드된 파일을 사용합니다.")
    else:
        # 기본 파일 로드 (같은 폴더에 파일이 있어야 함)
        default_file = 'ta_20260122174530.csv'
        try:
            df = load_data(default_file)
            st.sidebar.info("기본 탑재 데이터를 사용 중입니다.")
        except FileNotFoundError:
            st.error("기본 데이터 파일을 찾을 수 없습니다. CSV 파일을 업로드해주세요.")
            return

    if df.empty:
        return

    # 날짜 범위 정보
    min_date = df['날짜'].min().date()
    max_date = df['날짜'].max().date()
    
    st.sidebar.write(f"📅 데이터 기간: {min_date} ~ {max_date}")

    # 분석할 날짜 선택 (기본값: 데이터의 가장 최근 날짜)
    selected_date = st.sidebar.date_input(
        "분석하고 싶은 날짜 선택",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )

    # --- 4. 데이터 분석 로직 ---
    # 선택된 날짜의 데이터 추출
    target_row = df[df['날짜'].dt.date == selected_date]

    if target_row.empty:
        st.error("선택한 날짜의 데이터가 없습니다.")
        return

    target_avg_temp = target_row['평균기온(℃)'].values[0]
    target_year = selected_date.year

    # 역사 속 '같은 날' 데이터 추출 (예: 매년 1월 21일 데이터만 모음)
    historical_df = df[
        (df['날짜'].dt.month == selected_date.month) & 
        (df['날짜'].dt.day == selected_date.day)
    ]
    
    # 역사적 통계 계산
    hist_avg_mean = historical_df['평균기온(℃)'].mean()
    hist_max = historical_df['평균기온(℃)'].max()
    hist_min = historical_df['평균기온(℃)'].min()
    
    # 비교 (더운지 추운지)
    diff = target_avg_temp - hist_avg_mean
    status = "더움" if diff > 0 else "추움"
    
    # --- 5. 결과 시각화 ---
    
    # [섹션 1] 핵심 지표 (Metric)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label=f"{selected_date} 평균기온", 
            value=f"{target_avg_temp}℃",
            delta=f"{diff:.1f}℃ (평년 대비)",
            delta_color="inverse" # 높으면 빨강(더움), 낮으면 파랑(추움) 효과를 위해 역전 시도(상황에 따라 조정)
        )
    with col2:
        st.metric(label="역대 같은 날 평균기온", value=f"{hist_avg_mean:.1f}℃")
    with col3:
        rank = historical_df['평균기온(℃)'].rank(ascending=False).loc[target_row.index].values[0]
        total_years = len(historical_df)
        st.metric(label="역대 순위 (더운 순)", value=f"{int(rank)}위 / {total_years}년 중")

    st.divider()

    # [섹션 2] 히스토그램 (분포 비교)
    st.subheader(f"📊 {selected_date.month}월 {selected_date.day}일의 역사적 기온 분포")
    
    fig_hist = px.histogram(
        historical_df, 
        x="평균기온(℃)", 
        nbins=30, 
        title=f"지난 {total_years}년 간의 {selected_date.month}월 {selected_date.day}일 기온 분포",
        color_discrete_sequence=['#bdc3c7'], # 회색 톤
        opacity=0.7
    )
    
    # 선택된 날짜의 위치 표시 (빨간 선)
    fig_hist.add_vline(
        x=target_avg_temp, 
        line_width=3, 
        line_dash="dash", 
        line_color="red", 
        annotation_text="선택한 날짜", 
        annotation_position="top right"
    )
    
    # 평년 기온 위치 표시 (파란 선)
    fig_hist.add_vline(
        x=hist_avg_mean, 
        line_width=2, 
        line_color="blue", 
        annotation_text="평년 기온", 
        annotation_position="top left"
    )

    st.plotly_chart(fig_hist, use_container_width=True)

    # [섹션 3] 시계열 그래프 (트렌드)
    st.subheader("📈 연도별 기온 변화 추이")
    
    # 사용자가 보기 편하게 현재 선택된 연도는 빨간 점으로 강조
    historical_df['color'] = historical_df['날짜'].dt.year.apply(lambda x: 'Selected' if x == target_year else 'History')
    
    fig_line = px.scatter(
        historical_df, 
        x='날짜', 
        y='평균기온(℃)', 
        color='color',
        color_discrete_map={'Selected': 'red', 'History': 'skyblue'},
        hover_data=['최저기온(℃)', '최고기온(℃)'],
        title=f"역대 {selected_date.month}월 {selected_date.day}일 기온 변화"
    )
    
    # 추세선 추가 (Lowess)
    fig_line.add_traces(
        px.scatter(historical_df, x='날짜', y='평균기온(℃)', trendline="lowess").data[1]
    )
    
    # 선 그래프 레이아웃 다듬기
    fig_line.update_traces(marker=dict(size=8))
    fig_line.update_layout(showlegend=False)
    
    st.plotly_chart(fig_line, use_container_width=True)

if __name__ == "__main__":
    main()
