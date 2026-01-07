import streamlit as st
import pandas as pd
import requests
import altair as alt
import random
import uuid
from datetime import datetime, timedelta
from opencc import OpenCC
from io import BytesIO
from gtts import gTTS

# ==========================================
# 1. 系統設定 & CSS 美學工程
# ==========================================
st.set_page_config(
    page_title="Re:Jesus | 遇見真實的耶穌",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化繁簡轉換 (容錯處理)
try:
    cc = OpenCC('s2twp')
except:
    cc = None

# 注入美學 CSS (金色與深藍主題)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;700&family=Noto+Sans+TC:wght@300;400;700&display=swap');

    /* 全域設定 */
    .stApp { background-color: #faf9f6; } /* 溫暖米白底 */
    h1, h2, h3, h4 { font-family: 'Noto Serif TC', serif !important; color: #2c3e50; }
    p, div, label, span { font-family: 'Noto Sans TC', sans-serif; color: #4a4a4a; }

    /* 卡片設計 (Card UI) */
    .event-card {
        background-color: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #f0f0f0;
        margin-bottom: 25px; transition: transform 0.2s ease-in-out;
    }
    .event-card:hover {
        transform: translateY(-5px); box-shadow: 0 10px 30px rgba(184, 134, 11, 0.15); border-color: #B8860B;
    }

    /* 標籤 */
    .tag { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; margin-right: 8px; }
    .tag-season { background-color: #e3f2fd; color: #1565c0; }
    .tag-loc { background-color: #f3e5f5; color: #7b1fa2; }
    
    /* 經文引用區 */
    .gospel-quote {
        font-family: 'Noto Serif TC', serif; font-size: 1.3em; line-height: 1.6;
        color: #2c3e50; border-left: 5px solid #B8860B; padding-left: 20px; margin: 20px 0;
    }

    /* 經文閱讀盒 */
    .verse-box {
        background-color: #fffbf0; padding: 20px; border-radius: 8px;
        border: 1px dashed #d4c5a0; font-family: 'Noto Serif TC', serif; font-size: 1.1em; line-height: 1.8;
    }
    
    /* IG 卡片樣式 */
    .insta-card {
        width: 100%; max-width: 400px; aspect-ratio: 4/5;
        background: linear-gradient(135deg, #2c3e50 0%, #B8860B 100%);
        color: white; padding: 40px; border-radius: 20px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        text-align: center; margin: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .insta-text { font-family: 'Noto Serif TC', serif; font-size: 24px; font-weight: bold; line-height: 1.5; margin-bottom: 20px; color: white !important;}
    .insta-ref { font-family: 'Noto Sans TC', sans-serif; font-size: 14px; opacity: 0.8; margin-top: auto; color: white !important;}

    /* 按鈕與連結 */
    .stButton button { border-radius: 30px; font-weight: bold; }
    .error-msg { color: #d9534f; font-size: 0.9em; background: #f9f2f4; padding: 5px; border-radius: 4px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 資料常數庫
# ==========================================

# 書卷對照表 (中英縮寫 -> API 格式)
BOOK_MAP = {
      # 英文縮寫
    "Mt": "馬太福音", "Mk": "馬可福音", "Lk": "路加福音", "Jn": "約翰福音",
    "Mat": "馬太福音", "Mrk": "馬可福音", "Luk": "路加福音", "Jhn": "約翰福音",
    # 中文縮寫 (您的 CSV 裡面的格式)
    "太": "馬太福音w", "可": "馬可福音", "路": "路加福音", "約": "約翰福音",
    "馬太": "馬太福音", "馬可": "馬可福音", "路加": "路加福音", "約翰":"約翰福音",
}

# 地點座標資料 (用於地圖)
LOCATION_COORDS = {
    "耶路撒冷": [31.7683, 35.2137], "聖殿": [31.7781, 35.2360], "各各他": [31.7797, 35.2299],
    "拿撒勒": [32.7019, 35.3035], "迦百農": [32.8810, 35.5749], "伯利恆": [31.7049, 35.2038],
    "約旦河": [31.856, 35.555], "加利利": [32.8, 35.6], "加利利海": [32.82, 35.58],
    "八福山": [32.8805, 35.5558], "橄欖山": [31.7791, 35.2435], "馬可樓": [31.7717, 35.2294],
    "客西馬尼": [31.7794, 35.2401], "耶利哥": [31.856, 35.444], "撒馬利亞": [32.1848, 35.2546],
    "迦拿": [32.7445, 35.3375], "格拉森": [32.7937, 35.6534], "伯大尼": [31.7716, 35.2604],
    "以馬忤斯": [31.8396, 35.0118]
}

# 主題探索路徑定義
CURATED_PATHS = {
    "🌟 神蹟之路": {"keywords": ["醫治", "趕鬼", "變水", "五餅", "復活"], "desc": "見證耶穌的大能"},
    "🔥 受難週": {"filter_season": ["週日", "週一", "週二", "週三", "週四", "週五", "週六"], "desc": "最後七天的關鍵時刻"},
    "⛰️ 登山寶訓": {"keywords": ["八福", "寶訓", "禱告"], "desc": "天國子民的生活準則"}
}

# 生命處方籤定義
LIFE_SCENARIOS = {
    "😟 焦慮/擔憂": "平安", "😔 孤單/被遺忘": "接納",
    "😡 憤怒/無法原諒": "饒恕", "😫 罪惡感/軟弱": "悔改"
}

# ==========================================
# 3. 核心功能函數 (Helpers)
# ==========================================

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        # 預處理經文 Flag
        for g in ['太', '可', '路', '約']:
            df[f'有_{g}'] = df[f'經文_{g}'].notna()
        # 處理座標
        df['lat'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[0])
        df['lon'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[1])
        return df
    except FileNotFoundError: return None

def get_youversion_link(ref_string):
    """產生 Bible.com 備用連結"""
    try:
        parts = str(ref_string).split()
        book = parts[0]
        yv_map = {"Mt": "MAT", "Mk": "MRK", "Lk": "LUK", "Jn": "JHN", "太": "MAT", "可": "MRK", "路": "LUK", "約": "JHN"}
        code = yv_map.get(book, "MAT")
        return f"https://www.bible.com/zh-TW/bible/46/{code}.1.CUNP"
    except:
        return "https://www.bible.com/zh-TW/bible/46/MAT.1.CUNP"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_bible_text(ref_string):
    """強健的經文抓取函數 (含容錯機制)"""
    if pd.isna(ref_string) or str(ref_string).strip() == "":
        return False, "無經文資料"

    ref_string = str(ref_string).strip().replace('\xa0', ' ')
    
    try:
        import re
        if " " not in ref_string:
            ref_string = re.sub(r"([a-zA-Z\u4e00-\u9fa5]+)(\d)", r"\1 \2", ref_string)
            
        parts = ref_string.split(maxsplit=1)
        if len(parts) < 2: return False, f"格式無法解析: {ref_string}"
        
        book, verse = parts[0], parts[1]
        api_book = BOOK_MAP.get(book, book) # 查表
        
        url = f"https://bible-api.com/{api_book}+{verse}?translation=cuv"
        resp = requests.get(url, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            text = data.get('text', '')
            if not text: return False, "API 回傳空值"
            if cc: text = cc.convert(text) # 繁簡轉換
            return True, text
        elif resp.status_code == 404:
            return False, "找不到該章節 (404)"
        else:
            return False, f"API 連線錯誤 ({resp.status_code})"
    except Exception as e:
        return False, f"系統錯誤: {str(e)}"

def text_to_speech(text):
    """文字轉語音"""
    try:
        tts = gTTS(text=text, lang='zh-TW')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

def create_ics(plan_data, start_date):
    """生成行事曆檔案"""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Re:Jesus//Plan//EN"]
    curr = start_date
    for day, events in plan_data.items():
        dt_start = curr.strftime("%Y%m%d")
        dt_end = (curr + timedelta(days=1)).strftime("%Y%m%d")
        desc = "\\n".join([f"{e['name']} ({e['ref']})" for e in events])
        lines.extend([
            "BEGIN:VEVENT", f"UID:{uuid.uuid4()}",
            f"DTSTART;VALUE=DATE:{dt_start}", f"DTEND;VALUE=DATE:{dt_end}",
            f"SUMMARY:Re:Jesus 讀經計畫 Day {day}", f"DESCRIPTION:{desc}", "END:VEVENT"
        ])
        curr += timedelta(days=1)
    lines.append("END:VCALENDAR")
    return "\n".join(lines)

def generate_markdown(row):
    """生成教材"""
    return f"# {row['事件名稱']}\n**地點**：{row['地點']}\n\n## 1. 觀察\n經文：{row['經文總覽']}\n\n## 2. 解釋\n核心：{row['福音中心']}\n\n## 3. 應用\n這件事如何挑戰你的生活？"

# ==========================================
# 4. UI 渲染元件
# ==========================================

def render_card(row):
    """渲染美化卡片"""
    st.markdown(f"""
    <div class="event-card">
        <div>
            <span class="tag tag-season">{row['季節']}</span>
            <span class="tag tag-loc">📍 {row['地點']}</span>
        </div>
        <h2 style="margin-top:10px;">{row['事件名稱']}</h2>
        <div class="gospel-quote">
            {row['福音中心']}
        </div>
        <div style="font-size:0.9em; color:#888; text-align:right;">
            💡 神學主題：{row['神學主題']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 5])
    
    # 語音按鈕
    with c1:
        if st.button("🔊 聽聽看", key=f"tts_{row['EventID']}"):
            audio = text_to_speech(f"{row['事件名稱']}。{row['福音中心']}")
            if audio: st.audio(audio, format='audio/mp3')

    # 經文閱讀 (含備案)
    with c2:
        with st.expander("📖 展開閱讀經文"):
            gospels = [('馬太', row['經文_太']), ('馬可', row['經文_可']), ('路加', row['經文_路']), ('約翰', row['經文_約'])]
            active = [(n, r) for n, r in gospels if pd.notna(r)]
            
            if active:
                tabs = st.tabs([f"{n}" for n, r in active])
                for i, (name, ref) in enumerate(active):
                    with tabs[i]:
                        success, result = fetch_bible_text(ref)
                        if success:
                            st.markdown(f"<div class='verse-box'><b>{ref}</b><br>{result}</div>", unsafe_allow_html=True)
                        else:
                            # 備案按鈕
                            st.markdown(f"<p class='error-msg'>⚠️ {result}，請點擊下方連結閱讀：</p>", unsafe_allow_html=True)
                            st.link_button(f"🔗 前往 Bible.com 閱讀 {name}福音", get_youversion_link(ref))
            else:
                st.info("此事件無直接引用經文")

# ==========================================
# 5. 主程式邏輯
# ==========================================
def main():
    df = load_data()
    if df is None: st.error("❌ 找不到 data.csv"); return

    # --- 側邊欄 ---
    with st.sidebar:
        st.markdown("<h1 style='color:#B8860B; text-align:center;'>✝️ Re:Jesus</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;'>終極完整版</p>", unsafe_allow_html=True)
        st.divider()
        
        menu = st.radio("功能導航", [
            "🏠 探索首頁", 
            "🔍 資料庫查詢", 
            "👣 主題探索路徑", 
            "💊 生命處方籤", 
            "🎨 IG 金句卡", 
            "📝 實用工具箱",
            "🗺️ 聖地地圖", 
            "🏆 聖經知識王",
            "🛠️ 系統診斷室"
        ])

    # === 1. 首頁 ===
    if menu == "🏠 探索首頁":
        st.markdown("""
        <div style="text-align: center; padding: 40px 20px;">
            <h1 style="font-size: 3em; margin-bottom: 10px;">遇見，真實的耶穌</h1>
            <p style="font-size: 1.2em; color: #666;">穿越時空，在每一個春夏秋冬裡與祂同行。</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✨ 隨機抽取今日靈糧", type="primary", use_container_width=True):
            st.session_state.rand = df.sample(1).iloc[0]
        if 'rand' not in st.session_state:
            st.session_state.rand = df.sample(1).iloc[0]
        render_card(st.session_state.rand)

    # === 2. 資料庫查詢 ===
    elif menu == "🔍 資料庫查詢":
        st.header("🔍 資料庫搜尋")
        c1, c2 = st.columns([3, 1])
        q = c1.text_input("輸入關鍵字 (如：彼得, 信心)")
        loc = c2.multiselect("地點", df['地點'].unique())
        
        out = df.copy()
        if q: out = out[out.astype(str).apply(lambda x: x.str.contains(q, case=False)).any(axis=1)]
        if loc: out = out[out['地點'].isin(loc)]
        
        st.info(f"共找到 {len(out)} 筆資料")
        for _, row in out.head(10).iterrows():
            render_card(row)

    # === 3. 主題路徑 ===
    elif menu == "👣 主題探索路徑":
        st.header("👣 主題路徑")
        path = st.selectbox("選擇旅程", list(CURATED_PATHS.keys()))
        info = CURATED_PATHS[path]
        st.info(info['desc'])
        
        if "keywords" in info:
            mask = df.apply(lambda r: any(k in str(r['事件名稱']) for k in info['keywords']), axis=1)
        else:
            mask = df['季節'].apply(lambda x: any(d in str(x) for d in info['filter_season']))
            
        for i, row in df[mask].reset_index().iterrows():
            with st.expander(f"Step {i+1}: {row['事件名稱']}"):
                st.markdown(f"**{row['福音中心']}**")
                if st.button("查看詳情", key=f"path_{i}"):
                    st.session_state.rand = row
                    st.rerun()

    # === 4. 生命處方 ===
    elif menu == "💊 生命處方籤":
        st.header("💊 心靈急診室")
        feel = st.selectbox("現在的心情？", list(LIFE_SCENARIOS.keys()))
        res = df[df['福音中心'].str.contains(LIFE_SCENARIOS[feel])].head(3)
        st.markdown(f"### 給你的處方：")
        for _, row in res.iterrows(): render_card(row)

    # === 5. IG 卡片 ===
    elif menu == "🎨 IG 金句卡":
        st.header("🎨 製作分享卡片")
        if st.button("🎲 換一句"):
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
        st.caption("📱 請直接截圖分享")

    # === 6. 工具箱 ===
    elif menu == "📝 實用工具箱":
        st.header("🛠️ 實用工具")
        t1, t2 = st.tabs(["📅 讀經計畫", "📄 小組教材"])
        with t1:
            days = st.number_input("幾天讀完？", 7, 365, 30)
            if st.button("生成行事曆 (.ics)"):
                per_day = len(df) / days
                plan = {d: [{"name": r['事件名稱'], "ref": r['經文總覽']} for _, r in df.iloc[int((d-1)*per_day):int(d*per_day)].iterrows()] for d in range(1, days+1)}
                st.download_button("下載行事曆", create_ics(plan, datetime.today()), "plan.ics")
        with t2:
            evt = st.selectbox("選擇事件", df['事件名稱'].unique())
            if st.button("生成教材"):
                md = generate_markdown(df[df['事件名稱']==evt].iloc[0])
                st.download_button("下載 Markdown", md, f"{evt}.md")

    # === 7. 地圖 ===
    elif menu == "🗺️ 聖地地圖":
        st.header("🌍 耶穌行蹤")
        st.map(df.dropna(subset=['lat', 'lon']), size=20, color='#B8860B')

    # === 8. 知識王 ===
    elif menu == "🏆 聖經知識王":
        st.header("🏆 知識挑戰")
        if 'quiz_idx' not in st.session_state:
            st.session_state.quiz_idx = random.randint(0, len(df)-1)
            st.session_state.quiz_revealed = False

        q = df.iloc[st.session_state.quiz_idx]
        st.markdown(f"### 題目：**「{q['事件名稱']}」** 發生在哪裡？")
        
        opts = list(set([q['地點']] + df['地點'].sample(3).tolist()))
        random.shuffle(opts)
        
        cols = st.columns(2)
        for i, opt in enumerate(opts):
            if cols[i%2].button(opt, key=opt, use_container_width=True):
                if opt == q['地點']:
                    st.success("🎉 答對了！")
                    st.balloons()
                else:
                    st.error(f"❌ 錯了... 是 {q['地點']}")
                st.session_state.quiz_revealed = True
        
        if st.session_state.quiz_revealed and st.button("下一題", type="primary"):
            st.session_state.quiz_idx = random.randint(0, len(df)-1)
            st.session_state.quiz_revealed = False
            st.rerun()

    # === 9. 系統診斷室 ===
    elif menu == "🛠️ 系統診斷室":
        st.header("🛠️ API 連線診斷")
        test_ref = st.text_input("輸入測試經文", "Jn 3:16")
        if st.button("開始測試"):
            success, msg = fetch_bible_text(test_ref)
            if success: st.success(f"✅ 成功：{msg}")
            else: st.error(f"❌ 失敗：{msg}")

if __name__ == "__main__":
    main()
