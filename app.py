import streamlit as st
from serpapi import GoogleSearch
import tempfile
import os

st.set_page_config(page_title="探し物は何ですか？", page_icon="🔍", layout="wide")

try:
    SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
except Exception:
    st.error("⚠️ APIキーが設定されていません。")
    st.stop()

st.title("🔍 探し物は何ですか？")

with st.sidebar:
    st.header("検索条件")
    uploaded_files = st.file_uploader("画像をアップロード", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], key="uploader")
    part_number = st.text_input("品番", key="pn")
    maker = st.text_input("メーカー名", key="mk")
    keywords = st.text_input("キーワード", key="kw")
    search_btn = st.button("この条件で探す", type="primary", key="btn")

def get_items_from_res(res_dict, engine):
    """APIの結果から共通フォーマットでリスト化する"""
    extracted = []
    if engine == "google_lens":
        for item in res_dict.get("visual_matches", []):
            extracted.append({
                "title": item.get("title", "名称不明"),
                "price": item.get("price", {}).get("extracted", "価格不明"),
                "source": item.get("source", "不明"),
                "link": item.get("link"),
                "thumbnail": item.get("thumbnail")
            })
    else:
        for item in res_dict.get("shopping_results", []):
            extracted.append({
                "title": item.get("title", "名称不明"),
                "price": item.get("price", "価格不明"),
                "source": item.get("source", "不明"),
                "link": item.get("link"),
                "thumbnail": item.get("thumbnail")
            })
    return extracted

if search_btn:
    all_results = []
    
    # 1. 画像検索
    if uploaded_files:
        with st.spinner("画像を解析中..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(uploaded_files[0].getvalue())
                tmp_path = tmp_file.name
            try:
                search = GoogleSearch({"engine": "google_lens", "file": tmp_path, "api_key": SERPAPI_KEY, "hl": "ja"})
                all_results.extend(get_items_from_res(search.get_dict(), "google_lens"))
            finally:
                if os.path.exists(tmp_path): os.remove(tmp_path)

    # 2. テキスト検索 (段階的に試行)
    search_queries = []
    if maker and part_number: search_queries.append(f"{maker} {part_number}")
    if part_number: search_queries.append(part_number)
    if keywords: search_queries.append(keywords)
    
    # 重複削除
    search_queries = list(dict.fromkeys(search_queries))

    if not all_results and search_queries:
        for q in search_queries:
            with st.spinner(f"「{q}」で検索中..."):
                params = {"engine": "google_shopping", "q": q, "api_key": SERPAPI_KEY, "google_domain": "google.co.jp", "hl": "ja", "gl": "jp"}
                res = GoogleSearch(params).get_dict()
                found = get_items_from_res(res, "google_shopping")
                if found:
                    all_results.extend(found)
                    break # 見つかったらループを抜ける

    # 結果表示
    if not all_results:
        st.error("該当する商品が見つかりませんでした。品番のみ、あるいはメーカー名のみなど、入力をシンプルにして再度お試しください。")
    else:
        st.success(f"{len(all_results)} 件見つかりました。")
        cols = st.columns(3)
        for idx in range(min(3, len(all_results))):
            item = all_results[idx]
            with cols[idx]:
                with st.container(border=True):
                    if item.get("thumbnail"): st.image(item["thumbnail"], use_container_width=True)
                    st.subheader(item['title'][:30] + "...")
                    st.write(f"**{item['price']}**")
                    st.caption(f"販売元: {item['source']}")
                    if item.get("link"): st.link_button("👉 商品を見る", item["link"], use_container_width=True)
