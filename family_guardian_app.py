import streamlit as st
import pandas as pd

# ==========================================
# 1. 페이지 및 기본 설정
# ==========================================
st.set_page_config(
    page_title="성분 한눈에 - 맞춤형 가족 가디언",
    page_icon="🛡️",
    layout="wide"
)

# 세션 상태 초기화
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {"name": "가족가디언", "age": 30, "gender": "남성", "height": 170.0, "weight": 65.0}
if "selected_drugs" not in st.session_state:
    st.session_state.selected_drugs = []
if "custom_drugs" not in st.session_state:
    st.session_state.custom_drugs = []
if "selected_supplements" not in st.session_state:
    st.session_state.selected_supplements = []
if "custom_supplements" not in st.session_state:
    st.session_state.custom_supplements = []

# 연령별 영양성분 상한 섭취량(UL) 가이드 정보
def get_kdris_ul(age):
    if age < 9:
        return {"비타민 A": 1200, "비타민 D": 50, "마그네슘": 150, "아연": 15, "칼슘": 1400}, "소아 (1~8세)"
    elif age >= 60:
        return {"비타민 A": 3000, "비타민 D": 100, "마그네슘": 350, "아연": 35, "칼슘": 2000}, "고령자 (60세 이상)"
    else:
        return {"비타민 A": 3000, "비타민 D": 100, "마그네슘": 350, "아연": 35, "칼슘": 2500}, "성인/청소년 (9~59세)"

# BMI 판정 함수
def get_bmi_status(bmi):
    if bmi < 18.5:
        return "저체중", "orange", "⚖️ 균형 잡힌 식단과 충분한 영양 섭취가 필요합니다둥!"
    elif 18.5 <= bmi < 23:
        return "정상 체중", "green", "✨ 아주 훌륭한 상태입니다! 꾸준히 유지해 주세요둥!"
    elif 23 <= bmi < 25:
        return "과체중 (비만 전단계)", "blue", "⚠️ 식습관 및 가벼운 운동을 통한 체중 관리를 추천합니다둥!"
    elif 25 <= bmi < 30:
        return "1단계 비만", "red", "🚨 칼로리 조절 및 유산소 운동이 필요할 수 있습니다둥!"
    else:
        return "2단계 이상 고도비만", "purple", "🔥 전문가와의 상담 또는 보다 적극적인 건강 관리가 권장됩니다둥!"

# ==========================================
# 2. 데이터베이스 정의 (약물, 상호작용, 증상별 약물 추천)
# ========================================== 
DRUG_DIRECTORY = {
    "타이레놀": "아세트아미노펜계열",
    "아세트아미노펜": "아세트아미노펜계열",
    "게보린": "아세트아미노펜계열",
    "펜잘": "아세트아미노펜계열",
    "이지엔6": "비스테로이드소염제",
    "이부프로펜": "비스테로이드소염제",
    "록소프로펜": "비스테로이드소염제",
    "낙센": "비스테로이드소염제",
    "나프록센": "비스테로이드소염제",
    "아스피린": "항응고제/아스피린",
    "딜라트렌": "고혈압약",
    "노바스크": "고혈압약",
    "메트포르민": "당뇨약",
    "아마릴": "당뇨약",
    "리피토": "고지혈증약",
    "로수바스타틴": "고지혈증약",
    "레바미피드": "위장보호제",
    "가스터": "위산분비억제제",
    "알마겔": "제산제"
}

