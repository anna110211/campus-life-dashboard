import os
import re
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from wordcloud import WordCloud

# ==========================================
# 0. 페이지 기본 설정 및 한글 폰트 지정
# ==========================================
st.set_page_config(page_title="캠퍼스 생활 설문 대시보드", page_icon="🎓", layout="wide")

# 한글 폰트 설정 (제공된 NanumGothic.ttf 우선 적용)
font_path = "NanumGothic.ttf"
if os.path.exists(font_path):
  font_prop = fm.FontProperties(fname=font_path)
  font_name = font_prop.get_name()
  plt.rc("font", family=font_name)
else:
  # 기본 OS별 대체 폰트 설정
  plt.rc("font", family="Malgun Gothic" if os.name == "nt" else "AppleGothic")
plt.rc("axes", unicode_minus=False)  # 마이너스 기호 깨짐 방지


# ==========================================
# 1. 컬럼 매핑 유틸리티 함수
# ==========================================
def find_col(df, keywords):
  """컬럼명에 특정 키워드가 포함되어 있는지 찾아 실제 컬럼명을 반환합니다."""
  for col in df.columns:
    for kw in keywords:
      if kw in col.replace(" ", ""):
        return col
  return None


# ==========================================
# 2. 메인 웹 인터페이스 (위에서 아래 순서)
# ==========================================

# [1] 헤더 영역
st.title("🎓 캠퍼스 생활 설문 결과 대시보드")
st.markdown(
    "학생회 데이터 담당자가 제공하는 **재학생 캠퍼스 생활 습관 및 만족도"
    " 분석** 페이지입니다."
)
st.divider()

# [2] CSV 파일 업로드 및 데이터 정제/미리보기 섹션
st.subheader("📁 1. 설문 데이터 업로드 및 검증")

# 파일 업로드 위젯 (로컬에 campus_life.csv가 있으면 기본 자동 불러오기 지원)
uploaded_file = st.file_uploader(
    "설문 결과 CSV 파일(campus_life.csv)을 업로드하세요.", type=["csv"]
)

raw_df = None
if uploaded_file is not None:
  raw_df = pd.read_csv(uploaded_file)
elif os.path.exists("campus_life.csv"):
  raw_df = pd.read_csv("campus_life.csv")

if raw_df is None:
  st.info("👆 분석을 시작하려면 CSV 파일을 업로드해 주세요.")
  st.stop()

import collections
import matplotlib.pyplot as plt

# ==========================================
# 추가 시각화: 한 줄 의견 심층 분석 (Top 10 및 긍/부정 분석)
# ==========================================
st.divider()
st.subheader("💡 6. 한 줄 의견 심층 키워드 분석")

if opinion_col and not filtered_df[opinion_col].dropna().empty:
  # 텍스트 병합 및 단어 추출 (2글자 이상)
  all_text_for_analysis = " ".join(filtered_df[opinion_col].dropna().astype(str).tolist())
  extracted_words = re.findall(r'[가-힣]{2,}', all_text_for_analysis)

  # 1. 긍정/부정 단어 사전 정의 및 카운팅
  pos_keywords = ['좋다', '만족', '최고', '유익', '편리', '좋음', '쾌적', '재밌', '충분', '좋은']
  neg_keywords = ['아쉽', '부족', '불편', '불만', '최악', '힘들', '어렵', '비싸', '개선', '나쁨']

  pos_count = sum(1 for word in extracted_words if any(p in word for p in pos_keywords))
  neg_count = sum(1 for word in extracted_words if any(n in word for n in neg_keywords))

  st.markdown(f"**[{selected_dept}] 학생들의 감성 분석 결과**")

  # 메트릭 표시
  emo_col1, emo_col2 = st.columns(2)
  emo_col1.metric(label="😊 긍정적 단어 등장 횟수", value=f"{pos_count} 회")
  emo_col2.metric(label="😠 부정적 단어 등장 횟수", value=f"{neg_count} 회")

  # 긍정/부정 파이 차트와 Top 10 막대그래프를 나란히 배치
  col_chart1, col_chart2 = st.columns(2)

  with col_chart1:
    st.caption("긍정 vs 부정 단어 비율")
    fig_emo, ax_emo = plt.subplots(figsize=(5, 5))
    if pos_count == 0 and neg_count == 0:
      ax_emo.text(0.5, 0.5, "감성 단어 매칭 결과 없음", ha='center', va='center')
      ax_emo.axis('off')
    else:
      ax_emo.pie(
        [pos_count, neg_count],
        labels=['긍정', '부정'],
        autopct='%1.1f%%',
        colors=['#66b3ff', '#ff9999'],
        startangle=90
      )
    st.pyplot(fig_emo)

  with col_chart2:
    st.caption("가장 자주 등장하는 단어 Top 10")
    # 2. 키워드 빈도수 계산 (Top 10)
    word_counts = collections.Counter(extracted_words)
    top_10_words = word_counts.most_common(10)

    if top_10_words:
      words, counts = zip(*top_10_words)
      fig_top10, ax_top10 = plt.subplots(figsize=(6, 5))

      # 가로형 막대그래프
      sns.barplot(x=list(counts), y=list(words), ax=ax_top10, palette="viridis")
      ax_top10.set_xlabel("등장 횟수")
      ax_top10.set_ylabel("키워드")
      st.pyplot(fig_top10)
    else:
      st.info("추출할 단어가 충분하지 않습니다.")
else:
  st.info("한 줄 의견 데이터를 분석할 수 없습니다.")