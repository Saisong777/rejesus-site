import streamlit as st
import pandas as pd
import altair as alt
import requests
from gtts import gTTS
from io import BytesIO

# ==========================================
# 1. 系統與 CSS 設定
# ==========================================
st.set_page_config(
    page_title="Re:Jesus - 經文即時版",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .highlight-box {background-color: #f0f7ff; padding: 15px; border-radius: 8px; border: 1px solid #cce5ff;}
    .verse-text {font-size: 1.1em; line-height: 1.6; color: #2c3e50; background-color: #fdfdfd; padding: 10px; border-left: 4px solid #4a90e2;}
    .stButton button {width: 100%;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 資料庫與對照表
# ==========================================

# 書卷名轉換表 (縮寫 -> API 英文名)
BOOK_MAP = {
    "Mt": "Matthew", "Mk": "Mark", "Lk": "Luke", "Jn": "John",
    "太": "Matthew", "可": "Mark", "路": "Luke", "約": "John"
}

# 地點座標
LOCATION_COORDS = {
    "耶路撒冷": [31.7683, 35.2137], "聖殿": [31.7781, 35.2360], "拿撒勒": [32.7019, 35.3035],
    "迦百農": [32.8810, 35.5749], "伯利恆": [31.7049, 35.2038], "加利利": [32.8, 35.6],
    "加利利海": [32.82, 35.58], "橄欖山": [31.7791, 35.2435], "馬可樓": [31.7717, 35.2294],
    "耶利哥": [31.856, 35.444], "撒馬利亞": [32.1848, 35.2546], "迦拿": [32.7445, 35.3375],
    "格拉森": [32.7937, 35.6534], "伯大尼": [31.7716, 35.2604], "以馬忤斯": [31.8396, 35.0118]
}

# 簡單的繁簡轉換字典 (修正 API 常見簡體字)
TC_CONVERT = {
    "耶穌": "耶穌", "祂": "祂", "神": "神", "灵": "靈", "义": "義", "爱": "愛",
    "见": "見", "体": "體", "国": "國", "书": "書", "听": "聽", "门": "門",
    "祷": "禱", "应": "應", "显": "顯", "据": "據", "圣": "聖", "稣": "穌"
}

# ==========================================
# 3. 核心函數庫
# ==========================================

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        df['lat'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[0])
        df['lon'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[1])
        return df
    except FileNotFoundError: return None

@st.cache_data(ttl=3600) # 快取1小時，避免重複呼叫 API
def fetch_bible_text(ref_string):
    """
    呼叫公開 API 抓取經文
    輸入: "Mt 5:3" 或 "太 5:3"
    輸出: 經文文字
    """
    if pd.isna(ref_string) or str(ref_string) == "nan":
        return None

    try:
        # 1. 簡單解析 (例如 "Mt 5:3-10")
        parts = str(ref_string).split()
        book_abbr = parts[0] # "Mt"
        chapter_verse = parts[1] if len(parts) > 1 else "" # "5:3-10"
        
        # 轉換書卷名
        api_book = BOOK_MAP.get(book_abbr, book_abbr)
        
        # 2. 呼叫 bible-api.com (免費、免金鑰)
        # 格式: https://bible-api.com/Matthew+5:3-10?translation=cuv
        url = f"https://bible-api.com/{api_book}+{chapter_verse}?translation=cuv"
        response = requests.get(url, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            raw_text = data['text']
            
            # 3. 簡單繁簡處理
            for s, t in TC_CONVERT.items():
                raw_text = raw_text.replace(s, t) # 如果原文是簡體，盡量轉回常用繁體
                
            return raw_text
        else:
            return "（無法自動抓取此段經文，請點擊下方按鈕前往閱讀）"
    except:
        return None

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='zh-TW')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# ==========================================
# 4. UI 顯示元件
# ==========================================

def render_event_card(row):
    """渲染單一事件卡片，包含經文抓取功能"""
    with st.container():
        st.markdown(f"""
        <div class="highlight-box">
            <h3>{row['事件名稱']}</h3>
            <p style="color:#666">📍 {row['地點']} | 🗓️ {row['季節']}</p>
            <p style="font-size:1.1em; font-weight:bold;">{row['福音中心']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- 經文互動區 (核心修改) ---
        ref = row['經文總覽']
        with st.expander(f"📖 閱讀經文 ({ref})"):
            # 1. 嘗試抓取
            fetched_text = fetch_bible_text(ref)
            
            if fetched_text and "無法" not in fetched_text:
                st.markdown(f"<div class='verse-text'>{fetched_text}</div>", unsafe_allow_html=True)
                st.caption("來源: CUV (自動抓取，可能包含簡體字)")
            else:
                st.warning("此經文格式較複雜，建議直接前往網站閱讀。")
            
            # 2. 提供外部連結 (備案)
            # 建立 YouVersion 連結
            yv_book = BOOK_MAP.get(str(ref).split()[0], "MAT")[:3].upper() # 轉成 MAT, MRK
            yv_url = f"https://www.bible.com/zh-TW/bible/46/{yv_book}.1.CUNP"
            st.link_button("🔗 前往 YouVersion 閱讀完整章節", yv_url)

        # 語音按鈕
        if st.button("🔊 聽聽看", key=f"btn_{row['EventID']}"):
            txt = f"{row['事件名稱']}。{row['福音中心']}"
            audio = text_to_speech(txt)
            if audio: st.audio(audio)
            
        st.divider()

# ==========================================
# 5. 主程式
# ==========================================
def main():
    df = load_data()
    if df is None: st.error("❌ 找不到 data.csv"); return

    with st.sidebar:
        st.title("✝️ Re:Jesus 9.0")
        menu = st.radio("功能選單", ["🏠 首頁總覽", "🔍 資料庫查詢", "👣 主題路徑", "💊 生命處方", "🗺️ 地圖"])

    # === 1. 首頁 ===
    if menu == "🏠 首頁總覽":
        st.header("🏠 今日靈糧")
        if st.button("✨ 隨機抽取", type="primary"):
            st.session_state['daily'] = df.sample(1).iloc[0]
            
        if 'daily' in st.session_state:
            render_event_card(st.session_state['daily'])

    # === 2. 資料庫查詢 (支援經文顯示) ===
    elif menu == "🔍 資料庫查詢":
        st.header("🔍 搜尋資料庫")
        search = st.text_input("輸入關鍵字 (如: 彼得, 醫治)")
        
        # 篩選
        out = df.copy()
        if search:
            out = out[out.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        
        st.markdown(f"找到 **{len(out)}** 筆結果：")
        
        # 顯示前 20 筆 (避免 API 呼叫過多)
        for i, row in out.head(20).iterrows():
            render_event_card(row)
            
        if len(out) > 20:
            st.info("⚠️ 為了顯示效能，僅列出前 20 筆。請嘗試更精確的關鍵字。")

    # === 3. 主題路徑 ===
    elif menu == "👣 主題路徑":
        st.header("👣 主題探索")
        path = st.selectbox("選擇路徑", ["🌟 神蹟之路", "🔥 受難週", "⛰️ 登山寶訓"])
        
        # 簡易篩選邏輯
        if path == "🌟 神蹟之路":
            mask = df['事件名稱'].str.contains("醫治|趕鬼|復活|變水")
        elif path == "🔥 受難週":
            mask = df['季節'].str.contains("週")
        else:
            mask = df['事件名稱'].str.contains("寶訓|八福")
            
        path_df = df[mask]
        st.success(f"此路徑共有 {len(path_df)} 站")
        
        for i, row in path_df.iterrows():
            st.markdown(f"#### Step {i+1}: {row['事件名稱']}")
            render_event_card(row)

    # === 4. 生命處方 ===
    elif menu == "💊 生命處方":
        st.header("💊 生命處方")
        feel = st.selectbox("心情", ["焦慮", "孤單", "憤怒"])
        key_map = {"焦慮": "平安", "孤單": "接納", "憤怒": "饒恕"}
        
        res = df[df['福音中心'].str.contains(key_map[feel])].head(3)
        for i, row in res.iterrows():
            render_event_card(row)

    # === 5. 地圖 ===
    elif menu == "🗺️ 地圖":
        st.header("🌍 互動地圖")
        st.map(df.dropna(subset=['lat', 'lon']), size=20, color='#FF4B4B')

if __name__ == "__main__":
    main()
