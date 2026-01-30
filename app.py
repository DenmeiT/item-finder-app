import streamlit as st
from serpapi import GoogleSearch

# --- ページ設定 ---
st.set_page_config(page_title="探し物は何ですか？", page_icon="🔍", layout="wide")

# --- APIキーの取得 (セキュリティ対応) ---
# Streamlit CloudのSecrets、またはローカルのsecrets.tomlからキーを読み込みます
try:
    if "SERPAPI_KEY" in st.secrets:
        SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
    else:
        # シークレットが設定されていない場合のフォールバック（またはエラー表示）
        st.error("⚠️ APIキーが設定されていません。Streamlit CloudのSecrets設定を確認してください。")
        st.stop()
except FileNotFoundError:
    st.error("⚠️ secretsファイルが見つかりません。")
    st.stop()

# --- タイトルと説明 ---
st.title("🔍 探し物は何ですか？")
st.markdown("曖昧な記憶やキーワードから、該当する商品を3つ提案します。")

# --- サイドバー：入力エリア ---
with st.sidebar:
    st.header("検索条件")
    
    # 画像入力 (最大3枚)
    uploaded_files = st.file_uploader(
        "画像をアップロード (最大3枚)", 
        accept_multiple_files=True, 
        type=['png', 'jpg', 'jpeg']
    )
    
    # テキスト入力
    st.caption("以下のいずれかを入力してください")
    part_number = st.text_input("品番", placeholder="例: WH-1000XM5")
    maker = st.text_input("メーカー名", placeholder="例: SONY")
    keywords = st.text_input("キーワード", placeholder="例: ワイヤレスヘッドホン ノイズキャンセリング")
    
    search_btn = st.button("この条件で探す", type="primary")

# --- ロジック部分 ---
def get_search_query(part_number, maker, keywords):
    # 空白を除去してリスト化し、検索クエリを作成
    parts = [p.strip() for p in [maker, part_number, keywords] if p and p.strip()]
    return " ".join(parts)

# --- メイン処理 ---
if search_btn:
    # 検索クエリの作成
    query = get_search_query(part_number, maker, keywords)
    
    # バリデーション
    if not query:
        st.warning("⚠️ 品番、メーカー名、キーワードのいずれかを入力してください。（画像検索機能は現在準備中です）")
    else:
        st.info(f"🔎 「{query}」で商品を検索中...")
        
        try:
            # SerpApi (Google Shopping) を実行
            params = {
                "api_key": SERPAPI_KEY,
                "engine": "google_shopping",  # ショッピング検索
                "q": query,                   # 検索クエリ
                "google_domain": "google.co.jp", 
                "gl": "jp",                   # 地域: 日本
                "hl": "ja",                   # 言語: 日本語
                "num": 3                      # 取得件数
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # 結果の抽出
            shopping_results = results.get("shopping_results", [])
            
            if not shopping_results:
                st.warning("該当する商品が見つかりませんでした。別のキーワードを試してみてください。")
            else:
                st.success(f"{len(shopping_results)} 件の候補が見つかりました！")
                st.divider()
                
                # --- 結果表示 (3列カラム) ---
                cols = st.columns(3)
                
                for i, item in enumerate(shopping_results[:3]): # 最大3件
                    with cols[i]:
                        # コンテナを使ってカード風に表示
                        with st.container(border=True):
                            # 画像表示
                            image_url = item.get("thumbnail")
                            if image_url:
                                st.image(image_url, use_container_width=True)
                            else:
                                st.text("画像なし")
                            
                            # 商品タイトル
                            title = item.get("title", "名称不明")
                            st.subheader(f"{title[:20]}...") # 長すぎる場合は省略
                            
                            # 価格と販売元
                            price = item.get("price", "価格不明")
                            source = item.get("source", "不明なショップ")
                            st.write(f"**{price}**")
                            st.caption(f"販売元: {source}")
                            
                            # リンクボタン
                            link = item.get("link")
                            if link:
                                st.link_button("👉 商品ページを見る", link, use_container_width=True)
                            
                            # 詳細（折りたたみ）
                            with st.expander("詳細情報"):
                                st.write(title)

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

# --- アップロードされた画像のプレビュー ---
if uploaded_files:
    st.divider()
    st.caption("📂 アップロードされた画像（参考）")
    preview_cols = st.columns(len(uploaded_files))
    for i, file in enumerate(uploaded_files):
        with preview_cols[i]:
            st.image(file, width=150)