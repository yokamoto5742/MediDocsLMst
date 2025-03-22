import os
import json
import google.generativeai as genai


def initialize_gemini():
    try:
        if 'GEMINI_CREDENTIALS' in os.environ:
            api_key = os.environ.get('GEMINI_CREDENTIALS')

            if not api_key:
                raise ValueError("認証情報にapi_keyが含まれていません。")

            genai.configure(api_key=api_key)
            return True

    except Exception as e:
        raise Exception(f"Gemini API初期化エラー: {str(e)}")


def create_discharge_summary_prompt(medical_text):
    """
    退院時サマリ生成用のプロンプトを作成する関数

    Args:
        medical_text (str): 医療テキスト

    Returns:
        str: 構築されたプロンプト
    """
    # 添付されたプロンプトファイルの内容を使用
    prompt = f"""あなたは経験豊富な医療文書作成の専門家です。
当院のフォーマットに従って退院時サマリを作成してください
このカルテ記載を使用して、包括的で簡潔な退院時サマリを作成してください。
医療専門用語を適切に使用し、重要な情報を漏らさず、読みやすく整理された文書を作成してください。
医療従事者が読みやすく、必要な情報を迅速に把握できるような文書を作成してください。

退院時サマリの構造:
・入院期間

・現病歴(入院日までの情報のみを記載)

・入院時検査

・入院中の治療経過
入院中に投与された重要な薬剤
手術情報(手術日と術式のみ)
処置情報(侵襲のある処置日と処置名のみ)

・退院申し送り
退院時方針
退院時処方


・禁忌/アレルギー

【カルテ情報】
{medical_text}
"""
    return prompt


def generate_discharge_summary(medical_text):
    """
    Gemini APIを使用して退院時サマリを生成する関数

    Args:
        medical_text (str): 医療テキスト

    Returns:
        str: 生成された退院時サマリ
    """
    try:
        initialize_gemini()
        model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')  # 安定版は gemini-2.0-flash

        # プロンプトの作成
        prompt = create_discharge_summary_prompt(medical_text)

        # 生成実行
        response = model.generate_content(prompt)

        # レスポンスからテキストを抽出
        if hasattr(response, 'text'):
            summary_text = response.text
        else:
            summary_text = str(response)

        return summary_text

    except Exception as e:
        # エラーをより詳細に表示
        error_msg = f"Gemini APIでエラーが発生しました: {str(e)}"
        print(error_msg)  # ログ出力
        raise Exception(error_msg)
