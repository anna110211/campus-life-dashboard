import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from wordcloud import WordCloud
import collections
import re
import os

# ==========================================
# 0. 페이지 기본 설정 및 한글 폰트 지정
# ==========================================
st.set_page_config(page_title="캠퍼스 생활 설문 대시보드", page_icon="🎓", layout="wide")

font_path = "NanumGothic.ttf"
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    font_name = font_prop.get_name()
    plt.rc('font', family=font_name)
else:
    plt.rc('font', family='Malgun Gothic' if os.name == 'nt' else 'AppleGothic')
plt.rc('axes', unicode_minus=False)

# ==========================================
# 1. 컬럼 매핑 유틸리티 함수
# ==========================================
def find_col(df, keywords):
    for col in df.columns:
        for kw in keywords:
            if kw in str(col).replace(" ", ""):
                return col
    return None

# ==========================================
# 2. 메인 웹 인터페이스
# ==========================================
st.title("🎓 캠퍼스 생활 설문 결과 대시보드")
st.markdown("학생회 데이터 담당자가 제공하는 **재학생 캠퍼스 생활 습관 및 만족도 분석** 페이지입니다.")
st.divider()

# [1] 파일 업로드
st.subheader("📁 1. 설문 데이터 업로드 및 검증")
uploaded_file = st.file_uploader("설문 결과 CSV 파일(campus_life.csv)을 업로드하세요.", type=["csv"])

raw_df = None
if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)
elif os.path.exists("campus_life.csv"):
    raw_df = pd.read_csv("campus_life.csv")

if raw_df is None:
    st.info("분석을 시작하려면 설문 결과 CSV 파일을 업로드해 주세요.")
    st.stop()

# 컬럼 자동 매핑
dept_col = find_col(raw_df, ['학과', '전공', '학부'])
study_col = find_col(raw_df, ['공부시간', '학습시간', '공부'])
sleep_col = find_col(raw_df, ['수면시간', '수면'])
phone_col = find_col(raw_df, ['스마트폰', '폰사용', '스마트폰사용시간'])
satis_col = find_col(raw_df, ['만족도', '학교생활만족도'])
opinion_col = find_col(raw_df, ['의견', '한줄의견', '한줄', '소감', '코멘트'])

# 데이터 정제
total_rows = len(raw_df)
df = raw_df.copy()

num_cols = [c for c in [study_col, sleep_col, phone_col, satis_col] if c]
for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce')

valid_condition = pd.Series(True, index=df.index)
if dept_col: valid_condition &= df[dept_col].notnull()
if satis_col: valid_condition &= df[satis_col].notnull() & (df[satis_col] >= 0)
if study_col: valid_condition &= (df[study_col] >= 0) & (df[study_col] <= 24)
if sleep_col: valid_condition &= (df[sleep_col] >= 0) & (df[sleep_col] <= 24)
if phone_col: valid_condition &= (df[phone_col] >= 0) & (df[phone_col] <= 24)

clean_df = df[valid_condition].copy()
valid_rows = len(clean_df)
excluded_rows = total_rows - valid_rows

col_info1, col_info2, col_info3 = st.columns(3)
col_info1.metric("총 응답 수", f"{total_rows:,} 건")
col_info2.metric("정상 분석 데이터", f"{valid_rows:,} 건")
col_info3.metric("잘못된 데이터 제외 건수", f"{excluded_rows:,} 건", delta=f"-{excluded_rows} 건", delta_color="inverse")

with st.expander("🔍 정제된 데이터 미리보기 (상위 5건)"):
    st.dataframe(clean_df.head(), use_container_width=True)

st.divider()

# [2] 학과 선택 필터
st.subheader("🎯 2. 학과별 맞춤 분석 필터")
if dept_col and dept_col in clean_df.columns:
    departments = ["전체 학과"] + sorted(clean_df[dept_col].dropna().unique().tolist())
else:
    departments = ["전체 학과"]

selected_dept = st.selectbox("확인하고자 하는 학과를 선택하세요:", options=departments, index=0)

if selected_dept == "전체 학과" or not dept_col:
    filtered_df = clean_df
else:
    filtered_df = clean_df[clean_df[dept_col] == selected_dept]

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
avg_satis = filtered_df[satis_col].mean() if satis_col else 0
avg_study = filtered_df[study_col].mean() if study_col else 0
avg_sleep = filtered_df[sleep_col].mean() if sleep_col else 0
avg_phone = filtered_df[phone_col].mean() if phone_col else 0

m_col1.metric("⭐ 평균 학교생활 만족도", f"{avg_satis:.2f} 점")
m_col2.metric("📖 평균 공부시간", f"{avg_study:.1f} 시간")
m_col3.metric("💤 평균 수면시간", f"{avg_sleep:.1f} 시간")
m_col4.metric("📱 평균 스마트폰 시간", f"{avg_phone:.1f} 시간")

st.divider()

# [3] 학과별 생활 습관 막대그래프
st.subheader("📊 3. 학과별 학생들의 생활 습관 비교")
habit_cols = [c for c in [study_col, sleep_col, phone_col] if c]
if dept_col and habit_cols:
    dept_habit_mean = clean_df.groupby(dept_col)[habit_cols].mean()
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    dept_habit_mean.plot(kind='bar', ax=ax1, width=0.7, colormap='Set2')
    ax1.set_title("학과별 평균 생활 습관 비교", fontsize=14, pad=12)
    ax1.set_xlabel("학과", fontsize=11)
    ax1.set_ylabel("평균 시간 (시간)", fontsize=11)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=30, ha='right')
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    st.pyplot(fig1)
else:
    st.info("학과 또는 생활 습관 관련 데이터 컬럼을 찾을 수 없습니다.")

# [4] 만족도 상관관계 히트맵
st.subheader("🔥 4. 생활 습관과 학교생활 만족도 간의 관련성 (히트맵)")
corr_target_cols = [c for c in [study_col, sleep_col, phone_col, satis_col] if c]
if len(corr_target_cols) >= 2:
    corr_matrix = filtered_df[corr_target_cols].corr()
    fig2, ax2 = plt.subplots(figsize=(7, 5))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, linewidths=0.8, ax=ax2)
    ax2.set_title(f"[{selected_dept}] 상관관계 히트맵", fontsize=13, pad=12)
    st.pyplot(fig2)
else:
    st.info("상관관계를 계산할 수치형 데이터가 부족합니다.")

# [5] 워드클라우드
st.subheader("☁️ 5. 학생 한 줄 의견 키워드 분석 (워드 클라우드)")
if opinion_col and opinion_col in filtered_df.columns and not filtered_df[opinion_col].dropna().empty:
    all_text = " ".join(filtered_df
