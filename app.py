import streamlit as st
import os
from utils.gemini_api import generate_discharge_summary
from utils.text_processor import format_discharge_summary, parse_discharge_summary

st.set_page_config(
    page_title="退院時サマリ作成アプリ",
    page_icon="🏥",
    layout="wide"
)

# セッション状態の初期化
if "discharge_summary" not in st.session_state:
    st.session_state.discharge_summary = ""
if "parsed_summary" not in st.session_state:
    st.session_state.parsed_summary = {}

st.title("退院時サマリ作成アプリ")

# メイン機能
def main():
    # テキスト入力
    input_text = st.text_area(
        "入力および出力テキストは保存されません",
        height=100,
        placeholder="ここにテキストを貼り付けてください..."
    )

    # 実行ボタン
    if st.button("退院時サマリ作成", type="primary"):
        # APIキーが設定されているか環境変数を確認
        if not os.environ.get("GEMINI_CREDENTIALS"):
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

                # 退院時サマリを項目ごとに分割
                parsed_summary = parse_discharge_summary(discharge_summary)
                st.session_state.parsed_summary = parsed_summary

        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

    if st.session_state.discharge_summary:
        # 退院時サマリの表示
        if st.session_state.parsed_summary:
            # タブを作成
            tabs = st.tabs([
                "全文", "入院期間", "現病歴", "入院時検査",
                "入院中の治療経過", "退院申し送り", "禁忌/アレルギー"
            ])

            # 全文タブ
            with tabs[0]:
                st.text_area(
                    "生成結果 (全文)",
                    value=st.session_state.discharge_summary,
                    height=300
                )

            # 各項目タブ
            sections = ["入院期間", "現病歴", "入院時検査", "入院中の治療経過", "退院申し送り", "禁忌/アレルギー"]
            for i, section in enumerate(sections, 1):
                with tabs[i]:
                    section_content = st.session_state.parsed_summary.get(section, "")
                    st.text_area(
                        f"{section}",
                        value=section_content,
                        height=300
                    )

        st.info("💡 テキストを選択して Ctrl+C でコピーできます")


if __name__ == "__main__":
    main()