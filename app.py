import streamlit as st
from serpapi import GoogleSearch
from PIL import Image
import io
import tempfile
import os

st.set_page_config(page_title="探し物は何ですか？", page_icon="🔍", layout="wide")

# APIキー取得
try:
    SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
except Exception:
    st.error("⚠️ APIキーが設定されていません。Streamlit CloudのSecretsを確認してください。")
    st.stop()

st.title("🔍 探し物は何ですか？")

with st.sidebar:
    st.header("検索条件")
    uploaded_files = st.file_uploader("画像をアップロード", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
    part_number = st.text_input("品番")
    maker = st.text_input("メーカー名")
    keywords = st.text_input("キーワード")
    search_btn = st.button("この条件で探す", type="primary")

def process_and_search_lens(uploaded_file):
    # --- 画像の軽量化処理 ---
    # 大きすぎる画像はエラーの原因になるため、最大800pxにリサイズ
    img = Image.open(uploaded_file)
    img.thumbnail((800, 800))
    
    # 一時ファイルとして保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        img.convert("RGB").save(tmp.name, format="JPEG", quality=85)
        tmp_path = tmp.name

    try:
        # SerpApi推奨の送信方式 (fileパラメータ)
        params = {
            "engine": "google_lens",
            "api_key": SERPAPI_KEY,
            "hl": "ja"
        }
        search = GoogleSearch(params)
        # 内部でファイルを読み込んで送信
        res = search.get_dict(file=tmp_path)
        
        if "error" in res:
            st.warning(f"API通知: {res['error']}")
            return None
            
        matches = res.get("visual_matches", [])
        if not matches:
            # 視覚的一致がない場合、ショッピング結果をチェック
            matches = res.get("shopping_results", [])
            
        if matches:
            item = matches[0]
            return {
                "title": item.get("title", "商品名不明"),
                "price": item.get("price", {}).get("extracted", "価格不明") if isinstance(item.get("price"), dict) else item.get("price", "価格不明"),
                "source": item.get("source", "不明"),
                "link": item.get("link"),
                "thumbnail": item.get("thumbnail")
            }
    except Exception as e:
        # エラー詳細を表示
        st.error(f"詳細エラー: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return None

if search_btn:
    final_results = []

    # 1. 画像検索の実行
    if uploaded_files:
        with st.spinner("画像を最適化して解析中..."):
            for f in uploaded_files[:3]:
                res = process_and_search_lens(f)
                if res:
                    final_results.append(res)

    # 2. テキスト検索 (結果が不足している場合)
    if len(final_results) < 3:
        query = " ".join([p for p in [maker, part_number, keywords] if p])
        if query:
            with st.spinner(f"「{query}」で検索中..."):
                try:
                    search = GoogleSearch({
                        "engine": "google_shopping",
                        "q": query,
                        "api_key": SERPAPI_KEY,
                        "google_domain": "google.co.jp",
                        "hl": "ja",
                        "gl": "jp"
                    })
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
        st.error("商品が見つかりませんでした。別の画像をお試しください。")
    else:
        st.success("候補が見つかりました！")
        cols = st.columns(3)
        for i, item in enumerate(final_results[:3]):
            with cols[i]:
                with st.container(border=True):
                    if item.get("thumbnail"):
                        st.image(item["thumbnail"], use_container_width=True)
                    st.subheader(f"{item['title'][:25]}...")
                    st.write(f"💰 {item['price']}")
                    st.caption(f"🏬 {item['source']}")
                    st.link_button("商品を見る", item["link"], use_container_width=True)
