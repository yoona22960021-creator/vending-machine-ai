import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os

# 페이지 기본 설정 (코드가 켜지면 화면부터 무조건 그리도록 최상단 배치)
st.set_page_config(page_title="자판기 AI 추천 시스템", page_icon="🥤", layout="centered")

st.title("🥤 가림고 자판기 추천 시스템")
st.write("원하시는 음료를 추천해드립니다.")
st.markdown("---")

# 로그인된 사용자의 바탕화면 경로를 자동으로 인식하도록 설정
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
file_name = "data.xlsx"

@st.cache_data
def load_data():
    try:
        if file_name.endswith('.csv'):
            return pd.read_csv(file_name, encoding='cp949')
        else:
            # 엑셀 전용 엔진인 openpyxl을 명시적으로 지정
            return pd.read_excel(file_name, engine='openpyxl')
    except Exception as e:
        # 파일 로드 실패 시 원인을 화면에 빨간색 박스로 표시
        st.error(f"🚨 실제 엑셀 파일을 읽지 못했습니다. 원인: {e}")
        st.info(f"현재 접근하려는 파일 경로: {file_name}")
        
        # 에러 확인을 위해 기존 임시 데이터는 그대로 유지
        return pd.DataFrame({
            'Name': ['데미소다', '포카리스웨트', '코카콜라 제로', '밀키스'],
            'Sugar': [15, 12, 0, 20],
            'Calories': [60, 40, 0, 80],
            'Price': [1000, 1200, 1500, 1100],
            'AI_score': [15.2, 18.4, 20.1, 14.5],
            'Popularity (득표수)': [10, 25, 18, 32]
        })

df = load_data()

# 주요 데이터 기초통계량 계산
min_sugar, max_sugar, avg_sugar = int(df['Sugar'].min()), int(df['Sugar'].max()), int(df['Sugar'].mean())
min_cal, max_cal, avg_cal = int(df['Calories'].min()), int(df['Calories'].max()), int(df['Calories'].mean())
min_price, max_price, avg_price = int(df['Price'].min()), int(df['Price'].max()), int(df['Price'].mean())

# 2. 질문 선택 (오류 발생 부분 수정 완료)
question = st.selectbox(
    "어떤 음료를 찾고 계신가요?",
    [
        "선택해주세요",
        "🤖 AI회귀 식으로 판단한 최고의 음료수는? ",
        "📐 내가 원하는 조건과 가장 유사한 음료는? ",
        "💰 학생들이 판단한 가성비 최고인 음료수는?",
        "🔥 학생들이 투표한 가장 인기 많은 음료수는? ",
        "🏃 다이어트 중인데 칼로리 낮은 음료 없나? (저칼로리)"
    ]
)

st.markdown("---")

