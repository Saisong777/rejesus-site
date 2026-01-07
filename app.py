import streamlit as st
import pandas as pd
import requests
import altair as alt
from opencc import OpenCC
import time
from io import BytesIO

# ==========================================
# 1. 系統設定
# ==========================================
st.set_page_config(
    page_title="Re:Jesus X - 極致聖經版",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 專業繁簡轉換器 (S2TWP: Simplified to Traditional Taiwan with Phrases)
cc = OpenCC('s2twp')

st.markdown("""
<style>
    .highlight-box {background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #4a90e2; box-shadow: 0 2px 5px rgba(0,0,0,0.05);}
    .verse-content {font-size: 1.15em; line-height: 1.7; color: #212529; background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6;}
    .verse-ref {font-weight: bold; color: #6c757d; margin-bottom: 5px; display: block;}
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 4px; padding: 5px 15px; background-color: #f1f3f5; }
    .stTabs [aria-selected="true"] { background-color: #4a90e2; color: white; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 資料處理核心
# ==========================================

# 書卷映射表 (CSV縮寫 -> API全名)
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
    "格拉森": [32.7937, 35.6534], "伯大尼": [31.7716, 35.2604]
}

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        # 預處理：確認有哪些書卷
        for g in ['太', '可', '路', '約']:
            df[f'有_{g}'] = df[f'經文_{g}'].notna()
        
        # 座標處理
        df['lat'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[0])
        df['lon'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[1])
        return df
    except FileNotFoundError: return None

# --- 經文抓取核心 (最複雜的部分) ---
@st.cache_data(ttl=86400, show_spinner=False) # 快取 24 小時
def fetch_single_verse_text(ref_string):
    """抓取單一段經文並轉換繁體"""
    if pd.isna(ref_string): return None
    
    # 清洗經文格式 (移除多餘空格)
    ref_string = str(ref_string).strip()
    
    try:
        # 1. 拆解書卷與章節 (例如 "Mt 5:3-10")
        parts = ref_string.split(maxsplit=1)
        book_abbr = parts[0]
        chapter_verse = parts[1] if len(parts) > 1 else ""
        
        # 2. 轉換書卷名為英文 (API需求)
        api_book = BOOK_MAP.get(book_abbr, book_abbr)
        
        # 3. 呼叫 API
        url = f"https://bible-api.com/{api_book}+{chapter_verse}?translation=cuv"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            raw_text = data['text']
            # 4. 關鍵步驟：使用 OpenCC 進行完美的繁簡轉換
            return cc.convert(raw_text)
        else:
            return None
    except Exception as e:
        return None

# ==========================================
# 3. UI 顯示元件
# ==========================================

def render_full_event(row):
    """顯示完整的事件卡片，包含四福音分頁"""
    
    # 1. 基本資訊卡
    st.markdown(f"""
    <div class="highlight-box">
        <h3>{row['EventID']} | {row['事件名稱']}</h3>
        <p><b>📍 {row['地點']} | 🗓️ {row['季節']}</b></p>
        <p style="font-size:1.2em; color:#2c3e50;">{row['福音中心']}</p>
        <hr style="margin: 10px 0;">
        <p style="font-size:0.9em; color:#666;">神學主題：{row['神學主題']} | 焦點：{row['焦點']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. 經文展開區 (平行對照)
    with st.expander(f"📖 展開閱讀經文 (共 {row['經文總覽']})", expanded=False):
        
        # 檢查哪卷書有經文
        gospels = [
            ("馬太", row['經文_太']), 
            ("馬可", row['經文_可']), 
            ("路加", row['經文_路']), 
            ("約翰", row['經文_約'])
        ]
        
        # 過濾出有內容的書卷
        active_gospels = [(name, ref) for name, ref in gospels if pd.notna(ref)]
        
        if not active_gospels:
            st.warning("此事件無明確經文引用")
        else:
            # 建立分頁
            tabs = st.tabs([f"{name} ({ref})" for name, ref in active_gospels])
            
            # 在每個分頁中抓取經文
            for i, (name, ref) in enumerate(active_gospels):
                with tabs[i]:
                    with st.spinner(f"正在抓取 {name}福音 {ref}..."):
                        text = fetch_single_verse_text(ref)
                        
                    if text:
                        st.markdown(f"<span class='verse-ref'>{name}福音 {ref}</span>", unsafe_allow_html=True)
                        st.markdown(f"<div class='verse-content'>{text}</div>", unsafe_allow_html=True)
                        
                        # YouVersion 外部連結 (備案)
                        book_code = BOOK_MAP.get(ref.split()[0], "MAT")[:3].upper()
                        url = f"https://www.bible.com/zh-TW/bible/46/{book_code}.1.CUNP"
                        st.caption(f"[🔗 前往 YouVersion 閱讀全章]({url})")
                    else:
                        st.error(f"無法自動抓取 {ref}，可能是格式過於複雜。")
                        st.link_button("直接前往線上聖經閱讀", "https://www.bible.com/zh-TW/bible/46/MAT.1.CUNP")

    st.divider()

# ==========================================
# 4. 主程式邏輯
# ==========================================
def main():
    df = load_data()
    if df is None: st.error("請確認 data.csv 是否存在"); return

    with st.sidebar:
        st.title("✝️ Re:Jesus X")
        st.caption("極致聖經整合版")
        
        menu = st.radio("功能導航", [
            "🏠 平行經文閱讀", 
            "👣 主題探索", 
            "🔍 全庫搜尋",
            "📥 下載完整資料庫 (含經文)"
        ])
        
        st.divider()
        st.info("💡 提示：點擊事件下方的展開按鈕，即可自動下載並轉換四福音經文。")

    # === 功能 1: 平行經文閱讀 (主介面) ===
    if menu == "🏠 平行經文閱讀":
        st.header("🏠 四福音平行對照")
        st.markdown("這裡展示耶穌生平的完整紀錄。若該事件在多卷福音書都有記載，您可以點擊分頁進行對照。")
        
        # 分頁控制 (避免一次載入太多)
        page_size = 10
        total_pages = len(df) // page_size + 1
        page = st.number_input("選擇頁數", 1, total_pages, 1)
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        current_view = df.iloc[start_idx:end_idx]
        
        for _, row in current_view.iterrows():
            render_full_event(row)

    # === 功能 2: 主題探索 ===
    elif menu == "👣 主題探索":
        st.header("👣 主題路徑")
        path = st.selectbox("選擇路徑", ["🌟 神蹟之路 (28個事件)", "🔥 受難週 (最後7天)", "⛰️ 登山寶訓"])
        
        if path.startswith("🌟"):
            mask = df['事件名稱'].str.contains("醫治|趕鬼|復活|變水|五餅")
        elif path.startswith("🔥"):
            mask = df['季節'].str.contains("週")
        else:
            mask = df['事件名稱'].str.contains("寶訓|八福")
            
        subset = df[mask]
        st.success(f"此路徑包含 {len(subset)} 個事件")
        for _, row in subset.iterrows():
            render_full_event(row)

    # === 功能 3: 全庫搜尋 ===
    elif menu == "🔍 全庫搜尋":
        st.header("🔍 關鍵字搜尋")
        q = st.text_input("輸入關鍵字 (例如: 彼得, 信心, 聖殿)")
        if q:
            res = df[df.astype(str).apply(lambda x: x.str.contains(q, case=False)).any(axis=1)]
            st.info(f"找到 {len(res)} 筆結果")
            for _, row in res.head(20).iterrows(): # 限制顯示數量以保效能
                render_full_event(row)

    # === 功能 4: 批次下載 (Heavy Task) ===
    elif menu == "📥 下載完整資料庫 (含經文)":
        st.header("📥 批次抓取並下載")
        st.warning("⚠️ 注意：這會觸發大量網路請求，可能需要幾分鐘的時間。請勿頻繁點擊。")
        
        if st.button("🚀 開始抓取所有經文"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 複製一份資料
            download_df = df.copy()
            download_df['完整經文內容'] = ""
            
            # 限制抓取數量 (以免 Streamlit Cloud 超時，這裡設為前 50 筆示範，您可自行改為 len(df))
            # 若要抓全部，請改為 total_items = len(download_df)
            total_items = 50 
            status_text.text(f"準備抓取前 {total_items} 筆資料的經文...")
            
            for index, row in download_df.head(total_items).iterrows():
                # 組合所有經文
                full_text = ""
                refs = [row['經文_太'], row['經文_可'], row['經文_路'], row['經文_約']]
                books = ['太', '可', '路', '約']
                
                for book, ref in zip(books, refs):
                    if pd.notna(ref):
                        txt = fetch_single_verse_text(ref)
                        if txt:
                            full_text += f"【{book} {ref}】\n{txt}\n\n"
                            
                download_df.at[index, '完整經文內容'] = full_text
                
                # 更新進度
                progress = (index + 1) / total_items
                progress_bar.progress(progress)
                status_text.text(f"正在處理: {row['事件名稱']}...")
                time.sleep(0.1) # 禮貌性延遲
            
            st.success("抓取完成！(為避免超時，此模式預設僅抓取前50筆，您可修改程式碼解鎖全部)")
            
            # 轉換為 CSV 下載
            csv = download_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 下載 Excel/CSV 檔案",
                csv,
                "ReJesus_Full_Bible_Text.csv",
                "text/csv"
            )

if __name__ == "__main__":
    main()
