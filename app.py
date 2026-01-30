import streamlit as st
from serpapi import GoogleSearch
import tempfile
import os

# --- ページ設定 ---
st.set_page_config(page_title="探し物は何ですか？", page_icon="🔍", layout="wide")

# --- APIキー取得 ---
try:
    SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
except Exception:
    st.error("⚠️ APIキーが設定されていません。")
    st.stop()

st.title("🔍 探し物は何ですか？")
st.markdown("画像、品番、キーワードから商品を特定します。")

# --- サイドバー入力 ---
with st.sidebar:
    st.header("検索条件")
    # keyを設定して状態を安定させます
    uploaded_files = st.file_uploader("画像をアップロード (最大3枚)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], key="uploader")
    part_number = st.text_input("品番", key="pn")
    maker = st.text_input("メーカー名", key="mk")
    keywords = st.text_input("キーワード", key="kw")
    search_btn = st.button("この条件で探す", type="primary", key="btn")

# --- 検索ロジック ---
def execute_search(files, pn, mk, kw):
    all_results = []
    
    # 1. 画像がある場合は Google Lens を実行
    if files:
        st.info("📸 画像を解析中...")
        for uploaded_file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                params = {
                    "engine": "google_lens",
                    "file": tmp_path,
                    "api_key": SERPAPI_KEY,
                    "hl": "ja"
                }
                search = GoogleSearch(params)
                res_dict = search.get_dict()
                
                for item in res_dict.get("visual_matches", []):
                    all_results.append({
                        "title": item.get("title", "名称不明"),
                        "price": item.get("price", {}).get("extracted", "価格不明"),
                        "source": item.get("source", "不明"),
                        "link": item.get("link"),
                        "thumbnail": item.get("thumbnail")
                    })
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    # 2. テキスト情報がある場合は Shopping 検索を追加
    query_parts = [p for p in [mk, pn, kw] if p]
    if query_parts:
        query = " ".join(query_parts)
        st.info(f"🔎 テキスト検索中: {query}")
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": SERPAPI_KEY,
            "google_domain": "google.co.jp",
            "hl": "ja",
            "gl": "jp"
        }
        search = GoogleSearch(params)
        res_dict = search.get_dict()
        for item in res_dict.get("shopping_results", []):
            all_results.append({
                "title": item.get("title", "名称不明"),
                "price": item.get("price", "価格不明"),
                "source": item.get("source", "不明"),
                "link": item.get("link"),
                "thumbnail": item.get("thumbnail")
            })

    return all_results

# --- メイン表示 ---
if search_btn:
    if not uploaded_files and not part_number and not keywords:
        st.warning("⚠️ 画像またはテキストを入力してください。")
    else:
        # 検索実行
        found_items = execute_search(uploaded_files, part_number, maker, keywords)
        
        if not found_items:
            st.error("該当する商品が見つかりませんでした。")
        else:
            st.success("該当しそうな商品が見つかりました！")
            st.divider()
            
            # 出力は3つに限定
            display_items = found_items[:3]
            cols = st.columns(3)
            
            # enumerateの代わりにrangeを使ってインデックスを確実に管理
            for idx in range(len(display_items)):
                item = display_items[idx]
                with cols[idx]:
                    with st.container(border=True):
                        if item.get("thumbnail"):
                            st.image(item["thumbnail"], use_container_width=True)
                        st.subheader(item['title'][:25] + "...")
                        st.write(f"**{item['price']}**")
                        st.caption(f"販売元: {item['source']}")
                        if item.get("link"):
                            st.link_button("👉 商品ページを見る", item["link"], use_container_width=True)
