import streamlit as st
import os
from utils.gemini_api import generate_discharge_summary
from utils.text_processor import format_discharge_summary

# ページ設定
st.set_page_config(
    page_title="退院時サマリ作成アプリ",
    page_icon="🏥",
    layout="wide"
)

# セッション状態の初期化
if "discharge_summary" not in st.session_state:
    st.session_state.discharge_summary = ""

st.title("退院時サマリ作成アプリ")

# サイドバー - 設定情報表示
with st.sidebar:
    st.header("設定")
    st.info("Gemini APIキーは環境変数から読み込まれます。以下のいずれかを設定してください：")
    st.code("""
# 方法1: 直接APIキーを設定
GOOGLE_API_KEY=あなたのAPIキー

# 方法2: JSON形式で設定
GEMINI_CREDENTIALS={"api_key": "あなたのAPIキー"}
    """)

    st.markdown("---")
    st.subheader("注意事項")
    st.markdown("""
    - 入力および出力テキストはサーバーに保存されません
    - 個人情報の取り扱いには十分ご注意ください
    """)


# メイン機能
def main():

    # テキスト入力
    input_text = st.text_area(
        "電子カルテのテキストデータから退院時サマリを作成します",
        height=200,
        placeholder="ここにテキストを貼り付けてください..."
    )

    # 実行ボタン
    if st.button("退院時サマリを作成", type="primary"):
        # APIキーが設定されているか環境変数を確認
        if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_CREDENTIALS"):
            st.error("⚠️ Gemini APIの認証情報が設定されていません。環境変数を確認してください。")
            return

        if not input_text or len(input_text.strip()) < 10:
            st.warning("⚠️ カルテ情報を入力してください")
            return

        try:
            with st.spinner("退院時サマリを作成中..."):
                discharge_summary = generate_discharge_summary(input_text)

                discharge_summary = format_discharge_summary(discharge_summary)

                st.session_state.discharge_summary = discharge_summary

        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

    if st.session_state.discharge_summary:
        st.header("退院時サマリ")
        st.text_area(
            "生成結果",
            value=st.session_state.discharge_summary,
            height=400
        )

        st.info("💡 テキストを選択して Ctrl+C でコピーできます")


if __name__ == "__main__":
    main()
