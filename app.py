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
                for _, row in day_events.iterrows():
                    event_list.append({
                        "id": row['EventID'],
                        "name": row['事件名稱'],
                        "ref": row['經文總覽']
                    })
                
                plan_preview[current_day] = event_list
                idx = end_idx
                current_day += 1

            # 顯示下載按鈕
            ics_string = create_ics_file(plan_preview, start_date)
            st.success(f"已成功規劃 {days} 天的旅程！")
            
            st.download_button(
                label="📅 加入我的行事曆 (下載 .ics 檔)",
                data=ics_string,
                file_name="ReJesus_Reading_Plan.ics",
                mime="text/calendar"
            )
            
            # 顯示預覽表格
            st.subheader("📋 計畫預覽")
            for d, evs in list(plan_preview.items())[:5]: # 只顯示前5天
                with st.expander(f"Day {d} (預計閱讀 {len(evs)} 個事件)"):
                    for e in evs:
                        st.markdown(f"- **{e['name']}** : {e['ref']}")
            if days > 5:
                st.caption("... (後續天數請下載行事曆查看)")

    # === 功能 2: 聖經知識王 (Gamification) ===
    elif menu == "🏆 聖經知識王":
        st.header("🏆 挑戰：你有多認識耶穌？")
        st.markdown("測試看看你對耶穌生平細節的熟悉度！")
        
        # 初始化 Session State
        if 'quiz_q' not in st.session_state:
            st.session_state.quiz_q = None
            st.session_state.quiz_opt = []
            st.session_state.quiz_ans = None
            st.session_state.quiz_revealed = False

        # 出題邏輯
        if st.session_state.quiz_q is None or st.button("🔄 下一題"):
            # 隨機選一個事件
            target = df.sample(1).iloc[0]
            st.session_state.quiz_ans = target['地點']
            
            # 題目：這個事件發生在哪裡？
            st.session_state.quiz_q = f"請問 **「{target['事件名稱']}」** 發生在哪裡？"
            st.session_state.quiz_target_row = target
            
            # 產生選項 (1個正確 + 3個錯誤)
            options = set([target['地點']])
            while len(options) < 4:
                options.add(df.sample(1).iloc[0]['地點'])
            st.session_state.quiz_opt = list(options)
            st.session_state.quiz_revealed = False
            
            # 強制刷新按鈕狀態
            st.rerun()

        # 顯示題目
        st.markdown(f"### ❓ {st.session_state.quiz_q}")
        st.markdown(f"> 提示：{st.session_state.quiz_target_row['福音中心']}")
        
        # 顯示選項按鈕
        if not st.session_state.quiz_revealed:
            cols = st.columns(2)
            for i, opt in enumerate(st.session_state.quiz_opt):
                if cols[i % 2].button(opt, key=f"opt_{i}"):
                    if opt == st.session_state.quiz_ans:
                        st.success(f"🎉 答對了！就是 {opt}！")
                        st.balloons()
                    else:
                        st.error(f"❌ 答錯了... 正確答案是 {st.session_state.quiz_ans}")
                    
                    st.session_state.quiz_revealed = True
                    st.rerun()
        else:
            # 揭曉答案後的畫面
            st.info(f"正確答案：**{st.session_state.quiz_ans}**")
            st.markdown("---")
            st.markdown(f"**📖 事件詳情**：")
            st.write(st.session_state.quiz_target_row['事件名稱'])
            st.caption(st.session_state.quiz_target_row['經文總覽'])

    # === 功能 3: 神學熱力圖 (Analytics) ===
    elif menu == "📊 神學熱力圖":
        st.header("📊 地點 vs 神學主題 透視")
        st.markdown("這張圖表展示了耶穌在「不同地點」主要都在教導或經歷「什麼主題」。圓點越大/顏色越深，代表事件越多。")
        
        # 資料聚合
        heatmap_data = df.groupby(['地點', '神學主題']).size().reset_index(name='次數')
        
        # 過濾掉次數太少的，避免圖表太亂
        heatmap_data = heatmap_data[heatmap_data['次數'] > 0]
        
        # Altair 圖表
        chart = alt.Chart(heatmap_data).mark_circle().encode(
            x=alt.X('地點', sort=None),
            y=alt.Y('神學主題', sort=None),
            size='次數',
            color=alt.Color('次數', scale=alt.Scale(scheme='orangered')),
            tooltip=['地點', '神學主題', '次數']
        ).properties(
            height=600
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)
        st.info("💡 觀察：你可以看到「耶路撒冷」集中了許多關於「受難、彌賽亞」的主題，而「加利利」則更多關於「神蹟、呼召」。")

    # === 功能 4: AI 導覽員 (Chat - 保留) ===
    elif menu == "💬 AI 導覽員":
        st.header("💬 與資料對話")
        st.markdown("輸入你的感受或關鍵字，讓系統為你尋找相關經文。")
        
        # 簡易聊天邏輯
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "平安！您今天想了解耶穌的什麼事蹟？或是有什麼心情想分享？"}]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("輸入關鍵字 (例如: 焦慮, 信心, 醫治)..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            # 搜尋
            mask = df.apply(lambda r: prompt in str(r['事件名稱']) or prompt in str(r['福音中心']) or prompt in str(r['神學主題']), axis=1)
            res = df[mask]
            
            if not res.empty:
                reply = f"找到 {len(res)} 筆相關資料：\n\n"
                for i, row in res.head(3).iterrows():
                    reply += f"🔹 **{row['事件名稱']}** ({row['地點']})\n> {row['福音中心']}\n\n"
                reply += "..."
            else:
                reply = "抱歉，資料庫中暫時沒有找到直接相關的事件。試試看「神蹟」或「禱告」？"
            
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").write(reply)

if __name__ == "__main__":
    main()
