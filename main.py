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

# --- 2. 데이터 로드 함수 (강화된 버전) ---
@st.cache_data
def load_data(file_path_or_buffer):
    df = pd.DataFrame()
    
    # A. 인코딩 감지 및 읽기 시도
    try:
        # utf-8 시도
        df = pd.read_csv(file_path_or_buffer, skiprows=7, encoding='utf-8')
    except UnicodeDecodeError:
        # 실패 시 cp949(윈도우) 시도
        if hasattr(file_path_or_buffer, 'seek'):
            file_path_or_buffer.seek(0)
        df = pd.read_csv(file_path_or_buffer, skiprows=7, encoding='cp949')
    except Exception as e:
        # 기타 에러 발생 시
        st.error(f"파일을 읽는 도중 알 수 없는 에러가 발생했습니다: {e}")
        return pd.DataFrame()

    # B. 컬럼명 정리 (앞뒤 공백 제거)
    df.columns = df.columns.str.strip()
    
    # C. '날짜' 컬럼 찾기 및 표준화 (스마트 매핑)
    # 기상청 데이터마다 '날짜', '일시', 'date' 등 이름이 다를 수 있음
    col_mapping = {
        '일시': '날짜',
        'date': '날짜',
        'Date': '날짜',
        'time': '날짜'
    }
    df.rename(columns=col_mapping, inplace=True)

    # D. 그래도 '날짜' 컬럼이 없는 경우 디버깅 정보 출력
    if '날짜' not in df.columns:
        st.error("🚨 데이터에서 '날짜' 컬럼을 찾을 수 없습니다!")
        st.write("현재 파일의 컬럼 목록:", df.columns.tolist())
        st.write("힌트: 데이터 파일의 헤더(제목줄)가 7번째 줄이 맞나요? 원본 파일을 확인해보세요.")
        return pd.DataFrame() # 빈 데이터프레임 반환

    # E. '날짜' 컬럼 전처리
    try:
        df['날짜'] = df['날짜'].astype(str).str.strip()
        # 탭(\t) 문자 제거
        df['날짜'] = df['날짜'].str.replace('\t', '', regex=False)
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
    except Exception as e:
        st.error(f"날짜 변환 중 오류: {e}")
        return pd.DataFrame()
    
    # F. 결측치 제거
    cols_to_check = ['평균기온(℃)', '최저기온(℃)', '최고기온(℃)']
    existing_cols = [c for c in cols_to_check if c in df.columns]
    
    if existing_cols:
        df = df.dropna(subset=existing_cols)
    
    return df

# --- 3. 메인 UI 및 로직 ---
def main():
    st.title("🌡️ 오늘은 예전에 비해 얼마나 더울까?")
    st.markdown("과거 100년 넘는 데이터를 통해 **오늘의 기온이 역사적으로 어떤 위치**에 있는지 분석합니다.")

    # 사이드바: 파일 업로드 및 설정
    st.sidebar.header("설정")
    
    uploaded_file = st.sidebar.file_uploader("새로운 기상 데이터 업로드 (CSV)", type=['csv'])
    
    df = pd.DataFrame()

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        if not df.empty:
            st.sidebar.success("업로드된 파일을 사용합니다.")
    else:
        # 기본 파일 로드
        default_file = 'ta_20260122174530.csv'
        try:
            df = load_data(default_file)
            if not df.empty:
                st.sidebar.info("기본 탑재 데이터를 사용 중입니다.")
        except FileNotFoundError:
            st.error(f"기본 데이터 파일({default_file})을 찾을 수 없습니다.")
            return

    # 데이터가 비어있으면(로드 실패 시) 여기서 중단
    if df.empty:
        return

    # 날짜 범위 정보 표시 (여기서 에러가 났었음 -> 이제 안전함)
    try:
        min_date = df['날짜'].min().date()
        max_date = df['날짜'].max().date()
    except AttributeError:
        st.error("날짜 데이터를 읽어왔지만, 시간 형식으로 변환되지 않았습니다.")
        st.write(df.head())
        return

    st.sidebar.write(f"📅 데이터 기간: {min_date} ~ {max_date}")

    # 분석할 날짜 선택
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
        st.warning(f"{selected_date}의 데이터가 기록되지 않았습니다.")
        return

    target_avg_temp = target_row['평균기온(℃)'].values[0]
    target_year = selected_date.year

    # 역사 속 '같은 날' 데이터 추출
    historical_df = df[
        (df['날짜'].dt.month == selected_date.month) & 
        (df['날짜'].dt.day == selected_date.day)
    ]
    
    # 역사적 통계 계산
    hist_avg_mean = historical_df['평균기온(℃)'].mean()
    
    # 비교
    diff = target_avg_temp - hist_avg_mean
    
    # --- 5. 결과 시각화 ---
    
    # [섹션 1] 핵심 지표
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label=f"{selected_date} 평균기온", 
            value=f"{target_avg_temp}℃",
            delta=f"{diff:.1f}℃ (평년 대비)",
            delta_color="inverse"
        )
    with col2:
        st.metric(label="역대 같은 날 평균기온", value=f"{hist_avg_mean:.1f}℃")
    with col3:
        # 순위 계산
        rank = historical_df['평균기온(℃)'].rank(ascending=False).loc[target_row.index].values[0]
        total_years = len(historical_df)
        st.metric(label="역대 더운 순위", value=f"{int(rank)}위 / {total_years}년 중")

    st.divider()

    # [섹션 2] 히스토그램
    st.subheader(f"📊 {selected_date.month}월 {selected_date.day}일의 역사적 기온 분포")
    
    fig_hist = px.histogram(
        historical_df, 
        x="평균기온(℃)", 
        nbins=30, 
        title=f"지난 {total_years}년 간의 {selected_date.month}월 {selected_date.day}일 기온 분포",
        color_discrete_sequence=['#bdc3c7'],
        opacity=0.7,
        labels={"평균기온(℃)": "기온 (℃)"}
    )
    
    fig_hist.add_vline(x=target_avg_temp, line_width=3, line_dash="dash", line_color="red", annotation_text="선택한 날짜")
    fig_hist.add_vline(x=hist_avg_mean, line_width=2, line_color="blue", annotation_text="평년 기온")

    st.plotly_chart(fig_hist, use_container_width=True)

    # [섹션 3] 시계열 그래프
    st.subheader("📈 연도별 기온 변화 추이")
    
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
    
    # 추세선 (에러 방지 처리 포함)
    if len(historical_df) > 5:
        try:
            import statsmodels.api as sm # 확인용 import
            trend = px.scatter(historical_df, x='날짜', y='평균기온(℃)', trendline="lowess").data[1]
            trend.line.color = "gray"
            fig_line.add_traces(trend)
        except:
            pass
    
    fig_line.update_traces(marker=dict(size=8))
    fig_line.update_layout(showlegend=False)
    
    st.plotly_chart(fig_line, use_container_width=True)

if __name__ == "__main__":
    main()
