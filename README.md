# 🌡️ 서울 기온 역사 분석기 (Seoul Historical Weather Analysis)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Plotly](https://img.shields.io/badge/Visualization-Plotly-orange)

> **"오늘 날씨, 역사적으로 봤을 때 과연 평범할까?"**
> 1907년부터 이어진 100년 이상의 기상 데이터를 분석하여, 특정 날짜의 기온이 평년과 얼마나 다른지 시각적으로 보여주는 Streamlit 웹 애플리케이션입니다.

## 📊 프로젝트 소개
이 프로젝트는 기상청 공공데이터를 활용하여 서울의 과거 기온 데이터를 분석합니다. 단순히 수치를 나열하는 것이 아니라, **'오늘'이 역사 속 같은 날짜들과 비교했을 때 얼마나 덥거나 추운지**를 직관적인 지표와 인터랙티브 그래프로 제공합니다.

### 🌟 주요 기능
1.  **역사적 비교 분석**: 선택한 날짜의 평균 기온이 지난 100년 평균 대비 몇 도나 차이 나는지 분석합니다.
2.  **순위 확인**: "오늘이 역대 1월 22일 중 몇 번째로 더운 날일까?"와 같은 궁금증을 해소해 줍니다.
3.  **인터랙티브 시각화 (Plotly)**:
    * **히스토그램**: 기온 분포 내에서 오늘의 위치를 시각적으로 확인.
    * **시계열 산점도**: 1900년대 초반부터 현재까지의 기온 변화 트렌드 확인.
4.  **데이터 업로드 지원**: 기본 탑재된 데이터 외에, 기상청 형식(헤더 7줄 포함)의 최신 CSV 파일을 업로드하여 분석할 수 있습니다.

## 📂 프로젝트 구조
```bash
├── app.py                  # 메인 애플리케이션 코드 (Streamlit)
├── requirements.txt        # 필요 라이브러리 목록
├── ta_20260122174530.csv   # 기본 기상 데이터 (1907~2026 서울)
└── README.md               # 프로젝트 설명서