DRUG_DB = {
    "고혈압약": {
        "dur_senior": True,
        "caution_food": ["자몽/자몽주스 (칼슘채널차단제 혈중 농도를 높여 저혈압 초래 우려)", "바나나·시금치 (일부 이뇨성 혈압약과 병용 시 고칼륨혈증 유발 가능)"],
        "caution_drug": ["고용량 칼슘/마그네슘 (흡수 방해 방지를 위해 2시간 이상 간격 복용 권장)"],
        "good_synergy": ["코엔자임Q10 (혈압 조절제 복용 시 발생하는 코큐텐 체내 결핍 보완)"]
    },
    "당뇨약": {
        "dur_senior": False,
        "caution_food": ["술/알코올 (유산산증 및 심각한 저혈당 위험 증가)"],
        "caution_drug": ["고용량 니아신/비타민B3 (혈당 수치를 높일 수 있으므로 정밀 모니터링 필요)"],
        "good_synergy": ["비타민 B12 (메트포르민 장기 섭취에 따른 흡수 장애 및 결핍 예방)"]
    },
    "고지혈증약": {
        "dur_senior": False,
        "caution_food": ["자몽주스 (스타틴 성분 분해를 방해하여 근육통 등 부작용 급증)"],
        "caution_drug": ["고용량 홍국 (붉은 누룩곰팡이 성분이 고지혈증약 성분과 겹쳐 독성 위험 증가)"],
        "good_synergy": ["코엔자임Q10 (스타틴의 생합성 저해에 따른 체내 코큐텐 보충 효과)"]
    },
    "아세트아미노펜계열": {
        "dur_senior": False,
        "caution_food": ["음주/알코올 (간 대사 경로를 교란하여 심각한 급성 간손상 우려)"],
        "caution_drug": ["복합 감기약 (동일 성분 아세트아미노펜의 일일 최대 상한선 4,000mg 초과 위험)"],
        "good_synergy": ["식사 유무와 무관하게 편안한 복용 가능"]
    },
    "비스테로이드소염제": {
        "dur_senior": True,
        "caution_food": ["공복 복용 피하기 (위 점막 자극 및 위장관 출혈 위험 방지를 위해 반드시 식후 복용)"],
        "caution_drug": ["다른 소염진통제 중복 복용 (위장 장애 부작용 배가)"],
        "good_synergy": ["위장보호제/제산제 병용 (위벽 손상 최소화)"]
    },
    "항응고제/아스피린": {
        "dur_senior": False,
        "caution_food": ["인삼/홍삼 (출혈 경향 증가 우려)"],
        "caution_drug": ["은행엽엑스, 고용량 오메가-3 (출혈 위험 증가)"],
        "good_synergy": ["심혈관 질환 예방"]
    }
}

# 증상별 약물 및 해결 팁 매핑
SYMPTOM_RECOMMENDER = {
    "두통 / 치통 / 생리통": {
        "drugs": ["타이레놀 (아세트아미노펜)", "이지엔6 (이부프로펜)", "나프록센 (낙센)"],
        "tip": "위장이 약한 분은 아세트아미노펜 계열을 복용하는 것을 추천하고, 염증성 통증에는 소염진통제(이부프로펜 계열)를 식후에 복용하는 것이 더 안전하둥!"
    },
    "근육통 / 관절염 / 염좌": {
        "drugs": ["이지엔6 (이부프로펜)", "낙센 (나프록센)", "록소프로펜"],
        "tip": "비스테로이드성 소염진통제는 염증 완화에 아주 탁월하지만, 빈속에 드시면 위장에 무리가 갈 수 있으니 꼭 식후 30분에 드셔주세요둥!"
    },
    "속쓰림 / 위산 역류": {
        "drugs": ["가스터 (위산분비억제제)", "알마겔 (제산제)", "레바미피드 (위장보호제)"],
        "tip": "제산제는 다른 약물의 성분 흡수를 방해할 수 있어요. 다른 약 복용 전후로 최소 2시간 간격을 두고 드시는 것이 현명하둥!"
    },
    "감기 / 몸살 / 발열": {
        "drugs": ["타이레놀", "이부프로펜 계열 종합감기약"],
        "tip": "종합감기약 안에도 타이레놀과 동일한 아세트아미노펜 성분이 들어있는 경우가 많으니, 중복해서 과다 복용하지 않도록 꼭 주의하세요둥!"
    }
}

# ==========================================
# 3. Streamlit 대시보드 UI 그리기
# ==========================================
st.title("🛡️ 성분 한눈에: 맞춤형 가족 가디언")
st.write("가족 구성원의 신체 스펙, 복용 약물, 영양제를 입력하여 맞춤형 안전 가이드를 받아보세요!")

tab1, tab2, tab3 = st.tabs(["👤 개인 프로필 및 BMI", "💊 복용 정보 입력 & 궁합", "🩺 증상 기반 약 추천"])

