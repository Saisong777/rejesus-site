import streamlit as st
import pandas as pd
import altair as alt

# --- 網頁設定 ---
st.set_page_config(
    page_title="Re:Jesus - 耶穌的春夏秋冬",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS樣式優化 ---
st.markdown("""
<style>
    .stExpander {border: 1px solid #f0f2f6; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
    .big-font {font-size:20px !important; font-weight: bold;}
    .highlight {background-color: #f0f8ff; padding: 10px; border-radius: 5px; border-left: 5px solid #4a90e2;}
</style>
""", unsafe_allow_html=True)

# --- 載入與處理資料函數 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        
        # 資料前處理：產生「主分類」 (取 '事件分類' 的第一層)
        df['主分類'] = df['事件分類'].astype(str).apply(lambda x: x.split('>')[0] if pd.notna(x) else "其他")
        
        # 處理品格標籤 (將 "信實、謙卑" 這種字串拆開成列表，方便搜尋)
        df['品格列表'] = df['耶穌品格'].astype(str).apply(lambda x: x.split('、') if pd.notna(x) and x != 'nan' else [])
        
        return df
    except FileNotFoundError:
        return None

# --- 主程式 ---
def main():
    df = load_data()
    
    if df is None:
        st.error("❌ 找不到資料檔 (data.csv)。請確認檔案是否已上傳至 GitHub。")
        return

    # --- 側邊欄：強大的篩選器 ---
    with st.sidebar:
        st.title("✝️ Re:Jesus")
        st.caption("探索耶穌生平的多維視角")
        st.divider()
        
        # 1. 關鍵字搜尋
        search_query = st.text_input("🔍 關鍵字搜尋", placeholder="搜尋經文、事件、備註...")
        
        # 2. 進階篩選器 (使用 Expander 收納，讓介面更乾淨)
        with st.expander("📂 進階篩選 (季節/地點/分類)", expanded=True):
            # 季節
            all_seasons = df['季節'].unique().tolist()
            selected_seasons = st.multiselect("🗓️ 季節", all_seasons, default=all_seasons)
            
            # 主分類
            all_categories = sorted(df['主分類'].unique().tolist())
            selected_categories = st.multiselect("🗂️ 事件階段", all_categories, default=all_categories)
            
            # 地點
            all_locations = sorted(df['地點'].unique().tolist())
            selected_locations = st.multiselect("📍 地點", all_locations)

        with st.expander("🧠 神學與品格", expanded=False):
            # 神學主題
            all_themes = sorted(df['神學主題'].astype(str).unique().tolist())
            selected_themes = st.multiselect("💡 神學主題", all_themes)
            
            # 耶穌品格 (這是個稍微複雜的處理，要抓出所有單獨的品格)
            unique_traits = set()
            for traits in df['品格列表']:
                unique_traits.update(traits)
            selected_traits = st.multiselect("❤️ 耶穌品格", sorted(list(unique_traits)))
        
        st.info(f"資料庫共有 {len(df)} 筆記載")

    # --- 資料過濾邏輯 ---
    filtered_df = df.copy()
    
    # 基礎過濾
    if selected_seasons: filtered_df = filtered_df[filtered_df['季節'].isin(selected_seasons)]
    if selected_categories: filtered_df = filtered_df[filtered_df['主分類'].isin(selected_categories)]
    if selected_locations: filtered_df = filtered_df[filtered_df['地點'].isin(selected_locations)]
    if selected_themes: filtered_df = filtered_df[filtered_df['神學主題'].isin(selected_themes)]
    
    # 品格過濾 (只要包含使用者選的任一品格就算)
    if selected_traits:
        filtered_df = filtered_df[filtered_df['品格列表'].apply(lambda x: any(trait in x for trait in selected_traits))]

    # 關鍵字搜尋
    if search_query:
        mask = (
            filtered_df['事件名稱'].astype(str).str.contains(search_query, case=False) |
            filtered_df['福音中心'].astype(str).str.contains(search_query, case=False) |
            filtered_df['經文總覽'].astype(str).str.contains(search_query, case=False) |
            filtered_df['OT_註解'].astype(str).str.contains(search_query, case=False)
        )
        filtered_df = filtered_df[mask]

    # --- 主畫面：分頁設計 ---
    tab1, tab2, tab3 = st.tabs(["📖 事件瀏覽", "📊 數據分析", "🎲 隨機探索"])

    # === 分頁 1: 事件瀏覽 ===
    with tab1:
        st.subheader(f"搜尋結果：共 {len(filtered_df)} 筆")
        
        # 顯示卡片列表
        for index, row in filtered_df.iterrows():
            # 卡片標題
            card_title = f"{row['EventID']} | {row['事件名稱']}"
            
            with st.expander(card_title, expanded=False):
                # 頂部資訊列
                c1, c2, c3 = st.columns([1,1,2])
                c1.markdown(f"**🗓️ 時間**: {row['大約日期']}")
                c2.markdown(f"**📍 地點**: {row['地點']}")
                c3.markdown(f"**🏷️ 分類**: {row['事件分類']}")
                
                st.divider()
                
                # 核心內容：左右分欄
                col_main, col_ref = st.columns([1.5, 1])
                
                with col_main:
                    st.markdown("#### 💡 福音中心與焦點")
                    st.markdown(f"<div class='highlight'>{row['福音中心']}</div>", unsafe_allow_html=True)
                    st.caption(f"原文/備註: {row['福音中心_原文']}")
                    
                    st.markdown("---")
                    st.markdown(f"**神學主題**: `{row['神學主題']}`")
                    st.markdown(f"**耶穌品格**: `{row['耶穌品格']}`")
                    
                    if pd.notna(row['舊約串珠']):
                        st.markdown("---")
                        st.markdown(f"**🔗 舊約串珠**: {row['舊約串珠']}")
                        st.info(f"註解: {row['OT_註解']}")

                with col_ref:
                    st.markdown("#### 📜 四福音對照")
                    # 自動偵測有哪些經文，並動態顯示
                    gospels = {
                        "太": row['經文_太'],
                        "可": row['經文_可'],
                        "路": row['經文_路'],
                        "約": row['經文_約']
                    }
                    
                    has_scripture = False
                    for book, ref in gospels.items():
                        if pd.notna(ref):
                            st.text_input(f"{book} (點擊複製)", value=ref, key=f"{row['EventID']}_{book}", disabled=False)
                            has_scripture = True
                    
                    if not has_scripture:
                        st.caption("無對應經文")

    # === 分頁 2: 數據分析 ===
    with tab2:
        st.header("📊 耶穌生平的數據視角")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("📍 最常發生的地點 (Top 10)")
            if not filtered_df.empty:
                loc_counts = filtered_df['地點'].value_counts().head(10).reset_index()
                loc_counts.columns = ['地點', '次數']
                chart_loc = alt.Chart(loc_counts).mark_bar().encode(
                    x=alt.X('次數', title=None),
                    y=alt.Y('地點', sort='-x', title=None),
                    color=alt.value('#4a90e2'),
                    tooltip=['地點', '次數']
                )
                st.altair_chart(chart_loc, use_container_width=True)
        
        with col_b:
            st.subheader("💡 神學主題分佈")
            if not filtered_df.empty:
                theme_counts = filtered_df['神學主題'].value_counts().head(10).reset_index()
                theme_counts.columns = ['主題', '次數']
                chart_theme = alt.Chart(theme_counts).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="次數", type="quantitative"),
                    color=alt.Color(field="主題", type="nominal"),
                    tooltip=['主題', '次數']
                )
                st.altair_chart(chart_theme, use_container_width=True)

    # === 分頁 3: 隨機探索 ===
    with tab3:
        st.header("🎲 每日一瞥")
        st.markdown("不知道從哪裡開始？讓系統為您隨機挑選一個事件，重新認識耶穌。")
        
        if st.button("✨ 隨機抽取一個事件", type="primary"):
            if not df.empty:
                random_row = df.sample(1).iloc[0]
                st.success(f"為您選出：{random_row['事件名稱']}")
                
                st.markdown(f"### {random_row['事件名稱']}")
                st.markdown(f"**{random_row['經文總覽']}**")
                
                st.markdown(f"""
                > {random_row['福音中心']}
                """)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**地點**: {random_row['地點']}")
                    st.markdown(f"**季節**: {random_row['季節']}")
                with c2:
                    st.markdown(f"**神學**: {random_row['神學主題']}")
                    st.markdown(f"**焦點**: {random_row['焦點']}")

if __name__ == "__main__":
    main()
