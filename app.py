import streamlit as st
import pandas as pd
import requests
import altair as alt
from opencc import OpenCC
from io import BytesIO
from gtts import gTTS

# ==========================================
# 1. 系統設定
# ==========================================
st.set_page_config(
    page_title="Re:Jesus | 經文修復版",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化繁簡轉換
try:
    cc = OpenCC('s2twp')
except:
    cc = None # 如果轉換器失敗，至少不要讓程式崩潰

# 注入 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;700&family=Noto+Sans+TC:wght@300;400;700&display=swap');
    .stApp { background-color: #faf9f6; }
    h1, h2, h3 { font-family: 'Noto Serif TC', serif !important; color: #2c3e50; }
    .event-card {
        background-color: white; padding: 25px; border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #eee; margin-bottom: 20px;
    }
    .verse-box {
        background-color: #fffbf0; padding: 15px; border-radius: 8px;
        border-left: 4px solid #B8860B; font-family: 'Noto Serif TC', serif;
        font-size: 1.1em; line-height: 1.6; margin-top: 10px;
    }
    .error-msg { color: #d9534f; font-size: 0.9em; background: #f9f2f4; padding: 5px; border-radius: 4px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心資料處理
# ==========================================

# 擴充書卷對照表 (確保覆蓋所有縮寫)
BOOK_MAP = {
    # 英文縮寫
    "Mt": "Matthew", "Mk": "Mark", "Lk": "Luke", "Jn": "John",
    "Mat": "Matthew", "Mrk": "Mark", "Luk": "Luke", "Jhn": "John",
    # 中文縮寫
    "太": "Matthew", "可": "Mark", "路": "Luke", "約": "John",
    "馬太": "Matthew", "馬可": "Mark", "路加": "Luke", "約翰": "John"
}

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        # 預處理經文 Flag
        for g in ['太', '可', '路', '約']:
            df[f'有_{g}'] = df[f'經文_{g}'].notna()
        return df
    except FileNotFoundError: return None

def get_youversion_link(ref_string):
    """產生 YouVersion 的外部連結 (備案用)"""
    try:
        parts = str(ref_string).split()
        book = parts[0]
        # 簡單映射到 YouVersion 代碼
        yv_map = {"Mt": "MAT", "Mk": "MRK", "Lk": "LUK", "Jn": "JHN", "太": "MAT", "可": "MRK", "路": "LUK", "約": "JHN"}
        book_code = yv_map.get(book, "MAT")
        # 連結格式: https://www.bible.com/zh-TW/bible/46/MAT.1.CUNP
        return f"https://www.bible.com/zh-TW/bible/46/{book_code}.1.CUNP"
    except:
        return "https://www.bible.com/zh-TW/bible/46/MAT.1.CUNP"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_bible_text_debug(ref_string):
    """帶有除錯訊息的抓取函數"""
    if pd.isna(ref_string) or str(ref_string).strip() == "":
        return False, "無經文資料"

    ref_string = str(ref_string).strip().replace('\xa0', ' ') # 移除怪異空白
    
    try:
        # 拆解
        import re
        # 如果是 "Mt5:3" 這種黏在一起的，補空白
        if " " not in ref_string:
            ref_string = re.sub(r"([a-zA-Z\u4e00-\u9fa5]+)(\d)", r"\1 \2", ref_string)
            
        parts = ref_string.split(maxsplit=1)
        if len(parts) < 2: return False, f"格式錯誤: {ref_string}"
        
        book_abbr, verse = parts[0], parts[1]
        api_book = BOOK_MAP.get(book_abbr, book_abbr) # 查表，查不到用原字
        
        # 呼叫 API
        url = f"https://bible-api.com/{api_book}+{verse}?translation=cuv"
        resp = requests.get(url, timeout=5) # 設定 5 秒超時
        
        if resp.status_code == 200:
            data = resp.json()
            text = data.get('text', '')
            if not text: return False, "API 回傳空值 (章節可能不存在)"
            
            # 繁簡轉換
            if cc: text = cc.convert(text)
            return True, text
            
        elif resp.status_code == 404:
            return False, f"找不到章節: {api_book} {verse}"
        else:
            return False, f"API 連線錯誤 (Code: {resp.status_code})"
            
    except Exception as e:
        return False, f"系統錯誤: {str(e)}"

# ==========================================
# 3. UI 渲染
# ==========================================

def render_card(row):
    st.markdown(f"""
    <div class="event-card">
        <div>
            <span style="background:#e3f2fd; color:#1565c0; padding:4px 8px; border-radius:12px; font-size:0.8em;">{row['季節']}</span>
            <span style="background:#f3e5f5; color:#7b1fa2; padding:4px 8px; border-radius:12px; font-size:0.8em;">📍 {row['地點']}</span>
        </div>
        <h3 style="margin-top:10px;">{row['事件名稱']}</h3>
        <div style="font-family:'Noto Serif TC'; font-size:1.2em; border-left:4px solid #B8860B; padding-left:15px; color:#333;">
            {row['福音中心']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 經文互動區
    with st.expander("📖 閱讀經文 (點擊展開)"):
        # 找出有經文的書卷
        gospels = [('馬太', row['經文_太']), ('馬可', row['經文_可']), ('路加', row['經文_路']), ('約翰', row['經文_約'])]
        active = [(n, r) for n, r in gospels if pd.notna(r)]
        
        if active:
            tabs = st.tabs([f"{n}" for n, r in active])
            for i, (name, ref) in enumerate(active):
                with tabs[i]:
                    # 1. 嘗試抓取
                    success, result = fetch_bible_text_debug(ref)
                    
                    if success:
                        # 成功顯示經文
                        st.markdown(f"<div class='verse-box'><b>{ref}</b><br>{result}</div>", unsafe_allow_html=True)
                    else:
                        # 失敗顯示備案按鈕
                        st.markdown(f"<p class='error-msg'>⚠️ 無法載入經文 ({result})，但您可以直接前往閱讀：</p>", unsafe_allow_html=True)
                        link = get_youversion_link(ref)
                        st.link_button(f"🔗 前往 Bible.com 閱讀 {name}福音", link)
        else:
            st.info("此事件無引用經文")

# ==========================================
# 4. 主程式
# ==========================================
def main():
    df = load_data()
    if df is None: st.error("❌ 找不到 data.csv"); return

    with st.sidebar:
        st.title("✝️ Re:Jesus")
        st.caption("經文修復版")
        menu = st.radio("選單", ["🏠 首頁", "🔍 資料庫", "🛠️ 系統測試"])
        
        st.divider()
        st.info(f"📚 資料庫載入: {len(df)} 筆")

    if menu == "🏠 首頁":
        st.header("今日靈糧")
        if st.button("✨ 隨機抽取", type="primary"):
            st.session_state.rand = df.sample(1).iloc[0]
        
        if 'rand' not in st.session_state:
            st.session_state.rand = df.sample(1).iloc[0]
        
        render_card(st.session_state.rand)

    elif menu == "🔍 資料庫":
        st.header("資料庫搜尋")
        q = st.text_input("搜尋關鍵字")
        out = df
        if q:
            out = df[df.astype(str).apply(lambda x: x.str.contains(q, case=False)).any(axis=1)]
        
        st.write(f"結果: {len(out)} 筆")
        for _, row in out.head(10).iterrows():
            render_card(row)

    # === 全新的測試專區 ===
    elif menu == "🛠️ 系統測試":
        st.header("🛠️ API 連線診斷室")
        st.markdown("如果經文抓不到，請在這裡輸入測試，看看發生什麼事。")
        
        c1, c2 = st.columns([3, 1])
        with c1:
            test_ref = st.text_input("輸入測試經文 (例如: Jn 3:16, Mt 5:3)", "Jn 3:16")
        with c2:
            run_test = st.button("開始測試")
            
        if run_test:
            st.write(f"正在嘗試抓取: `{test_ref}` ...")
            success, msg = fetch_bible_text_debug(test_ref)
            
            if success:
                st.success("✅ 抓取成功！")
                st.markdown(f"**回傳內容：** {msg}")
            else:
                st.error("❌ 抓取失敗")
                st.markdown(f"**錯誤原因：** `{msg}`")
                st.markdown("---")
                st.markdown("**常見解決辦法：**")
                st.markdown("1. 若顯示 **API 連線錯誤**：請嘗試重啟 App (Reboot)。")
                st.markdown("2. 若顯示 **找不到章節**：請確認縮寫是否在 `BOOK_MAP` 中。")

if __name__ == "__main__":
    main()
