import streamlit as st
import pandas as pd
import requests
from opencc import OpenCC

# --- 1. 設定頁面 ---
st.set_page_config(page_title="Re:Jesus 經文版", page_icon="✝️")

# 初始化繁簡轉換器 (簡體 -> 台灣繁體)
cc = OpenCC('s2twp')

# --- 2. 建立萬能書卷對照表 (這是最關鍵的一步) ---
# API 只看得懂英文全名 (Matthew)，所以我們要建立一個字典來翻譯
BOOK_MAP = {
    # 英文縮寫
    "Mt": "馬太福音", "Mk": "馬可福音", "Lk": "路加福音", "Jn": "約翰福音",
    "Mat": "馬太福音", "Mrk": "馬可福音", "Luk": "路加福音", "Jhn": "約翰福音",
    # 中文縮寫 (您的 CSV 裡面的格式)
    "太": "馬太福音w", "可": "馬可福音", "路": "路加福音", "約": "約翰福音",
    "馬太": "馬太福音", "馬可": "馬可福音", "路加": "路加福音", "約翰": "約翰福音"
}

# --- 3. 定義抓取經文的函數 ---
@st.cache_data(ttl=86400)
def fetch_bible_text(ref_string):
    if pd.isna(ref_string): return None
    ref_string = str(ref_string).strip()
    
    try:
        # --- 除錯步驟 A: 檢查輸入 ---
        # st.write(f"正在處理: {ref_string}") # 想看詳細可以取消這行註解

        import re
        if " " not in ref_string:
            ref_string = re.sub(r"([a-zA-Z\u4e00-\u9fa5]+)(\d)", r"\1 \2", ref_string)
            
        parts = ref_string.split(maxsplit=1)
        if len(parts) < 2:
            st.error(f"格式錯誤，無法拆分章節: {ref_string}") # 顯示錯誤
            return None

        book_abbr = parts[0]
        verse = parts[1]
        
        # --- 除錯步驟 B: 檢查對照表 ---
        api_book = BOOK_MAP.get(book_abbr, book_abbr)
        # st.write(f"書卷轉換: {book_abbr} -> {api_book}") # 想看詳細可以取消這行註解
        
        url = f"https://bible-api.com/{api_book}+{verse}?translation=cuv"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # 檢查 API 是否真的回傳了經文
            if 'text' not in data or not data['text']:
                st.warning(f"API 有回應但無經文: {url}")
                return None
            return cc.convert(data['text'])
        else:
            st.error(f"API 連線失敗 (代碼 {response.status_code}): {url}") # 顯示錯誤
            return None
            
    except Exception as e:
        st.error(f"程式發生錯誤: {e}") # 顯示錯誤
        return None
        
# --- 4. 主程式 ---
def main():
    st.title("✝️ Re:Jesus 經文查詢測試")
    
    # 讀取資料
    try:
        df = pd.read_csv("data.csv")
    except:
        st.error("找不到 data.csv")
        return

    # 顯示搜尋框
    search = st.text_input("搜尋事件 (例如: 登山寶訓)")
    
    if search:
        results = df[df['事件名稱'].str.contains(search, case=False)]
        
        for index, row in results.iterrows():
            with st.expander(f"{row['事件名稱']} ({row['經文總覽']})"):
                st.write(f"**福音中心**：{row['福音中心']}")
                
                # --- 這裡就是呼叫上面那個函數的地方 ---
                # 我們嘗試抓取「馬太福音」的經文
                if pd.notna(row['經文_太']):
                    st.markdown("---")
                    st.caption(f"📖 馬太福音 {row['經文_太']}")
                    
                    # 呼叫函數！
                    text = fetch_bible_text(row['經文_太'])
                    
                    if text:
                        st.info(text) # 成功抓到，顯示經文
                    else:
                        st.warning("暫時無法自動抓取此經文，請查閱聖經。")
                        # 提供備用連結
                        st.markdown(f"[點此前往網頁閱讀](https://www.bible.com/zh-TW/bible/46/MAT.1.CUNP)")

if __name__ == "__main__":
    main()