# 3. 알고리즘 실행 구간 (전체 Top 3 순위제로 변경 완료)
if question != "선택해주세요":
    
    # 코사인 유사도 추천 알고리즘
    if "📐" in question:
        st.subheader("🎯 원하시는 음료의 기준을 설정해주세요")
        
        st.caption(f"💡 우리 학교 자판기 데이터 안내:")
        st.caption(f"- 당류 범위: {min_sugar}g ~ {max_sugar}g (평균 약 {avg_sugar}g)")
        st.caption(f"- 칼로리 범위: {min_cal}kcal ~ {max_cal}kcal (평균 약 {avg_cal}kcal)")
        st.caption(f"- 가격 범위: {min_price}원 ~ {max_price}원 (평균 약 {avg_price}원)")
        
        st.markdown("---")
        
        st.write("🏃‍♂️ 빠른 조건 설정 피드백")
        col1, col2, col3 = st.columns(3)
        
        if 'sugar_val' not in st.session_state:
            st.session_state.sugar_val = avg_sugar
            st.session_state.cal_val = avg_cal
            st.session_state.price_val = avg_price

        if col1.button("🍃 다이어트용 (저당/저칼로리)"):
            st.session_state.sugar_val = 5
            st.session_state.cal_val = 30
            st.session_state.price_val = 1200

        if col2.button("📊 평범한 선택 (평균 수치)"):
            st.session_state.sugar_val = avg_sugar
            st.session_state.cal_val = avg_cal
            st.session_state.price_val = avg_price

        if col3.button("⚡ 당 충전 (고당도/에너지)"):
            st.session_state.sugar_val = max_sugar - 5
            st.session_state.cal_val = max_cal - 20
            st.session_state.price_val = 1400

        user_sugar = st.slider("선호하는 당류 (g)", min_sugar, max_sugar, int(st.session_state.sugar_val))
        user_calories = st.slider("선호하는 칼로리 (kcal)", min_cal, max_cal, int(st.session_state.cal_val))
        user_price = st.slider("선호하는 가격 (원)", min_price, max_price, int(st.session_state.price_val))
        
        if st.button("코사인 유사도 분석 시작"):
            features = ['Sugar', 'Calories', 'Price']
            matrix = df[features].values
            user_vector = np.array([[user_sugar, user_calories, user_price]])
            
            similarities = cosine_similarity(matrix, user_vector).flatten()
            df_copy = df.copy()
            df_copy['Similarity'] = similarities
            
            # 상위 3개 추출
            top3 = df_copy.sort_values(by='Similarity', ascending=False).head(3)
            
            st.success("🎯 설정하신 조건과 가장 유사한 음료 순위 (Top 3)")
            for i, (index, row) in enumerate(top3.iterrows(), 1):
                st.write(f"**{i}위: '{row['Name']}'**")
                st.info(f"💡 당류 {row['Sugar']}g / {row['Calories']}kcal / {row['Price']}원 (유사도: {row['Similarity']*100:.1f}%)")

    # [로직 1] AI 회귀분석 알고리즘
    elif "🤖" in question:
        # 상위 3개 추출
        top3 = df.sort_values(by='AI_score', ascending=False).head(3)
        
        st.success("🤖 AI 회귀분석이 뽑은 최고의 밸런스 순위 (Top 3)")
        for i, (index, row) in enumerate(top3.iterrows(), 1):
            st.write(f"**{i}위: '{row['Name']}'**")
            st.info(f"💡 예측 인기도 점수: {row['AI_score']:.2f}점")

    # [로직 2] 가성비 필터링 알고리즘
    elif "💰" in question:
        cheap_df = df[df['Price'] <= 1200]
        if not cheap_df.empty:
            # 상위 3개 추출
            top3 = cheap_df.sort_values(by='AI_score', ascending=False).head(3)
            
            st.warning("💰 1,200원 이하 가성비 추천 순위 (Top 3)")
            for i, (index, row) in enumerate(top3.iterrows(), 1):
                st.write(f"**{i}위: '{row['Name']}'**")
                st.info(f"💡 가격: {row['Price']}원 (예측 점수: {row['AI_score']:.2f}점)")
        else:
            st.error("1,200원 이하의 음료가 데이터에 없습니다.")

    # [로직 3] 실제 데이터 통계 알고리즘
    elif "🔥" in question:
        # 상위 3개 추출
        top3 = df.sort_values(by='Popularity (득표수)', ascending=False).head(3)
        
        st.info("🔥 우리 학교 학생들이 가장 많이 마시는 음료 순위 (Top 3)")
        for i, (index, row) in enumerate(top3.iterrows(), 1):
            st.write(f"**{i}위: '{row['Name']}'**")
            st.info(f"💡 설문조사 득표수: {row['Popularity (득표수)']}표")

    # [로직 4] 저칼로리 탐색 알고리즘
    elif "🏃" in question:
        # 상위 3개 추출 (오름차순)
        top3 = df.sort_values(by='Calories', ascending=True).head(3)
        
        st.error("🏃 다이어트 저칼로리 추천 순위 (Top 3)")
        for i, (index, row) in enumerate(top3.iterrows(), 1):
            st.write(f"**{i}위: '{row['Name']}'**")
            st.info(f"💡 칼로리: {row['Calories']}kcal")

st.markdown("---")

# 데이터 확인용
if st.checkbox("데이터베이스 원본 확인"):
    st.dataframe(df)
