import streamlit as st
import pandas as pd
import requests
import altair as alt
import random
from opencc import OpenCC
from io import BytesIO
from gtts import gTTS
from datetime import datetime, timedelta
import uuid

# ==========================================
# 1. 系統設定與 CSS 美學 (Design System)
# ==========================================
st.set_page_config(
    page_title="Re:Jesus | 遇見真實的耶穌",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化繁簡轉換器
cc = OpenCC('s2twp')

# 注入美學 CSS
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;700&family=Noto+Sans+TC:wght@300;400;700&display=swap');

    /* 全域設定 */
    .stApp { background-color: #faf9f6; } /* 米白底色 */
    
    h1, h2, h3, h4 { font-family: 'Noto Serif TC', serif !important; color: #2c3e50; }
    p, div, label, span { font-family: 'Noto Sans TC', sans-serif; color: #4a4a4a; }

    /* 卡片設計 (Card UI) */
    .event-card {
        background-color: white;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f0;
        margin-bottom: 25px;
        transition: transform 0.2s ease-in-out;
    }
    .event-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(184, 134, 11, 0.15);
        border-color: #d4af37;
    }

    /* 標籤樣式 */
    .tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: bold;
        margin-right: 8px;
    }
    .tag-season { background-color: #e3f2fd; color: #1565c0; }
    .tag-loc { background-color: #f3e5f5; color: #7b1fa2; }
    .tag-theme { background-color: #e8f5e9; color: #2e7d32; }

    /* 經文引用區 */
    .gospel-quote {
        font-family: 'Noto Serif TC', serif;
        font-size: 1.4em;
        line-height: 1.6;
        color: #2c3e50;
        border-left: 5px solid #B8860B; /* 金色邊條 */
        padding-left: 20px;
        margin: 20px 0;
    }

    /* 經文閱讀區 */
    .verse-box {
        background-color: #fffbf0;
        padding: 20px;
        border-radius: 8px;
        border: 1px dashed #d4c5a0;
        font-family: 'Noto Serif TC', serif;
        font-size: 1.15em;
        line-height: 1.8;
        color: #333;
    }

    /* IG 卡片樣式 */
    .insta-card {
        width: 100%; max-width: 400px; aspect-ratio: 4/5;
        background: linear-gradient(135deg, #2c3e50 0%, #B8860B 100%);
        color: white; padding: 40px; border-radius: 20px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        text-align: center; margin: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .insta-text { font-family: 'Noto Serif TC', serif; font-size: 24px; font-weight: bold; line-height: 1.5; margin-bottom: 20px; color: white;}
    .insta-ref { font-family: 'Noto Sans TC', sans-serif; font-size: 14px; opacity: 0.8; margin-top: auto;}

    /* 按鈕優化 */
    .stButton button { border-radius: 30px; border: none; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 資料處理核心
# ==========================================

# 擴充版書卷對照表 (確保各種縮寫都能抓到)
BOOK_MAP = {
    "Mt": "Matthew", "Mk": "Mark", "Lk": "Luke", "Jn": "John",
    "Mat": "Matthew", "Mrk": "Mark", "Luk": "Luke", "Jhn": "John",
    "太": "Matthew", "可": "Mark", "路": "Luke", "約": "John",
    "馬太": "Matthew", "馬可": "Mark", "路加": "Luke", "約翰": "John"
}

# 地點座標資料庫
LOCATION_COORDS = {
    "耶路撒冷": [31.7683, 35.2137], "聖殿": [31.7781, 35.2360], "各各他": [31.7797, 35.2299],
    "拿撒勒": [32.7019, 35.3035], "迦百農": [32.8810, 35.5749], "伯利恆": [31.7049, 35.2038],
    "約旦河": [31.856, 35.555], "加利利": [32.8, 35.6], "加利利海": [32.82, 35.58],
    "八福山": [32.8805, 35.5558], "橄欖山": [31.7791, 35.2435], "馬可樓": [31.7717, 35.2294],
    "客西馬尼": [31.7794, 35.2401], "耶利哥": [31.856, 35.444], "撒馬利亞": [32.1848, 35.2546],
    "迦拿": [32.7445, 35.3375], "格拉森": [32.7937, 35.6534], "伯大尼": [31.7716, 35.2604]
}

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        # 預先處理經文 Flag
        for g in ['太', '可', '路', '約']:
            df[f'有_{g}'] = df[f'經文_{g}'].notna()
        
        # 處理座標
        df['lat'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[0])
        df['lon'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[1])
        return df
    except FileNotFoundError: return None

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_bible_text(ref_string):
    """強健的經文抓取函數"""
    if pd.isna(ref_string) or str(ref_string).strip() == "": return None
    ref_string = str(ref_string).strip()
    
    try:
        # 處理縮寫 (如 "Mt5:3" -> "Mt 5:3")
        import re
        if " " not in ref_string:
            ref_string = re.sub(r"([a-zA-Z\u4e00-\u9fa5]+)(\d)", r"\1 \2", ref_string)
            
        parts = ref_string.split(maxsplit=1)
        book = parts[0]
        verse = parts[1] if len(parts) > 1 else ""
        
        api_book = BOOK_MAP.get(book, book) # 查不到就用原字
        
        url = f"https://bible-api.com/{api_book}+{verse}?translation=cuv"
        resp = requests.get(url, timeout=3)
        
        if resp.status_code == 200:
            text = resp.json().get('text', '')
            if text: return cc.convert(text) # 繁簡轉換
        return None
    except: return None

def text_to_speech(text):
    """文字轉語音"""
    try:
        tts = gTTS(text=text, lang='zh-TW')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# ==========================================
# 3. UI 渲染元件
# ==========================================

def render_card(row):
    """顯示美化後的事件卡片"""
    st.markdown(f"""
    <div class="event-card">
        <div>
            <span class="tag tag-season">{row['季節']}</span>
            <span class="tag tag-loc">📍 {row['地點']}</span>
            <span class="tag tag-theme">💡 {row['神學主題']}</span>
        </div>
        <h2 style="margin-top:15px; margin-bottom:10px;">{row['事件名稱']}</h2>
        <div class="gospel-quote">
            {row['福音中心']}
        </div>
        <div style="text-align: right; font-size: 0.9em; color: #888;">
            📖 經文出處：{row['經文總覽']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 互動按鈕區
    c1, c2 = st.columns([1, 5])
    
    # 語音按鈕
    with c1:
        if st.button("🔊 聽聽看", key=f"tts_{row['EventID']}"):
            txt = f"{row['事件名稱']}。{row['福音中心']}。"
            audio = text_to_speech(txt)
            if audio: st.audio(audio, format='audio/mp3')

    # 經文閱讀區
    with c2:
        with st.expander("📖 展開閱讀經文 (四福音對照)"):
            gospels = [('馬太', row['經文_太']), ('馬可', row['經文_可']), ('路加', row['經文_路']), ('約翰', row['經文_約'])]
            active = [(n, r) for n, r in gospels if pd.notna(r)]
            
            if active:
                tabs = st.tabs([f"{n}" for n, r in active])
                for i, (name, ref) in enumerate(active):
                    with tabs[i]:
                        with st.spinner("載入經文中..."):
                            txt = fetch_bible_text(ref)
                        if txt:
                            st.markdown(f"<div class='verse-box'><b>{name} {ref}</b><br>{txt}</div>", unsafe_allow_html=True)
                        else:
                            st.warning("無法自動抓取，請點擊下方連結。")
                            st.markdown(f"[🔗 前往 YouVersion 閱讀 {name} {ref}](https://www.bible.com/zh-TW/bible/46/MAT.1.CUNP)")
            else:
                st.info("此事件無明確經文引用。")

# ==========================================
# 4. 主程式邏輯
# ==========================================
def main():
    df = load_data()
    if df is None: st.error("❌ 找不到 data.csv，請確認檔案已上傳至 GitHub。"); return

    # --- 側邊欄 ---
    with st.sidebar:
        st.markdown("<h1 style='color:#B8860B; text-align:center;'>✝️ Re:Jesus</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#666;'>終極完美版</p>", unsafe_allow_html=True)
        st.divider()
        
        menu = st.radio("功能導航", [
            "🏠 探索首頁", 
            "🔍 資料庫查詢", 
            "👣 主題探索路徑", 
            "💊 生命處方籤", 
            "🎨 IG 金句卡", 
            "🗺️ 聖地地圖", 
            "🏆 聖經知識王"
        ])
        
        st.markdown("---")
        st.caption("Designed for everyone.")

    # === 1. 首頁 ===
    if menu == "🏠 探索首頁":
        st.markdown("""
        <div style="text-align: center; padding: 40px 20px;">
            <h1 style="font-size: 3.5em; margin-bottom: 10px; color: #2c3e50;">遇見，真實的耶穌</h1>
            <p style="font-size: 1.2em; color: #666;">穿越時空，在每一個春夏秋冬裡與祂同行。</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✨ 隨機抽取今日靈糧", type="primary", use_container_width=True):
            st.session_state.rand_row = df.sample(1).iloc[0]
            
        if 'rand_row' not in st.session_state:
            st.session_state.rand_row = df.sample(1).iloc[0]
            
        render_card(st.session_state.rand_row)

    # === 2. 資料庫查詢 ===
    elif menu == "🔍 資料庫查詢":
        st.header("🔍 搜尋資料庫")
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("輸入關鍵字 (如：彼得, 信心, 醫治)", placeholder="在此輸入...")
        with col2:
            filter_loc = st.multiselect("地點篩選", df['地點'].unique())

        out = df.copy()
        if search:
            out = out[out.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        if filter_loc:
            out = out[out['地點'].isin(filter_loc)]
            
        st.info(f"共找到 {len(out)} 筆資料")
        for _, row in out.head(15).iterrows(): # 限制顯示數量
            render_card(row)

    # === 3. 主題路徑 ===
    elif menu == "👣 主題探索路徑":
        st.header("👣 跟隨耶穌的腳蹤")
        path = st.selectbox("選擇一條路徑", ["🌟 神蹟之路 (28站)", "🔥 受難週 (最後7天)", "⛰️ 登山寶訓"])
        
        if "神蹟" in path: mask = df['事件名稱'].str.contains("醫治|趕鬼|復活|變水|五餅")
        elif "受難" in path: mask = df['季節'].str.contains("週")
        else: mask = df['事件名稱'].str.contains("寶訓|八福")
        
        path_df = df[mask]
        st.success(f"此旅程包含 {len(path_df)} 個站點")
        
        for i, row in path_df.reset_index().iterrows():
            with st.expander(f"Step {i+1}: {row['事件名稱']} ({row['地點']})"):
                st.markdown(f"**{row['福音中心']}**")
                if st.button("查看詳情", key=f"p_{i}"):
                    st.session_state.rand_row = row
                    st.rerun() # 跳轉回首頁顯示卡片

    # === 4. 生命處方 ===
    elif menu == "💊 生命處方籤":
        st.header("💊 心靈急診室")
        feeling = st.selectbox("你現在感覺如何？", ["😟 焦慮/擔憂", "😔 孤單/被遺忘", "😡 憤怒/無法原諒", "😫 罪惡感/軟弱"])
        
        feel_map = {
            "😟 焦慮/擔憂": "平安", "😔 孤單/被遺忘": "接納",
            "😡 憤怒/無法原諒": "饒恕", "😫 罪惡感/軟弱": "悔改"
        }
        keyword = feel_map[feeling]
        
        st.markdown(f"### 給感到「{feeling.split()[1]}」的你：")
        res = df[df['福音中心'].str.contains(keyword)].head(3)
        for _, row in res.iterrows():
            render_card(row)

    # === 5. IG 金句卡 ===
    elif menu == "🎨 IG 金句卡":
        st.header("🎨 製作分享卡片")
        st.caption("截圖下方卡片，分享至 Instagram 限時動態！")
        
        if st.button("🎲 換一句話"):
            r = df.sample(1).iloc[0]
            st.session_state.ig_txt = r['福音中心']
            st.session_state.ig_ref = f"{r['事件名稱']} | {r['經文總覽']}"
            
        if 'ig_txt' not in st.session_state:
            r = df.sample(1).iloc[0]
            st.session_state.ig_txt = r['福音中心']
            st.session_state.ig_ref = f"{r['事件名稱']} | {r['經文總覽']}"
            
        st.markdown(f"""
        <div class="insta-card">
            <div class="insta-text">“{st.session_state.ig_txt}”</div>
            <div class="insta-ref">{st.session_state.ig_ref}<br>Re:Jesus</div>
        </div>
        """, unsafe_allow_html=True)

    # === 6. 地圖 ===
    elif menu == "🗺️ 聖地地圖":
        st.header("🌍 耶穌行蹤地圖")
        map_df = df.dropna(subset=['lat', 'lon'])
        st.map(map_df, size=20, color='#B8860B')

    # === 7. 知識王 ===
    elif menu == "🏆 聖經知識王":
        st.header("🏆 聖經知識挑戰")
        if 'quiz_idx' not in st.session_state:
            st.session_state.quiz_idx = random.randint(0, len(df)-1)
            st.session_state.quiz_revealed = False

        q_row = df.iloc[st.session_state.quiz_idx]
        st.markdown(f"### ❓ 題目：**「{q_row['事件名稱']}」** 發生在哪裡？")
        
        opts = list(set([q_row['地點']] + df['地點'].sample(3).tolist()))
        random.shuffle(opts)
        
        cols = st.columns(2)
        for i, opt in enumerate(opts):
            if cols[i%2].button(opt, key=opt, use_container_width=True):
                if opt == q_row['地點']:
                    st.success("🎉 答對了！")
                    st.balloons()
                else:
                    st.error(f"❌ 答錯了... 正確答案是 {q_row['地點']}")
                st.session_state.quiz_revealed = True
        
        if st.session_state.quiz_revealed:
            if st.button("🔄 下一題", type="primary"):
                st.session_state.quiz_idx = random.randint(0, len(df)-1)
                st.session_state.quiz_revealed = False
                st.rerun()

if __name__ == "__main__":
    main()
