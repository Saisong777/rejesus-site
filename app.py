import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# --- 網頁設定 ---
st.set_page_config(
    page_title="Re:Jesus - 耶穌的春夏秋冬",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 美化 (讓介面更像 App) ---
st.markdown("""
<style>
    .stChatInput {border-radius: 20px;}
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #FF4B4B;
    }
    .big-number {
        font-size: 40px; 
        font-weight: bold; 
        color: #FF4B4B;
    }
    .map-container {border: 2px solid #eee; border-radius: 10px; overflow: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 座標資料庫 (將聖經地點轉為經緯度) ---
# 這是為了地圖功能手動建立的對照表
LOCATION_COORDS = {
    "耶路撒冷": [31.7683, 35.2137], "聖殿": [31.7781, 35.2360], "各各他": [31.7797, 35.2299],
    "拿撒勒": [32.7019, 35.3035], "迦百農": [32.8810, 35.5749], "伯利恆": [31.7049, 35.2038],
    "約旦河": [31.856, 35.555], "加利利": [32.8, 35.6], "加利利海": [32.82, 35.58],
    "八福山": [32.8805, 35.5558], "橄欖山": [31.7791, 35.2435], "馬可樓": [31.7717, 35.2294],
    "客西馬尼": [31.7794, 35.2401], "耶利哥": [31.856, 35.444], "撒馬利亞": [32.1848, 35.2546],
    "迦拿": [32.7445, 35.3375], "拿因城": [32.6300, 35.3400], "格拉森": [32.7937, 35.6534],
    "該撒利亞腓立比": [33.2486, 35.6917], "伯大尼": [31.7716, 35.2604], "以馬忤斯": [31.8396, 35.0118],
    "推羅": [33.2709, 35.1963], "西頓": [33.5599, 35.3756], "低加波利": [32.7, 35.8],
    "比利亞": [32.0, 35.6], "猶大": [31.6, 35.1]
}

# --- 函數區 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        # 資料清洗
        df['主分類'] = df['事件分類'].astype(str).apply(lambda x: x.split('>')[0] if pd.notna(x) else "其他")
        return df
    except FileNotFoundError:
        return None

def get_lat_lon(loc_name):
    """模糊比對地點名稱以獲取座標"""
    if pd.isna(loc_name): return None
    for key, coords in LOCATION_COORDS.items():
        if key in str(loc_name):
            return coords
    return None # 找不到座標

# --- 主程式 ---
def main():
    df = load_data()
    if df is None:
        st.error("請確認 data.csv 是否存在")
        return

    # --- 側邊欄導航 ---
    with st.sidebar:
        st.title("✝️ Re:Jesus")
        st.caption("互動式耶穌生平資料庫")
        
        mode = st.radio(
            "選擇模式", 
            ["🏠 首頁總覽", "🗺️ 聖地地圖", "💬 智慧導覽", "🃏 記憶閃卡", "📂 資料庫查詢"]
        )
        st.divider()
        st.info("資料來源：耶穌的春夏秋冬")

    # === 1. 首頁總覽 ===
    if mode == "🏠 首頁總覽":
        st.title("歡迎來到 Re:Jesus")
        st.markdown("這是一個讓人們 **快速、無痛、互動** 認識耶穌的空間。")
        
        # 關鍵數據指標
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("記載事件", f"{len(df)} 件")
        c2.metric("涵蓋地點", f"{df['地點'].nunique()} 處")
        c3.metric("跨越時間", "約 33 年")
        c4.metric("引用經文", "四福音書")
        
        st.divider()
        
        # 隨機推薦
        st.subheader("💡 今日焦點")
        daily = df.sample(1).iloc[0]
        st.markdown(f"""
        <div class="card">
            <h3>{daily['事件名稱']}</h3>
            <p style="color:gray">📍 {daily['地點']} | 🗓️ {daily['季節']}</p>
            <p><b>{daily['福音中心']}</b></p>
            <hr>
            <p><i>{daily['福音中心_備註'] or ''}</i></p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("換一個焦點"):
            st.rerun()

    # === 2. 聖地地圖 ===
    elif mode == "🗺️ 聖地地圖":
        st.title("🌍 耶穌的足跡")
        st.markdown("在地圖上探索耶穌的事工分佈。圓點越大，代表在該地發生的事件越多。")
        
        # 準備地圖資料
        map_data = df['地點'].value_counts().reset_index()
        map_data.columns = ['地點', '事件數']
        
        # 取得座標
        coords = map_data['地點'].apply(get_lat_lon)
        map_data['lat'] = coords.apply(lambda x: x[0] if x else None)
        map_data['lon'] = coords.apply(lambda x: x[1] if x else None)
        map_data = map_data.dropna(subset=['lat', 'lon']) # 移除找不到座標的點
        
        # 調整圓點大小
        map_data['size'] = map_data['事件數'] * 50
        
        # 顯示地圖
        st.map(map_data, latitude='lat', longitude='lon', size='size', zoom=7, color='#FF4B4B')
        
        # 下方顯示地點詳情
        col1, col2 = st.columns([1, 2])
        with col1:
            selected_loc = st.selectbox("選擇地點查看詳細事件", map_data['地點'].tolist())
        
        with col2:
            loc_events = df[df['地點'] == selected_loc]
            st.write(f"**{selected_loc}** 發生了 {len(loc_events)} 件事：")
            st.dataframe(loc_events[['大約日期', '事件名稱', '神學主題']], hide_index=True)

    # === 3. 智慧導覽 (Chat) ===
    elif mode == "💬 智慧導覽":
        st.title("💬 與資料對話")
        st.markdown("輸入任何您感興趣的關鍵字（如：**信心、醫治、彼得、安息日**），系統將為您整理相關的耶穌生平。")
        
        # 模擬聊天介面
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "您好！想了解耶穌的哪方面？請輸入關鍵字。"}]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("請輸入關鍵字..."):
            # 顯示使用者輸入
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            # 搜尋邏輯
            mask = (
                df['事件名稱'].astype(str).str.contains(prompt, case=False) |
                df['福音中心'].astype(str).str.contains(prompt, case=False) |
                df['神學主題'].astype(str).str.contains(prompt, case=False) |
                df['耶穌品格'].astype(str).str.contains(prompt, case=False)
            )
            results = df[mask]
            
            # 生成回應
            if not results.empty:
                response = f"我找到了 **{len(results)}** 個與「{prompt}」相關的事件。\n\n"
                for i, row in results.head(5).iterrows():
                    response += f"- **{row['事件名稱']}** ({row['地點']})：{row['福音中心']}\n"
                if len(results) > 5:
                    response += f"\n*...以及其他 {len(results)-5} 筆資料 (請至資料庫查詢頁面查看完整清單)*"
            else:
                response = f"抱歉，我在資料庫中找不到關於「{prompt}」的明確記載。您可以試試其他關鍵字，例如「神蹟」或「禱告」。"
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)

    # === 4. 記憶閃卡 ===
    elif mode == "🃏 記憶閃卡":
        st.title("🃏 認識耶穌・記憶閃卡")
        st.caption("點擊按鈕抽取一張卡片，試著猜猜看這是什麼事件？")
        
        if 'flashcard' not in st.session_state:
            st.session_state.flashcard = df.sample(1).iloc[0]
            st.session_state.show_answer = False

        c1, c2, c3 = st.columns([1, 1, 2])
        if c1.button("🔄 抽一張新卡片"):
            st.session_state.flashcard = df.sample(1).iloc[0]
            st.session_state.show_answer = False
            st.rerun()
            
        card = st.session_state.flashcard
        
        # 卡片顯示區
        st.markdown("---")
        st.markdown("### 題目：這是什麼事件？")
        
        # 顯示題目線索
        st.info(f"💡 線索：{card['福音中心']}")
        st.write(f"📍 地點：{card['地點']}")
        st.write(f"🏷️ 神學主題：{card['神學主題']}")
        
        # 答案區
        if st.button("👀 看答案"):
            st.session_state.show_answer = True
            
        if st.session_state.show_answer:
            st.success(f"答案：{card['事件名稱']}")
            st.markdown(f"**📖 經文**：{card['經文總覽']}")
            if pd.notna(card['福音中心_備註']):
                st.caption(f"備註：{card['福音中心_備註']}")

    # === 5. 資料庫查詢 (原本的功能) ===
    elif mode == "📂 資料庫查詢":
        st.title("📂 完整資料庫")
        
        # 篩選器
        col1, col2 = st.columns(2)
        with col1:
            search = st.text_input("🔍 搜尋")
        with col2:
            season = st.multiselect("🗓️ 季節", df['季節'].unique())
            
        # 篩選邏輯
        out = df.copy()
        if season: out = out[out['季節'].isin(season)]
        if search:
            out = out[out.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
            
        st.dataframe(
            out[['EventID', '大約日期', '地點', '事件名稱', '神學主題', '福音中心', '經文總覽']],
            use_container_width=True,
            hide_index=True
        )

if __name__ == "__main__":
    main()
