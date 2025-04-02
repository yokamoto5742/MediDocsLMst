import json
import os

import google.generativeai as genai

from utils.config import get_config, GEMINI_CREDENTIALS, GEMINI_MODEL
from utils.prompt_manager import get_prompt_by_department


def initialize_gemini():
    try:
        if GEMINI_CREDENTIALS:
            genai.configure(api_key=GEMINI_CREDENTIALS)
            return True
        else:
            raise ValueError("Gemini API認証情報が設定されていません。")

    except Exception as e:
        raise Exception(f"Gemini API初期化エラー: {str(e)}")


def create_discharge_summary_prompt(medical_text, department="default"):
    prompt_data = get_prompt_by_department(department)

    if not prompt_data:
        config = get_config()
        prompt_template = config['PROMPTS']['discharge_summary']
    else:
        prompt_template = prompt_data['content']

    prompt = f"{prompt_template}\n\n【カルテ情報】\n{medical_text}"

    return prompt


def generate_discharge_summary(medical_text, department="default"):
    try:
        initialize_gemini()
        model_name = os.environ.get("GEMINI_MODEL")
        model = genai.GenerativeModel(model_name)

        prompt = create_discharge_summary_prompt(medical_text, department)
        response = model.generate_content(prompt)

        # レスポンスからテキストを抽出
        if hasattr(response, 'text'):
            summary_text = response.text
        else:
            summary_text = str(response)

        return summary_text

    except Exception as e:
        error_msg = f"Gemini APIでエラーが発生しました: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)
