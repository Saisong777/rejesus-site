import streamlit as st
import pandas as pd

# --- 網頁設定 ---
st.set_page_config(
    page_title="Re:Jesus - 耶穌的春夏秋冬",
    page_icon="✝️",
    layout="wide"
)

# --- 載入資料函數 ---
@st.cache_data
def load_data():
    # 讀取 CSV，請確保檔案名稱與這裡一致
    try:
        df = pd.read_csv("data.csv")
        return df
    except FileNotFoundError:
        return None

# --- 主程式 ---
def main():
    # 側邊欄：網站標題與簡介
    st.sidebar.title("✝️ Re:Jesus")
    st.sidebar.markdown("讓人們透過網站，輕鬆的認識耶穌。")
    st.sidebar.info("資料來源：耶穌的春夏秋冬資料庫")

    # 載入資料
    df = load_data()
    
    if df is None:
        st.error("找不到資料檔 (data.csv)。請確認檔案是否已上傳至 GitHub。")
        return

    # --- 搜尋與篩選區 ---
    st.sidebar.header("🔍 篩選與搜尋")
    
    # 1. 關鍵字搜尋
    search_query = st.sidebar.text_input("搜尋關鍵字 (例如: 神蹟, 醫治, 耶路撒冷)")
    
    # 2. 季節篩選
    all_seasons = df['季節'].unique().tolist()
    selected_seasons = st.sidebar.multiselect("選擇季節/時期", all_seasons, default=all_seasons)
    
    # 3. 地點篩選
    all_locations = df['地點'].unique().tolist()
    selected_locations = st.sidebar.multiselect("選擇地點", all_locations)

    # --- 資料過濾邏輯 ---
    filtered_df = df.copy()
    
    # 季節過濾
    if selected_seasons:
        filtered_df = filtered_df[filtered_df['季節'].isin(selected_seasons)]
    
    # 地點過濾
    if selected_locations:
        filtered_df = filtered_df[filtered_df['地點'].isin(selected_locations)]
        
    # 關鍵字搜尋 (搜尋 事件名稱, 福音中心, 經文總覽)
    if search_query:
        mask = (
            filtered_df['事件名稱'].astype(str).str.contains(search_query, case=False) |
            filtered_df['福音中心'].astype(str).str.contains(search_query, case=False) |
            filtered_df['經文總覽'].astype(str).str.contains(search_query, case=False)
        )
        filtered_df = filtered_df[mask]

    # --- 網站主內容 ---
    st.title("Re:Jesus 耶穌生平探索")
    st.markdown(f"共找到 **{len(filtered_df)}** 筆關於耶穌的記載")
    st.divider()

    # 展示資料 (使用卡片式呈現)
    for index, row in filtered_df.iterrows():
        # 標題區塊
        with st.expander(f"📖 {row['EventID']} | {row['事件名稱']} ({row['大約日期']})", expanded=True):
            
            # 分兩欄顯示詳細資訊
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"### 💡 福音中心")
                st.info(row['福音中心'])
                
                if pd.notna(row['福音中心_備註']):
                    st.caption(f"備註: {row['福音中心_備註']}")
                
                st.markdown("---")
                st.markdown(f"**📍 地點**: {row['地點']}")
                st.markdown(f"**🗓️ 季節**: {row['季節']}")
                
            with col2:
                st.markdown("### 📜 相關經文")
                st.write(f"**{row['經文總覽']}**")
                
                # 顯示各卷福音書經文 (如果有的話)
                refs = []
                if pd.notna(row['經文_太']): refs.append(f"太: {row['經文_太']}")
                if pd.notna(row['經文_可']): refs.append(f"可: {row['經文_可']}")
                if pd.notna(row['經文_路']): refs.append(f"路: {row['經文_路']}")
                if pd.notna(row['經文_約']): refs.append(f"約: {row['經文_約']}")
                
                for ref in refs:
                    st.text(ref)

            # 額外資訊：神學主題與焦點
            st.markdown("---")
            tags = [f"#{row['神學主題']}", f"#{row['焦點']}"]
            if pd.notna(row['耶穌品格']):
                 tags.append(f"#{row['耶穌品格']}")
            
            st.markdown(" ".join([f"`{tag}`" for tag in tags]))

if __name__ == "__main__":
    main()