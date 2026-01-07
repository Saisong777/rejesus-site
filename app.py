import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import uuid

# --- 1. 網頁設定 ---
st.set_page_config(
    page_title="Re:Jesus - 每日同行版",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS 與 UI 優化 ---
st.markdown("""
<style>
    .stButton button {width: 100%;}
    .big-stat {font-size: 2rem; font-weight: bold; color: #4a90e2;}
    .card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        border-left: 4px solid #FF4B4B;
    }
    .correct-answer {background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px;}
    .wrong-answer {background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# --- 3. 核心函數 ---

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        df['DateOrder'] = range(len(df)) # 建立順序索引
        return df
    except FileNotFoundError:
        return None

def create_ics_file(plan_data, start_date):
    """生成行事曆檔案內容 (.ics format)"""
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Re:Jesus//Reading Plan//EN",
        "CALSCALE:GREGORIAN"
    ]
    
    current_date = start_date
    date_format = "%Y%m%d"
    
    for day, events in plan_data.items():
        # 每日標題
        day_summary = f"Re:Jesus 讀經計畫 (Day {day})"
        description = "\\n".join([f"{e['id']} {e['name']} ({e['ref']})" for e in events])
        
        # 建立當日全天事件
        dt_start = current_date.strftime(date_format)
        dt_end = (current_date + timedelta(days=1)).strftime(date_format)
        
        event_block = [
            "BEGIN:VEVENT",
            f"UID:{uuid.uuid4()}",
            f"DTSTART;VALUE=DATE:{dt_start}",
            f"DTEND;VALUE=DATE:{dt_end}",
            f"SUMMARY:{day_summary}",
            f"DESCRIPTION:{description}",
            "END:VEVENT"
        ]
        ics_content.extend(event_block)
        current_date += timedelta(days=1)
        
    ics_content.append("END:VCALENDAR")
    return "\n".join(ics_content)

# --- 4. 主程式 ---
def main():
    df = load_data()
    if df is None:
        st.error("❌ 請確認 data.csv 是否存在")
        return

    # --- 側邊欄 ---
    with st.sidebar:
        st.title("✝️ Re:Jesus 6.0")
        st.caption("終極每日同行版")
        menu = st.radio("功能選擇", ["📅 讀經計畫生成", "🏆 聖經知識王", "📊 神學熱力圖", "💬 AI 導覽員"])
        st.divider()
        st.info(f"資料庫版本: v{len(df)}")

    # === 功能 1: 讀經計畫生成 (Calendar) ===
    if menu == "📅 讀經計畫生成":
        st.header("📅 打造你的專屬讀經計畫")
        st.markdown("輸入你想花幾天讀完耶穌生平，系統會為你安排進度，並產生行事曆檔案。")
        
        c1, c2 = st.columns(2)
        with c1:
            days = st.number_input("你想花幾天讀完？", min_value=7, max_value=365, value=40)
        with c2:
            start_date = st.date_input("從哪一天開始？", datetime.today())

        if st.button("🚀 生成計畫", type="primary"):
            # 計算邏輯
            total_events = len(df)
            events_per_day = total_events / days
            
            plan_preview = {}
            events_buffer = []
            
            # 分配事件
            current_day = 1
            idx = 0
            while idx < total_events:
                end_idx = int(current_day * events_per_day)
                if current_day == days: end_idx = total_events # 最後一天包含剩下所有
                
                day_events = df.iloc[idx:end_idx]
                
                # 儲存資料供預覽與下載
                event_list = []
