import streamlit as st
from serpapi import GoogleSearch
import base64
from PIL import Image
import io

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

def get_base64_image(uploaded_file):
    """画像をリサイズしてBase64文字列に変換"""
    img = Image.open(uploaded_file)
    img.thumbnail((500, 500)) # サイズを小さくして転送エラーを防ぐ
    buffered = io.BytesIO()
    img.convert("RGB").save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

if search_btn:
    final_results = []

    # 1. 画像検索の実行
    if uploaded_files:
        with st.spinner("画像を解析中..."):
            for f in uploaded_files[:3]:
                try:
                    b64_data = get_base64_image(f)
                    # パラメータを極限までシンプルに
                    params = {
                        "engine": "google_lens",
                        "base64_image": b64_data,
                        "api_key": SERPAPI_KEY
                    }
                    search = GoogleSearch(params)
                    res = search.get_dict()
                    
                    # デバッグ用（もし何も出ない場合はここを確認）
                    # st.write(res) 
                    
                    matches = res.get("visual_matches", [])
                    if matches:
                        item = matches[0]
                        final_results.append({
                            "title": item.get("title", "商品名不明"),
                            "price": item.get("price", {}).get("extracted", "価格不明") if isinstance(item.get("price"), dict) else "価格不明",
                            "source": item.get("source", "不明"),
                            "link": item.get("link"),
                            "thumbnail": item.get("thumbnail")
                        })
                except Exception as e:
                    st.error(f"解析エラー: {e}")

    # 2. テキスト検索 (結果が不足している場合、または画像がない場合)
    query_parts = [p for p in [maker, part_number, keywords] if p]
    if len(final_results) < 3 and query_parts:
        query = " ".join(query_parts)
        with st.spinner(f"テキスト「{query}」で検索中..."):
            try:
                params = {
                    "engine": "google_shopping",
                    "q": query,
                    "api_key": SERPAPI_KEY,
                    "google_domain": "google.co.jp",
                    "hl": "ja",
                    "gl": "jp"
                }
                search = GoogleSearch(params)
                s_res = search.get_dict().get("shopping_results", [])
                for s_item in s_res:
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

    # 表示
    if not final_results:
        st.error("商品が見つかりませんでした。別の画像や、より具体的な品番を入力してください。")
    else:
        st.success("候補が見つかりました！")
        cols = st.columns(3)
        for i in range(len(final_results[:3])):
            item = final_results[i]
            with cols[i]:
                with st.container(border=True):
                    if item.get("thumbnail"):
                        st.image(item["thumbnail"], use_container_width=True)
                    st.subheader(f"{item['title'][:25]}...")
                    st.write(f"💰 {item['price']}")
                    st.caption(f"🏬 {item['source']}")
                    st.link_button("商品を見る", item["link"], use_container_width=True)