# --- Tab 1: 프로필 및 BMI ---
with tab1:
    st.header("👤 가족 구성원 프로필 설정")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("이름/별명", value=st.session_state.user_profile["name"])
        age = st.number_input("나이 (만)", min_value=1, max_value=120, value=st.session_state.user_profile["age"])
        gender = st.selectbox("성별", ["남성", "여성"], index=0 if st.session_state.user_profile["gender"] == "남성" else 1)
    with col2:
        height = st.number_input("키 (cm)", min_value=50.0, max_value=250.0, value=st.session_state.user_profile["height"])
        weight = st.number_input("몸무게 (kg)", min_value=10.0, max_value=200.0, value=st.session_state.user_profile["weight"])

    if st.button("프로필 정보 저장 및 BMI 확인"):
        st.session_state.user_profile = {"name": name, "age": age, "gender": gender, "height": height, "weight": weight}
        st.success("프로필 정보가 저장되었둥!")

    # BMI 계산 및 상태 시각화
    h_m = st.session_state.user_profile["height"] / 100.0
    w = st.session_state.user_profile["weight"]
    bmi = round(w / (h_m ** 2), 2)
    status, color, desc = get_bmi_status(bmi)

    st.markdown("--- ")
    st.subheader(f"📊 {st.session_state.user_profile['name']}님의 실시간 비만도(BMI) 분석")

    b_col1, b_col2 = st.columns([1, 2])
    with b_col1:
        st.metric(label="나의 BMI 지수", value=f"{bmi} kg/m²")
    with b_col2:
        st.markdown(f"<h4>현재 상태: <span style='color:{color}; font-weight:bold;'>{status}</span></h4>", unsafe_allow_html=True)
        st.info(desc)

# --- Tab 2: 복용 정보 및 분석 ---
with tab2:
    st.header("💊 현재 복용 중인 약물 및 영양제")
    st.write("약물과 주의가 필요한 음식, 상호작용 위험 정보를 제공합니다.")

    selected_drugs_input = st.multiselect(
        "약물 검색 및 등록",
        options=list(DRUG_DIRECTORY.keys()),
        default=st.session_state.selected_drugs
    )
    st.session_state.selected_drugs = selected_drugs_input

    # 분석 가이드 제공
    if st.session_state.selected_drugs:
        st.subheader("📢 복용 주의사항 및 궁합 가이드")
        for drug in st.session_state.selected_drugs:
            category = DRUG_DIRECTORY[drug]
            db_info = DRUG_DB.get(category, {})

            with st.expander(f"🔍 {drug} ({category})의 안전 복용 정보"):
                if db_info.get("dur_senior") and st.session_state.user_profile["age"] >= 60:
                    st.error("⚠️ 노인 주의 성분: 만 60세 이상 복용 시 특히 더 주의가 필요하거나 전문가 상담이 필요한 성분입니다둥!")
                st.write("**🚫 궁합이 나쁜 음식:**")
                for food in db_info.get("caution_food", []):
                    st.write(f"- {food}")
                st.write("**💊 조심해야 할 약/영양성분:**")
                for caution in db_info.get("caution_drug", []):
                    st.write(f"- {caution}")
                st.write("**✨ 좋은 상호작용 시너지:**")
                for synergy in db_info.get("good_synergy", []):
                    st.write(f"- {synergy}")
    else:
        st.info("상단에 복용 중인 약물을 추가하시면 맞춤 가이드가 노출됩니다둥!")

# --- Tab 3: 증상 기반 약 추천 ---
with tab3:
    st.header("🩺 어떤 증상이 있으신가요?")
    st.write("불편한 증상을 선택하시면 안전하고 올바르게 상비약을 복용할 수 있도록 맞춤 추천을 해 드립니다.")

    symptom = st.selectbox(
        "현재 느끼는 주요 증상을 선택해 주세요",
        options=["선택안함"] + list(SYMPTOM_RECOMMENDER.keys())
    )

    if symptom != "선택안함":
        rec_info = SYMPTOM_RECOMMENDER[symptom]
        st.success(f"💡 **{symptom}**에 추천되는 일반의약품 목록")

        # 추천 약물 카드 형태 리스트업
        for item in rec_info["drugs"]:
            st.markdown(f"*   **{item}**")

        st.warning(f"ℹ️ **전문가 보조 가이드 팁:** {rec_info['tip']}")

        st.markdown("""
        ⚠️ *주의: 제공되는 추천 및 가이드는 참고용 의학 정보입니다. 고열이 지속되거나 심각한 통증 시 반드시 병원을 방문해 주세요.*
        """)
    else:
        st.info("증상을 선택하시면 맞춤형 추천 결과를 바로 확인하실 수 있둥!")
