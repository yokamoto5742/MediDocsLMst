import json
import os

import google.generativeai as genai

from utils.config import get_config, GEMINI_CREDENTIALS, GEMINI_MODEL
from utils.constants import MESSAGES
from utils.prompt_manager import get_prompt_by_department
from utils.exceptions import APIError


def initialize_gemini():
    try:
        if GEMINI_CREDENTIALS:
            genai.configure(api_key=GEMINI_CREDENTIALS)
            return True
        else:
            raise APIError(MESSAGES["API_CREDENTIALS_MISSING"])

    except Exception as e:
        raise APIError(f"Gemini API初期化エラー: {str(e)}")


def create_discharge_summary_prompt(medical_text, department="default"):
    prompt_data = get_prompt_by_department(department)

    if not prompt_data:
        config = get_config()
        prompt_template = config['PROMPTS']['discharge_summary']
    else:
        prompt_template = prompt_data['content']

    prompt = f"{prompt_template}\n\n【カルテ情報】\n{medical_text}"

    return prompt


def generate_discharge_summary(medical_text, department="default", model_name=None):
    try:
        initialize_gemini()
        if not model_name:
            model_name = GEMINI_MODEL
        model = genai.GenerativeModel(model_name)

        prompt = create_discharge_summary_prompt(medical_text, department)
        response = model.generate_content(prompt)

        if hasattr(response, 'text'):
            summary_text = response.text
        else:
            summary_text = str(response)

        input_tokens = 0
        output_tokens = 0

        if hasattr(response, 'usage_metadata'):
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count

        return summary_text, input_tokens, output_tokens

    except APIError as e:
        raise e
    except Exception as e:
        raise APIError(f"Gemini APIでエラーが発生しました: {str(e)}")
