import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")

        if st.session_state.get("logged_in"):
            st.success(f"Welcome, {st.session_state.get('user_email')}!")

        st.markdown("""
        ---
        ### 📊 About This App
        This web app allows you to upload and analyze population trends from a CSV file.

        **Key Features:**
        - Handle missing values and data formatting
        - View national population trends over the years
        - Analyze regional population changes and growth rates
        - Visualize trends with interactive charts and color-coded tables

        **Data Format Expected (column names in Korean):**
        - `연도` (Year)
        - `지역` (Region)
        - `인구` (Population)
        - `출생아수(명)` (Number of births)
        - `사망자수(명)` (Number of deaths)

        Upload your `population_trends.csv` file in the EDA section to begin analysis.
        """)


# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📈 Population Trends Analysis (population_trends.csv)")
        uploaded_pop = st.file_uploader("Upload population_trends.csv", type="csv")
        if uploaded_pop:
            self.analyze_population_data(uploaded_pop)

    def analyze_population_data(self, file):
        df = pd.read_csv(file)

        # Replace '-' with 0 for Sejong region
        df.loc[df['지역'] == '세종'] = df.loc[df['지역'] == '세종'].replace('-', 0)

        # Convert numeric columns
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Map Korean region names to English
        region_map = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
            '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
            '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam',
            '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju', '전국': 'National'
        }
        df['지역'] = df['지역'].map(region_map).fillna(df['지역'])

        tabs = st.tabs(["Summary", "Yearly Trends", "Regional Trends", "Top Changes", "Visualization"])

        with tabs[0]:
            st.subheader("✅ Dataset Info")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
            st.dataframe(df.describe())

        with tabs[1]:
            st.subheader("📉 National Population Trends")
            nat_df = df[df['지역'] == 'National']
            fig, ax = plt.subplots()
            sns.lineplot(data=nat_df, x='연도', y='인구', marker='o', ax=ax)
            ax.set_title("Population Over Time")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")

            recent = nat_df.sort_values('연도').tail(3)
            birth_avg = recent['출생아수(명)'].mean()
            death_avg = recent['사망자수(명)'].mean()
            latest_year = recent['연도'].max()
            latest_pop = recent[nat_df['연도'] == latest_year]['인구'].values[0]
            projected_pop = latest_pop + (birth_avg - death_avg) * (2035 - latest_year)

            ax.axvline(2035, color='gray', linestyle='--')
            ax.scatter([2035], [projected_pop], color='red')
            ax.text(2035, projected_pop, f"2035: {int(projected_pop):,}", color='red')
            st.pyplot(fig)

        with tabs[2]:
            st.subheader("📍 Regional Change (5 Years)")
            last_year = df['연도'].max()
            base_year = last_year - 5
            recent_df = df[df['연도'].isin([base_year, last_year])]
            pivot = recent_df.pivot(index='지역', columns='연도', values='인구')
            pivot = pivot.drop('National', errors='ignore')
            pivot['Change'] = pivot[last_year] - pivot[base_year]
            pivot['GrowthRate'] = pivot['Change'] / pivot[base_year] * 100

            sorted_df = pivot.sort_values('Change', ascending=False)

            fig, ax = plt.subplots(figsize=(10, 8))
            sns.barplot(x=sorted_df['Change']/1000, y=sorted_df.index.astype(str), ax=ax)
            for i, v in enumerate(sorted_df['Change']/1000):
                ax.text(v, i, f"{v:,.0f}", va='center')
            ax.set_title("Population Change (5Y)")
            ax.set_xlabel("Change (thousands)")
            st.pyplot(fig)

            fig2, ax2 = plt.subplots(figsize=(10, 8))
            sns.barplot(x=sorted_df['GrowthRate'], y=sorted_df.index.astype(str), ax=ax2)
            for i, v in enumerate(sorted_df['GrowthRate']):
                ax2.text(v, i, f"{v:.1f}%", va='center')
            ax2.set_title("Population Growth Rate (%)")
            ax2.set_xlabel("Growth Rate (%)")
            st.pyplot(fig2)

        with tabs[3]:
            st.subheader("🚀 Top 100 Annual Changes")
            df_sorted = df[df['지역'] != 'National'].sort_values(['지역', '연도'])
            df_sorted['Change'] = df_sorted.groupby('지역')['인구'].diff()
            top100 = df_sorted.sort_values('Change', ascending=False).head(100)
            top100_display = top100[['연도', '지역', '인구', 'Change']].copy()
            st.dataframe(
                top100_display.style.format({"Change": "{:,}"}).background_gradient(
                    subset=['Change'], cmap='RdBu_r', axis=0)
            )

        with tabs[4]:
            st.subheader("📊 Area Chart by Region")
            pivot_map = df.pivot(index='연도', columns='지역', values='인구')
            fig, ax = plt.subplots(figsize=(14, 6))
            pivot_map = pivot_map.fillna(0)
            pivot_map.plot.area(ax=ax, legend=True)
            ax.set_title("Population Over Time by Region")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
            st.pyplot(fig)




# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
