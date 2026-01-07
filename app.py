import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
import uuid
import random

# ==========================================
# 1. 系統設定與 CSS
# ==========================================
st.set_page_config(
    page_title="Re:Jesus - 終極全功能版",
    page_icon="✝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .big-stat {font-size: 1.5rem; font-weight: bold; color: #4a90e2;}
    .card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        border-left: 4px solid #FF4B4B;
    }
    .highlight-box {background-color: #f0f7ff; padding: 15px; border-radius: 8px; border: 1px solid #cce5ff;}
    .stButton button {width: 100%;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 資料常數與字典 (手動建立的資料庫)
# ==========================================

# A. 地點座標資料 (用於地圖)
LOCATION_COORDS = {
    "耶路撒冷": [31.7683, 35.2137], "聖殿": [31.7781, 35.2360], "各各他": [31.7797, 35.2299],
    "拿撒勒": [32.7019, 35.3035], "迦百農": [32.8810, 35.5749], "伯利恆": [31.7049, 35.2038],
    "約旦河": [31.856, 35.555], "加利利": [32.8, 35.6], "加利利海": [32.82, 35.58],
    "八福山": [32.8805, 35.5558], "橄欖山": [31.7791, 35.2435], "馬可樓": [31.7717, 35.2294],
    "客西馬尼": [31.7794, 35.2401], "耶利哥": [31.856, 35.444], "撒馬利亞": [32.1848, 35.2546],
    "迦拿": [32.7445, 35.3375], "拿因城": [32.6300, 35.3400], "格拉森": [32.7937, 35.6534],
    "該撒利亞腓立比": [33.2486, 35.6917], "伯大尼": [31.7716, 35.2604], "以馬忤斯": [31.8396, 35.0118],
    "推羅": [33.2709, 35.1963], "西頓": [33.5599, 35.3756], "低加波利": [32.7, 35.8],
    "比利亞": [32.0, 35.6], "猶大": [31.6, 35.1], "曠野": [31.7, 35.4]
}

# B. 主題探索路徑
CURATED_PATHS = {
    "🌟 神蹟之路": {"keywords": ["醫治", "趕鬼", "變水為酒", "五餅二魚", "復活"], "desc": "見證耶穌的大能與憐憫"},
    "🔥 受難週": {"filter_season": ["週日", "週一", "週二", "週三", "週四", "週五", "週六"], "desc": "最後七天的關鍵時刻"},
    "⛰️ 登山寶訓": {"keywords": ["八福", "登山寶訓", "禱告", "論"], "desc": "天國子民的生活準則"},
    "💧 約翰獨家": {"special_logic": "john_only", "desc": "約翰福音獨有的深刻對話"}
}

# C. 生命處方籤情境
LIFE_SCENARIOS = {
    "😟 焦慮/擔憂": {"keywords": ["平安", "不要怕", "信心", "風浪"], "msg": "祂是平靜風浪的主，把主權交給祂。", "theme": "保護、信實"},
    "😔 孤單/被遺忘": {"keywords": ["接納", "尋找", "痲瘋", "婦人"], "msg": "耶穌看見你了，在祂眼中你是無價之寶。", "theme": "恩典、接納"},
    "😡 憤怒/無法原諒": {"keywords": ["饒恕", "愛仇敵", "憐憫"], "msg": "饒恕是釋放自己，讓神的愛流進來。", "theme": "憐憫、同理"},
    "😫 罪惡感/軟弱": {"keywords": ["呼召", "罪人", "悔改", "稅吏"], "msg": "健康的人不需要醫生，祂正是為你而來。", "theme": "恩典、悔改"}
}

# ==========================================
# 3. 核心函數庫
# ==========================================

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data.csv")
        # 1. 建立福音書 Flag
        for g in ['太', '可', '路', '約']:
            df[f'有_{g}'] = df[f'經文_{g}'].notna()
        # 2. 建立座標
        df['lat'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[0] if pd.notna(x) else None)
        df['lon'] = df['地點'].map(lambda x: LOCATION_COORDS.get(x, [None, None])[1] if pd.notna(x) else None)
        # 3. 建立順序索引
        df['Order'] = range(len(df))
        return df
    except FileNotFoundError:
        return None

def create_ics(plan_data, start_date):
    """生成 ICS 行事曆檔案"""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Re:Jesus//Plan//EN"]
    curr = start_date
    for day, events in plan_data.items():
        dt_start = curr.strftime("%Y%m%d")
        dt_end = (curr + timedelta(days=1)).strftime("%Y%m%d")
        desc = "\\n".join([f"{e['name']} ({e['ref']})" for e in events])
        lines.extend([
            "BEGIN:VEVENT", f"UID:{uuid.uuid4()}",
            f"DTSTART;VALUE=DATE:{dt_start}", f"DTEND;VALUE=DATE:{dt_end}",
            f"SUMMARY:Re:Jesus Day {day}", f"DESCRIPTION:{desc}", "END:VEVENT"
        ])
        curr += timedelta(days=1)
    lines.append("END:VCALENDAR")
    return "\n".join(lines)

def generate_markdown(row):
    """生成小組教材"""
    return f"""
# 📖 查經：{row['事件名稱']}
### 1. 🧊 破冰
本週有沒有發生什麼事讓你想到「{row['神學主題']}」？
### 2. 🧐 觀察
* **經文**：{row['經文總覽']} ({row['地點']}/{row['季節']})
* **事件**：{row['福音中心_原文']}
### 3. 💡 解釋
* **耶穌品格**：{row['耶穌品格']}
* **核心意義**：{row['福音中心']}
### 4. 🏃 應用
* 這件事如何挑戰或安慰你？
* 你本週可以如何回應？
"""

# ==========================================
# 4. 主程式邏輯
# ==========================================
def main():
    df = load_data()
    if df is None:
        st.error("❌ 找不到 data.csv，請確認檔案已上傳至 GitHub。")
        return

    # --- 側邊欄導航 ---
    with st.sidebar:
        st.title("✝️ Re:Jesus 7.0")
        st.caption("全功能終極整合版")
        
        menu_options = [
            "🏠 首頁總覽",
            "🔍 資料庫查詢",
            "🗺️ 互動地圖",
            "👣 主題探索路徑",
            "💊 生命處方籤",
            "📊 數據分析 & 歷史軌跡",
            "📝 工具箱 (讀經/教材)",
            "🏆 聖經知識王",
            "🔢 福音對照透視"
        ]
        selection = st.radio("功能選單", menu_options)
        st.divider()
        st.info(f"📚 收錄 {len(df)} 筆事件")

    # ==========================================
    # 頁面 1: 首頁總覽
    # ==========================================
    if selection == "🏠 首頁總覽":
        st.header("歡迎來到 Re:Jesus")
        st.markdown("一個讓所有人**輕鬆、無痛、深度**認識耶穌的互動平台。")
        
        # 關鍵指標
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("記載事件", len(df))
        c2.metric("涵蓋地點", df['地點'].nunique())
        c3.metric("神學主題", df['神學主題'].nunique())
        c4.metric("引用經文", "四福音書")
        
        st.divider()
        
        # 每日一瞥
        if st.button("✨ 隨機抽取今日靈糧", type="primary"):
            row = df.sample(1).iloc[0]
            st.markdown(f"""
            <div class="highlight-box">
                <h3>{row['事件名稱']}</h3>
                <p><b>📍 {row['地點']} | 🗓️ {row['季節']}</b></p>
                <p style="font-size:1.1em;">{row['福音中心']}</p>
                <hr>
                <p><i>{row['經文總覽']}</i></p>
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # 頁面 2: 資料庫查詢
    # ==========================================
    elif selection == "🔍 資料庫查詢":
        st.header("📂 完整資料庫")
        
        c1, c2, c3 = st.columns(3)
        search = c1.text_input("🔍 關鍵字搜尋")
        loc_filter = c2.multiselect("📍 地點", df['地點'].unique())
        theme_filter = c3.multiselect("💡 主題", df['神學主題'].unique())
        
        out = df.copy()
        if search:
            out = out[out.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        if loc_filter:
            out = out[out['地點'].isin(loc_filter)]
        if theme_filter:
            out = out[out['神學主題'].isin(theme_filter)]
            
        st.write(f"共找到 {len(out)} 筆資料")
        st.dataframe(
            out[['EventID', '季節', '地點', '事件名稱', '神學主題', '福音中心', '經文總覽']],
            hide_index=True, use_container_width=True
        )

    # ==========================================
    # 頁面 3: 互動地圖
    # ==========================================
    elif selection == "🗺️ 互動地圖":
        st.header("🌍 耶穌的行蹤地圖")
        
        map_data = df.dropna(subset=['lat', 'lon'])
        
        # 調整地圖點大小
        map_counts = map_data.groupby(['lat', 'lon', '地點']).size().reset_index(name='count')
        map_counts['size'] = map_counts['count'] * 50
        
        st.map(map_counts, latitude='lat', longitude='lon', size='size', color='#FF4B4B', zoom=7)
        
        st.caption("註：地圖顯示耶穌事工的主要發生地。圓點越大代表發生在該處的事件越多。")

    # ==========================================
    # 頁面 4: 主題探索路徑
    # ==========================================
    elif selection == "👣 主題探索路徑":
        st.header("👣 跟隨耶穌的腳蹤")
        path_name = st.selectbox("選擇一條路徑開始：", list(CURATED_PATHS.keys()))
        info = CURATED_PATHS[path_name]
        
        st.info(info['desc'])
        
        # 篩選邏輯
        p_df = df.copy()
        if "keywords" in info:
            mask = p_df.apply(lambda r: any(k in str(r['事件名稱']) for k in info['keywords']), axis=1)
            p_df = p_df[mask]
        elif "filter_season" in info:
            mask = p_df['季節'].apply(lambda x: any(d in str(x) for d in info['filter_season']))
            p_df = p_df[mask]
        elif "special_logic" in info:
            p_df = p_df[p_df['有_約'] & ~p_df['有_太'] & ~p_df['有_可'] & ~p_df['有_路']]
            
        st.success(f"此路徑包含 {len(p_df)} 個站點")
        for i, row in p_df.reset_index().iterrows():
            with st.expander(f"Step {i+1}: {row['事件名稱']} ({row['地點']})"):
                st.write(row['福音中心'])
                st.caption(f"經文：{row['經文總覽']}")

    # ==========================================
    # 頁面 5: 生命處方籤
    # ==========================================
    elif selection == "💊 生命處方籤":
        st.header("💊 心靈急診室")
        feeling = st.selectbox("你現在感覺如何？", list(LIFE_SCENARIOS.keys()))
        
        if st.button("取得回應"):
            scen = LIFE_SCENARIOS[feeling]
            # 顯示卡片
            st.markdown(f"""
            <div class="highlight-box" style="border-left: 5px solid #0066cc;">
                <h3>🩺 處方：{scen['msg']}</h3>
                <p>推薦專注主題：<b>{scen['theme']}</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            # 推薦經文
            mask = df.apply(lambda r: any(k in str(r['事件名稱']) or k in str(r['福音中心']) for k in scen['keywords']), axis=1)
            res = df[mask].head(3)
            if not res.empty:
                st.markdown("### 📖 推薦閱讀")
                for _, r in res.iterrows():
                    st.markdown(f"- **{r['事件名稱']}**：{r['福音中心']}")

    # ==========================================
    # 頁面 6: 數據分析 & 歷史軌跡
    # ==========================================
    elif selection == "📊 數據分析 & 歷史軌跡":
        st.header("📊 數據透視")
        
        tab1, tab2 = st.tabs(["📅 時空軌跡", "🔥 神學熱力圖"])
        
        with tab1:
            st.markdown("耶穌3.5年事工的時間軸分佈 (顏色代表不同時期/季節)")
            chart_time = alt.Chart(df).mark_circle(size=80).encode(
                x=alt.X('Order', title='時間順序'),
                y=alt.Y('地點', sort='-x'),
                color='季節',
                tooltip=['事件名稱', '地點', '福音中心']
            ).interactive()
            st.altair_chart(chart_time, use_container_width=True)
            
        with tab2:
            st.markdown("地點 vs 神學主題的關聯性 (圓點越大代表越常出現)")
            heat_data = df.groupby(['地點', '神學主題']).size().reset_index(name='count')
            heat_data = heat_data[heat_data['count'] > 0]
            chart_heat = alt.Chart(heat_data).mark_circle().encode(
                x='地點', y='神學主題', size='count', color='count',
                tooltip=['地點', '神學主題', 'count']
            ).interactive()
            st.altair_chart(chart_heat, use_container_width=True)

    # ==========================================
    # 頁面 7: 工具箱 (讀經/教材)
    # ==========================================
    elif selection == "📝 工具箱 (讀經/教材)":
        st.header("🛠️ 實用工具箱")
        t1, t2 = st.tabs(["📅 生成讀經計畫", "📄 生成小組教材"])
        
        with t1:
            st.subheader("打造專屬讀經計畫 (.ics)")
            days = st.number_input("你想花幾天讀完？", 7, 365, 30)
            start_d = st.date_input("開始日期", datetime.today())
            
            if st.button("生成計畫檔案"):
                per_day = len(df) / days
                plan = {}
                idx = 0
                for d in range(1, days + 1):
                    end = int(d * per_day)
                    if d == days: end = len(df)
                    day_events = []
                    for _, r in df.iloc[idx:end].iterrows():
                        day_events.append({"name": r['事件名稱'], "ref": r['經文總覽']})
                    plan[d] = day_events
                    idx = end
                
                ics_data = create_ics(plan, start_d)
                st.download_button("📥 下載行事曆 (.ics)", ics_data, "My_ReJesus_Plan.ics", "text/calendar")
                st.success("檔案已生成！請下載後匯入 Google/Apple 行事曆。")

        with t2:
            st.subheader("一鍵生成小組教材")
            evt = st.selectbox("選擇事件", df['事件名稱'].unique())
            row = df[df['事件名稱'] == evt].iloc[0]
            md = generate_markdown(row)
            
            st.markdown("---")
            c1, c2 = st.columns([2,1])
            with c1:
                st.markdown(md)
            with c2:
                st.download_button("📥 下載教材 (.md)", md, f"Study_{evt}.md", "text/markdown")

    # ==========================================
    # 頁面 8: 聖經知識王
    # ==========================================
    elif selection == "🏆 聖經知識王":
        st.header("🏆 知識挑戰")
        if 'quiz_idx' not in st.session_state:
            st.session_state.quiz_idx = random.randint(0, len(df)-1)
            st.session_state.quiz_revealed = False

        q_row = df.iloc[st.session_state.quiz_idx]
        
        st.markdown(f"### ❓ 題目：**「{q_row['事件名稱']}」** 發生在哪裡？")
        st.caption(f"提示：{q_row['福音中心']}")
        
        # 選項
        opts = list(set([q_row['地點']] + df['地點'].sample(3).tolist()))
        random.shuffle(opts)
        
        cols = st.columns(2)
        for i, opt in enumerate(opts):
            if cols[i%2].button(opt, key=opt):
                if opt == q_row['地點']:
                    st.success("🎉 答對了！")
                    st.balloons()
                else:
                    st.error(f"❌ 答錯了... 正確答案是 {q_row['地點']}")
                st.session_state.quiz_revealed = True
        
        if st.session_state.quiz_revealed:
            if st.button("🔄 下一題"):
                st.session_state.quiz_idx = random.randint(0, len(df)-1)
                st.session_state.quiz_revealed = False
                st.rerun()

    # ==========================================
    # 頁面 9: 福音對照透視
    # ==========================================
    elif selection == "🔢 福音對照透視":
        st.header("🔢 四福音書合參透視")
        
        filter_type = st.radio("篩選模式", ["全部", "四福音皆有 (核心)", "僅約翰福音 (獨家)"], horizontal=True)
        
        v_df = df.copy()
        if filter_type == "四福音皆有 (核心)":
            v_df = v_df[v_df['有_太'] & v_df['有_可'] & v_df['有_路'] & v_df['有_約']]
        elif filter_type == "僅約翰福音 (獨家)":
            v_df = v_df[v_df['有_約'] & ~v_df['有_太'] & ~v_df['有_可'] & ~v_df['有_路']]
            
        for _, r in v_df.iterrows():
            with st.container():
                c1, c2 = st.columns([3, 2])
                c1.markdown(f"**{r['事件名稱']}**")
                c1.caption(r['福音中心'])
                
                badges = ""
                for g in ['太', '可', '路', '約']:
                    color = "#28a745" if r[f'有_{g}'] else "#e2e6ea"
                    badges += f"<span style='background-color:{color}; color:white; padding:2px 6px; border-radius:4px; margin-right:4px; font-size:0.8em'>{g}</span>"
                c2.markdown(badges, unsafe_allow_html=True)
                st.divider()

if __name__ == "__main__":
    main()
