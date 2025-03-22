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

# サイドバー - APIキー設定
with st.sidebar:
    st.header("設定")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

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
        if not api_key:
            st.error("⚠️ Gemini API Keyを入力してください")
            return

        if not input_text or len(input_text.strip()) < 10:
            st.warning("⚠️ カルテ情報を入力してください")
            return

        try:
            with st.spinner("退院時サマリを作成中..."):
                discharge_summary = generate_discharge_summary(input_text)

                # アスタリスクを削除
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

        # コピー操作の説明
        st.info("💡 テキストを選択して Ctrl+C でコピーできます")


if __name__ == "__main__":
    main()
