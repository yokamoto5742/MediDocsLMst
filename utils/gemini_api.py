import os
import google.generativeai as genai
from utils.text_processor import format_discharge_summary, extract_key_elements


def initialize_gemini():
    """
    Gemini APIのクライアントを初期化する関数

    Returns:
        bool: 初期化が成功したかどうか
    """
    api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("Gemini API Keyが設定されていません。サイドバーでAPIキーを入力してください。")

    # Gemini APIの設定
    genai.configure(api_key=api_key)
    return True


def create_discharge_summary_prompt(medical_text, format_type="標準形式"):
    """
    退院時サマリ生成用のプロンプトを作成する関数

    Args:
        medical_text (str): 前処理済みの医療テキスト
        format_type (str): 生成するサマリのフォーマットタイプ

    Returns:
        str: 構築されたプロンプト
    """
    # カルテから重要要素を抽出
    elements = extract_key_elements(medical_text)

    # フォーマットに応じたテンプレート選択
    format_instructions = {
        "標準形式": """
# 退院時サマリ

## 患者基本情報
- 患者ID: [患者ID]
- 入院日: [入院日]
- 退院日: [退院日]

## 診断名
[診断名]

## 入院理由と現病歴
[入院に至った経緯と現病歴]

## 入院後経過
[入院中の治療経過]

## 退院時状態
[退院時の患者の状態]

## 退院後治療計画
[退院後の治療計画と指示事項]

## 処方薬
[退院時処方薬]
""",
        "詳細形式": """
# 退院時サマリ - 詳細版

## 患者基本情報
- 患者ID: [患者ID]
- 入院日: [入院日]
- 退院日: [退院日]

## 診断名
### 主診断
[主診断]

### 副診断
[副診断]

## 入院理由と現病歴
### 主訴
[主訴]

### 現病歴
[現病歴の詳細]

### 既往歴
[既往歴]

## 入院後経過
### 検査所見
[重要な検査結果]

### 治療内容
[実施された治療の詳細]

### 臨床経過
[入院中の経過詳細]

## 退院時状態
### バイタルサイン
[退院時のバイタルサイン]

### 身体所見
[退院時の身体所見]

## 退院後治療計画
### 外来フォロー
[外来フォロー計画]

### 生活指導
[生活指導の内容]

## 処方薬
[退院時処方薬と用法用量]
""",
        "簡易形式": """
# 退院時サマリ（簡易版）

## 基本情報
[患者ID、入院期間]

## 診断
[診断名]

## 経過概要
[入院から退院までの簡潔な経過]

## 退院時処方と指示
[処方薬と退院指示]
"""
    }

    # プロンプト構築
    prompt = f"""
あなたは経験豊富な医師です。以下のカルテ情報から、正確で簡潔な退院時サマリを作成してください。

【フォーマット】
{format_instructions.get(format_type, format_instructions["標準形式"])}

【患者情報】
患者ID: {elements["patient_id"] if elements["patient_id"] else "不明"}
入院日: {elements["admission_date"] if elements["admission_date"] else "不明"}
退院日: {elements["discharge_date"] if elements["discharge_date"] else "不明"}
診断名: {", ".join(elements["diagnosis"]) if elements["diagnosis"] else "カルテから抽出"}

【カルテ情報】
{medical_text}

退院時サマリを上記のフォーマットに従って作成してください。
カルテに情報がない場合は、その項目は「記載なし」または「情報なし」と記載してください。
医学的に適切で、簡潔かつ明確な表現を使用してください。
"""
    return prompt


def generate_discharge_summary(medical_text, format_type="標準形式"):
    """
    Gemini APIを使用して退院時サマリを生成する関数

    Args:
        medical_text (str): 前処理済みの医療テキスト
        format_type (str): 生成するサマリのフォーマットタイプ

    Returns:
        str: 生成された退院時サマリ
    """
    try:
        # Gemini APIの初期化
        initialize_gemini()

        # Gemini 2.0 Flash モデルの設定
        model = genai.GenerativeModel('gemini-2.0-flash')

        # プロンプトの作成
        prompt = create_discharge_summary_prompt(medical_text, format_type)

        # 生成実行
        response = model.generate_content(prompt)

        # レスポンスからテキストを抽出
        if hasattr(response, 'text'):
            summary_text = response.text
        else:
            summary_text = str(response)

        # 生成されたテキストのフォーマット調整
        formatted_summary = format_discharge_summary(summary_text, format_type)

        return formatted_summary

    except Exception as e:
        # エラーをより詳細に表示
        error_msg = f"Gemini APIでエラーが発生しました: {str(e)}"
        print(error_msg)  # ログ出力
        raise Exception(error_msg)
