import streamlit as st
from serpapi import GoogleSearch
import base64

st.set_page_config(page_title="探し物は何ですか？", page_icon="🔍", layout="wide")

# APIキー取得
try:
    SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
except Exception:
    st.error("⚠️ APIキーが設定されていません。")
    st.stop()

st.title("🔍 探し物は何ですか？")

with st.sidebar:
    st.header("検索条件")
    uploaded_files = st.file_uploader("画像をアップロード", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
    part_number = st.text_input("品番")
    maker = st.text_input("メーカー名")
    keywords = st.text_input("キーワード")
    search_btn = st.button("この条件で探す", type="primary")

def execute_combined_search():
    final_results = []
    
    # 1. 画像検索 (Google Lens)
    if uploaded_files:
        with st.spinner("画像を解析中..."):
            for f in uploaded_files[:3]:
                # 画像をBase64に変換して直接送る手法を試みます
                base64_image = base64.b64encode(f.getvalue()).decode('utf-8')
                params = {
                    "engine": "google_lens",
                    "base64_image": base64_image,
                    "api_key": SERPAPI_KEY,
                    "hl": "ja"
                }
                try:
                    search = GoogleSearch(params)
                    res = search.get_dict()
                    # 'visual_matches' が空の場合、'knowledge_graph' なども探す
                    items = res.get("visual_matches", [])
                    if not items:
                        # ショッピング結果があればそれを使う
                        items = res.get("shopping_results", [])
                    
                    if items:
                        item = items[0]
                        final_results.append({
                            "title": item.get("title", "商品名不明"),
                            "price": item.get("price", {}).get("extracted", "価格不明") if isinstance(item.get("price"), dict) else item.get("price", "価格不明"),
                            "source": item.get("source", "不明"),
                            "link": item.get("link"),
                            "thumbnail": item.get("thumbnail")
                        })
                except Exception as e:
                    st.error(f"Lens解析エラー: {e}")

    # 2. テキスト検索 (Google Shopping) - 結果が3つに満たない場合
    if len(final_results) < 3:
        query = " ".join([p for p in [maker, part_number, keywords] if p])
        if query:
            with st.spinner(f"「{query}」で検索中..."):
                params = {
                    "engine": "google_shopping",
                    "q": query,
                    "api_key": SERPAPI_KEY,
                    "google_domain": "google.co.jp",
                    "hl": "ja",
                    "gl": "jp"
                }
                try:
                    search = GoogleSearch(params)
                    shopping_res = search.get_dict().get("shopping_results", [])
                    for s_item in shopping_res:
                        if len(final_results) >= 3: break
                        final_results.append({
                            "title": s_item.get("title"),
                            "price": s_item.get("price"),
                            "source": s_item.get("source"),
                            "link": s_item.get("link"),
                            "thumbnail": s_item.get("thumbnail")
                        })
                except Exception:
                    pass

    return final_results

if search_btn:
    results = execute_combined_search()
    
    if not results:
        st.error("やはり商品が見つかりませんでした。SerpApiの無料枠の上限、または画像のサイズが大きすぎる可能性があります。")
    else:
        st.success("候補が見つかりました！")
        cols = st.columns(3)
        for i, item in enumerate(results[:3]):
            with cols[i]:
                with st.container(border=True):
                    if item.get("thumbnail"):
                        st.image(item["thumbnail"], use_container_width=True)
                    st.subheader(f"{item['title'][:30]}...")
                    st.write(f"💰 {item['price']}")
                    st.caption(f"🏬 {item['source']}")
                    st.link_button("商品を見る", item["link"], use_container_width=True)
