import streamlit as st
import pandas as pd
import altair as alt

# --- 1. 網頁設定 ---
st.set_page_config(
    page_title="Re:Jesus - 耶穌的春夏秋冬",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS 樣式美化 ---
st.markdown("""
<style>
    .big-font {font-size:18px !important;}
    .path-card {
        background-color: #f8f9fa;
        border-left: 5px solid #4a90e2;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 5px;
    }
    .check-matrix {
        font-family: monospace;
        background-color: #f0f2f6;
        padding: 5px;
        border-radius: 4px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 核心函數 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        # 資料清洗
        df['主分類'] = df['事件分類'].astype(str).apply(lambda x: x.split('>')[0] if pd.notna(x) else "其他")
        
        # 建立福音書檢查欄位 (用於矩陣)
        df['有_太'] = df['經文_太'].notna()
        df['有_可'] = df['經文_可'].notna()
        df['有_路'] = df['經文_路'].notna()
        df['有_約'] = df['經文_約'].notna()
        return df
    except FileNotFoundError:
        return None

# --- 4. 主題路徑定義 (這是策展的核心) ---
# 您可以在這裡自由新增更多「片單」
CURATED_PATHS = {
    "🌟 耶穌的神蹟 (精選)": {
        "desc": "看見耶穌如何透過超自然的大能，帶下神的國度與憐憫。",
        "keywords": ["醫治", "趕鬼", "變水為酒", "五餅二魚", "平靜風浪", "復活"]
    },
    "🔥 受難週：最後的七天": {
        "desc": "跟隨耶穌走過他在世上的最後一週，從榮耀進城到十架受死。",
        "filter_season": ["週日", "週一", "週二", "週三", "週四", "週五", "週六"] # 透過季節欄位過濾
    },
    "⛰️ 登山寶訓與教導": {
        "desc": "聆聽天國君王的憲章，重新定義什麼是有福的人。",
        "keywords": ["八福", "登山寶訓", "禱告", "比喻", "論"]
    },
    "💧 獨特的約翰視角": {
        "desc": "探索那些只記載在約翰福音，關於生命、光與愛的深刻對話。",
        "special_logic": "john_only"
    }
}

# --- 5. 主程式 ---
def main():
    df = load_data()
    if df is None:
        st.error("❌ 請確認 data.csv 是否存在於 GitHub")
        return

    # --- 側邊欄 ---
    with st.sidebar:
        st.title("✝️ Re:Jesus")
        st.caption("探索・對照・深思")
        
        # 導航選單
        menu = st.radio("功能選單", ["👣 主題探索路徑", "📂 完整資料庫", "📊 福音書透視鏡", "🗺️ 互動地圖"])
        
        st.divider()
        st.markdown("**關於網站**")
        st.caption("本網站旨在讓人們透過視覺化與互動，輕鬆認識耶穌生平。")

    # === 功能 1: 主題探索路徑 (Curated Paths) ===
    if menu == "👣 主題探索路徑":
        st.header("👣 跟隨耶穌的腳蹤")
        st.markdown("不知道從哪裡開始？選擇一條我們為您整理的「主題路徑」，開始您的探索旅程。")
        
        # 選擇路徑
        selected_path_name = st.selectbox("請選擇一條路徑：", list(CURATED_PATHS.keys()))
        path_info = CURATED_PATHS[selected_path_name]
        
        st.info(f"📋 **路徑簡介**：{path_info['desc']}")
        
        # 篩選邏輯
        path_df = df.copy()
        
        if "keywords" in path_info:
            # 關鍵字篩選
            keyword_mask = path_df.apply(lambda row: any(k in str(row['事件名稱']) for k in path_info['keywords']), axis=1)
            path_df = path_df[keyword_mask]
            
        elif "filter_season" in path_info:
            # 季節篩選 (模糊比對，只要包含 "週五" 就算)
            season_mask = path_df['季節'].apply(lambda x: any(d in str(x) for d in path_info['filter_season']))
            path_df = path_df[season_mask]
            
        elif "special_logic" in path_info and path_info['special_logic'] == "john_only":
            # 只在約翰福音出現的事件
            path_df = path_df[path_df['有_約'] & ~path_df['有_太'] & ~path_df['有_可'] & ~path_df['有_路']]

        # 顯示結果
        st.write(f"此路徑包含 **{len(path_df)}** 個事件：")
        
        # 使用進度條增強儀式感
        progress_text = "路徑預覽"
        my_bar = st.progress(0, text=progress_text)
        my_bar.progress(100, text=f"載入完成！準備開始")

        # 時間軸式呈現
        for i, (index, row) in enumerate(path_df.iterrows()):
            with st.expander(f"Step {i+1}: {row['事件名稱']} ({row['地點']})"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**💡 福音中心**：{row['福音中心']}")
                    st.caption(f"神學主題：{row['神學主題']}")
                with c2:
                    # 迷你福音矩陣
                    matrix_html = ""
                    for g, icon in [('太', row['有_太']), ('可', row['有_可']), ('路', row['有_路']), ('約', row['有_約'])]:
                        color = "#4CAF50" if icon else "#ddd" # 綠色或灰色
                        matrix_html += f"<span style='color:{color}; font-weight:bold; margin-right:5px'>{g}</span>"
                    st.markdown(f"記載：{matrix_html}", unsafe_allow_html=True)
                    st.markdown(f"📜 {row['經文總覽']}")

    # === 功能 2: 完整資料庫 (保留強大的篩選功能) ===
    elif menu == "📂 完整資料庫":
        st.header("📂 自由探索資料庫")
        
        # 頂部篩選器
        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("🔍 關鍵字搜尋", placeholder="例如：彼得、信心...")
        with col2:
            locs = st.multiselect("📍 地點", df['地點'].unique())
        with col3:
            themes = st.multiselect("💡 神學主題", df['神學主題'].unique())

        # 執行篩選
        out = df.copy()
        if search:
            out = out[out.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        if locs:
            out = out[out['地點'].isin(locs)]
        if themes:
            out = out[out['神學主題'].isin(themes)]
            
        st.write(f"共 {len(out)} 筆資料")
        st.dataframe(
            out[['EventID', '季節', '地點', '事件名稱', '福音中心', '經文總覽']], 
            use_container_width=True,
            hide_index=True
        )

    # === 功能 3: 福音書透視鏡 (Gospel Harmony) ===
    elif menu == "📊 福音書透視鏡":
        st.header("📊 四福音書對照透視")
        st.markdown("這裡展示了四卷福音書如何從不同視角記載耶穌。你可以看到哪些事件是「大家都記了」，哪些是「獨家報導」。")
        
        # 統計數據
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("馬太記載", f"{df['有_太'].sum()} 處")
        col2.metric("馬可記載", f"{df['有_可'].sum()} 處")
        col3.metric("路加記載", f"{df['有_路'].sum()} 處")
        col4.metric("約翰記載", f"{df['有_約'].sum()} 處")
        
        st.divider()
        
        # 互動篩選：你想看怎麼樣的重疊？
        filter_type = st.radio("選擇檢視模式：", 
            ["🔍 顯示所有事件", "🌍 四福音皆有 (重要核心)", "💧 僅約翰福音 (獨家)", "🧱 符類福音 (太/可/路)"], horizontal=True)
        
        view_df = df.copy()
        if filter_type == "🌍 四福音皆有 (重要核心)":
            view_df = view_df[view_df['有_太'] & view_df['有_可'] & view_df['有_路'] & view_df['有_約']]
        elif filter_type == "💧 僅約翰福音 (獨家)":
            view_df = view_df[view_df['有_約'] & ~view_df['有_太'] & ~view_df['有_可'] & ~view_df['有_路']]
        elif filter_type == "🧱 符類福音 (太/可/路)":
            view_df = view_df[(view_df['有_太'] | view_df['有_可'] | view_df['有_路']) & ~view_df['有_約']]
            
        # 視覺化矩陣列表
        for index, row in view_df.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{row['事件名稱']}**")
                c1.caption(f"{row['福音中心']}")
                
                # 製作一個漂亮的 Checkbox 矩陣
                matrix = ""
                for g, has_it in [('太', row['有_太']), ('可', row['有_可']), ('路', row['有_路']), ('約', row['有_約'])]:
                    mark = "✅" if has_it else "⬜"
                    matrix += f"{mark} {g}　"
                c2.markdown(matrix)
                c3.markdown(f"*{row['大約日期']}*")
                st.divider()

    # === 功能 4: 互動地圖 (保留) ===
    elif menu == "🗺️ 互動地圖":
        st.header("🌍 耶穌的地理行蹤")
        # 簡單的地圖邏輯 (若無座標則僅顯示列表)
        st.info("地圖功能需要整合座標資料，目前為您展示地點分佈統計。")
        
        loc_counts = df['地點'].value_counts().reset_index()
        loc_counts.columns = ['地點', '事件數量']
        
        chart = alt.Chart(loc_counts).mark_bar().encode(
            x='事件數量',
            y=alt.Y('地點', sort='-x'),
            color=alt.value('#FF4B4B')
        )
        st.altair_chart(chart, use_container_width=True)

if __name__ == "__main__":
    main()
