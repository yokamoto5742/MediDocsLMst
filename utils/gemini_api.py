import os
import json
import google.generativeai as genai

from utils.config import get_config


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
    config = get_config()
    prompt_template = config['PROMPTS']['discharge_summary']
    prompt = f"{prompt_template}\n\n【カルテ情報】\n{medical_text}"

    return prompt


def generate_discharge_summary(medical_text):
    try:
        initialize_gemini()
        config = get_config()
        model_name = config['GEMINI']['model']

        model = genai.GenerativeModel(model_name)

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
