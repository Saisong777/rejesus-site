import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
import uuid
import random
from gtts import gTTS
from io import BytesIO

# ==========================================
# 1. 系統設定與 CSS
# ==========================================
st.set_page_config(
    page_title="Re:Jesus - 擴散與共鳴版",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂 CSS，包含 IG 卡片樣式
st.markdown("""
<style>
    .big-stat {font-size: 1.5rem; font-weight: bold; color: #4a90e2;}
    .highlight-box {background-color: #f0f7ff; padding: 15px; border-radius: 8px; border: 1px solid #cce5ff;}
    .stButton button {width: 100%;}
    
    /* IG 卡片樣式 */
    .insta-card {
        width: 100%;
        max-width: 400px;
        height: 500px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px;
        border-radius: 20px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        margin: auto;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .insta-content { font-size: 24px; font-weight: bold; line-height: 1.5; margin-bottom: 20px; }
    .insta-ref { font-size: 16px; opacity: 0.8; font-style: italic;}
    .insta-footer { margin-top: auto; font-size: 14px; opacity: 0.6; letter-spacing: 1px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 資料常數
# ==========================================

# A. 地點座標
LOCATION_COORDS = {
    "耶路撒冷": [31.7683, 35.2137], "聖殿": [31.7781, 35.2360], "各各他": [31.7797, 35.2299],
    "拿撒勒": [32.7019, 35.3035], "迦百農": [32.8810, 35.5749], "伯利恆": [31.7049, 35.2038],
    "約旦河": [31.856, 35.555], "加利利": [32.8, 35.6], "加利利海": [32.82, 35.58],
    "橄欖山": [31.7791, 35.2435], "馬可樓": [31.7717, 35.2294], "耶利哥": [31.856, 35.444],
    "撒馬利亞": [32.1848, 35.2546], "迦拿": [32.7445, 35.3375], "格拉森": [32.7937, 35.6534],
    "伯大尼": [31.7716, 35.2604], "以馬忤斯": [31.8396, 35.0118]
}

# B. 主題路徑
CURATED_PATHS = {
    "🌟 神蹟之路": {"keywords": ["醫治", "趕鬼", "變水", "五餅", "復活"], "desc": "見證耶穌的大能"},
    "🔥 受難週": {"filter_season": ["週日", "週一", "週二", "週三", "週四", "週五", "週六"], "desc": "最後七天的關鍵時刻"},
    "⛰️ 登山寶訓": {"keywords": ["八福", "寶訓", "禱告"], "desc": "天國子民的生活準則"},
    "💧 約翰獨家": {"special_logic": "john_only", "desc": "約翰福音獨有的深刻對話"}
}

# C. 人物測驗題目
QUIZ_QUESTIONS = [
    {"q": "遇到巨大的風浪或困難時，你的第一反應是？", 
     "opts": {"A": "立刻行動，試圖解決", "B": "充滿懷疑，思考這是否真實", "C": "安靜等待，相信會有轉機", "D": "感到受傷，尋求情感支持"}},
    {"q": "你覺得自己最渴望得到耶穌什麼樣的幫助？", 
     "opts": {"A": "給我明確的方向和使命", "B": "解答我心中的困惑", "C": "無條件的愛與接納", "D": "醫治我過去的傷痛"}},
    {"q": "在團體中，你通常扮演什麼角色？", 
     "opts": {"A": "帶頭衝鋒的領袖", "B": "冷靜分析的觀察者", "C": "默默付出的支持者", "D": "情感豐富的連結者"}}
]

# 測驗結果對應
PERSONA_RESULTS = {
    "A": {"name": "彼得 (Peter)", "desc": "你像彼得一樣熱情、行動力強，雖然偶爾衝動，但對主有一顆火熱的心。", "event_key": "呼召"},
    "B": {"name": "多馬 (Thomas)", "desc": "你像多馬一樣追求真理，不輕易相信，但一旦看見，你的信心比誰都堅定。", "event_key": "多馬"},
    "C": {"name": "約翰 (John)", "desc": "你像約翰一樣，是「主所愛的」，比起做事，你更看重與耶穌的親密關係。", "event_key": "最後晚餐"},
    "D": {"name": "抹大拉的馬利亞 (Mary)", "desc": "你擁有一顆敏銳易感的心，深刻經歷過恩典，因此你的愛也特別深厚。", "event_key": "復活"}
}

# ==========================================
# 3. 核心函數
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        for g in ['太', '可', '路', '約']:
            df[f'有_{g}'] = df[f'經文_{g}'].notna()
        df['lat'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[0])
        df['lon'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[1])
        return df
    except FileNotFoundError: return None

def text_to_speech(text):
    """將文字轉為語音 Bytes"""
    try:
        tts = gTTS(text=text, lang='zh-TW')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# ==========================================
# 4. 主程式
# ==========================================
def main():
    df = load_data()
    if df is None: st.error("❌ 找不到資料檔"); return

    with st.sidebar:
        st.title("✝️ Re:Jesus 8.0")
        menu = st.radio("功能選單", [
            "🏠 首頁總覽", "🧩 人物共鳴測驗", "🎨 IG 金句卡", 
            "👣 主題路徑", "🔍 資料庫", "🗺️ 地圖", 
            "💊 生命處方", "📝 工具箱", "🏆 知識王"
        ])

    # === 1. 首頁 (每日靈糧 + 語音) ===
    if menu == "🏠 首頁總覽":
        st.header("Re:Jesus - 聽見與看見")
        st.markdown("不僅閱讀，更透過 **語音** 與 **視覺** 體驗耶穌的生平。")
        
        if st.button("✨ 隨機抽取今日靈糧", type="primary"):
            row = df.sample(1).iloc[0]
            st.session_state['daily_row'] = row
            
        if 'daily_row' in st.session_state:
            row = st.session_state['daily_row']
            st.markdown(f"### {row['事件名稱']}")
            st.caption(f"📍 {row['地點']} | {row['季節']}")
            
            # 語音播放器
            audio_text = f"今日靈糧。{row['事件名稱']}。福音中心：{row['福音中心']}。這件事帶給我們的神學反思是：{row['神學主題']}。"
            audio_bytes = text_to_speech(audio_text)
            if audio_bytes:
                st.audio(audio_bytes, format='audio/mp3')
            
            st.info(row['福音中心'])
            st.markdown(f"**📖 經文**：{row['經文總覽']}")

    # === 2. 人物共鳴測驗 (New!) ===
    elif menu == "🧩 人物共鳴測驗":
        st.header("🧩 測驗：你是聖經中的誰？")
        st.markdown("回答 3 個問題，找出你在福音書中的屬靈原型。")
        
        ans = {}
        for i, q_data in enumerate(QUIZ_QUESTIONS):
            st.subheader(f"Q{i+1}: {q_data['q']}")
            ans[i] = st.radio("你的選擇：", list(q_data['opts'].keys()), format_func=lambda x: q_data['opts'][x], key=f"q{i}")
            
        if st.button("查看結果"):
            # 簡單計分：出現最多次的選項
            final_code = max(set(ans.values()), key=list(ans.values()).count)
            result = PERSONA_RESULTS[final_code]
            
            st.success(f"🎉 你的屬靈原型是：{result['name']}")
            st.markdown(f"### {result['desc']}")
            
            # 推薦相關事件
            st.markdown("---")
            st.markdown("👉 **推薦你閱讀這個事件**：")
            rec_row = df[df['事件名稱'].str.contains(result['event_key'])].iloc[0]
            st.info(f"{rec_row['事件名稱']} - {rec_row['福音中心']}")

    # === 3. IG 金句卡 (New!) ===
    elif menu == "🎨 IG 金句卡":
        st.header("🎨 製作你的分享卡片")
        st.markdown("選擇一句話，產生精美卡片。**請直接截圖 (Screenshot)** 分享到 Instagram 限時動態！")
        
        # 選擇來源
        source_type = st.radio("卡片內容來源", ["🎲 隨機一句", "✍️ 自訂輸入", "🔍 從事件選擇"])
        
        card_text = "耶穌愛你"
        card_ref = "Re:Jesus"
        
        if source_type == "🎲 隨機一句":
            if st.button("換一句"):
                r = df.sample(1).iloc[0]
                st.session_state.card_text = r['福音中心']
                st.session_state.card_ref = f"{r['事件名稱']} | {r['經文總覽']}"
            if 'card_text' in st.session_state:
                card_text = st.session_state.card_text
                card_ref = st.session_state.card_ref
                
        elif source_type == "✍️ 自訂輸入":
            card_text = st.text_area("輸入金句", "在此輸入感動你的話...")
            card_ref = st.text_input("輸入出處", "例如：馬太福音 5:3")
            
        elif source_type == "🔍 從事件選擇":
            evt = st.selectbox("選擇事件", df['事件名稱'].unique())
            r = df[df['事件名稱']==evt].iloc[0]
            card_text = r['福音中心']
            card_ref = f"{evt} | {r['經文總覽']}"

        # 顯示卡片 (HTML/CSS)
        st.markdown("---")
        st.markdown(f"""
        <div class="insta-card">
            <div class="insta-content">“{card_text}”</div>
            <div class="insta-ref">{card_ref}</div>
            <div class="insta-footer">Re:Jesus</div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("👆 用手機或電腦截圖上方卡片，即可分享！")

    # === 4. 主題路徑 (保留) ===
    elif menu == "👣 主題路徑":
        st.header("👣 跟隨腳蹤")
        path = st.selectbox("選擇路徑", list(CURATED_PATHS.keys()))
        info = CURATED_PATHS[path]
        st.info(info['desc'])
        
        p_df = df.copy()
        if "keywords" in info:
            mask = p_df.apply(lambda r: any(k in str(r['事件名稱']) for k in info['keywords']), axis=1)
            p_df = p_df[mask]
        elif "filter_season" in info:
            mask = p_df['季節'].apply(lambda x: any(d in str(x) for d in info['filter_season']))
            p_df = p_df[mask]
        
        for _, r in p_df.iterrows():
            with st.expander(f"{r['事件名稱']}"):
                st.write(r['福音中心'])
                if st.button(f"🔊 朗讀", key=f"tts_{r['EventID']}"):
                    speech = text_to_speech(r['福音中心'])
                    st.audio(speech)

    # === 5. 資料庫 (保留) ===
    elif menu == "🔍 資料庫":
        st.header("🔍 搜尋資料庫")
        search = st.text_input("關鍵字")
        out = df[df.astype(str).apply(lambda x: x.str.contains(search or "", case=False)).any(axis=1)]
        st.dataframe(out[['事件名稱', '地點', '福音中心', '經文總覽']], hide_index=True)

    # === 6. 地圖 (保留) ===
    elif menu == "🗺️ 地圖":
        st.header("🌍 互動地圖")
        map_data = df.dropna(subset=['lat', 'lon'])
        st.map(map_data, size=20, color='#FF4B4B')

    # === 7. 生命處方 (保留) ===
    elif menu == "💊 生命處方":
        st.header("💊 生命處方")
        st.markdown("你現在感覺如何？")
        feelings = {"焦慮": ["平安", "風浪"], "孤單": ["接納", "尋找"], "生氣": ["饒恕", "愛"]}
        f = st.selectbox("選擇心情", list(feelings.keys()))
        keys = feelings[f]
        res = df[df.apply(lambda r: any(k in str(r['事件名稱']) for k in keys), axis=1)].head(3)
        for _, r in res.iterrows():
            st.info(f"{r['事件名稱']}: {r['福音中心']}")

    # === 8. 工具箱 (保留) ===
    elif menu == "📝 工具箱":
        st.header("📝 讀經與教材")
        st.markdown("請至 7.0 版複製完整邏輯，此處僅為示範整合。")
        if st.button("下載讀經計畫範本"):
            st.info("功能已整合，請參考完整版程式碼。")

    # === 9. 知識王 (保留) ===
    elif menu == "🏆 知識王":
        st.header("🏆 聖經知識王")
        if st.button("出題"):
            q = df.sample(1).iloc[0]
            st.write(f"題目：{q['事件名稱']} 發生在哪？")
            st.success(f"答案：{q['地點']}")

if __name__ == "__main__":
    main()
