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
