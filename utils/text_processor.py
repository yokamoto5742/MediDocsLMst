import re


def preprocess_text(text):
    """
    カルテテキストの前処理を行う関数

    Args:
        text (str): 入力カルテテキスト

    Returns:
        str: 前処理済みのテキスト
    """
    if not text:
        return ""

    # 余分な空白の削除
    processed_text = re.sub(r'\s+', ' ', text)

    # 基本的なクリーニング
    processed_text = processed_text.strip()

    # 連続する改行を一つの改行に置換
    processed_text = re.sub(r'\n+', '\n', processed_text)

    # 全角括弧内のスペースを削除
    processed_text = re.sub(r'（\s+', '（', processed_text)
    processed_text = re.sub(r'\s+）', '）', processed_text)

    # テキストが長すぎる場合の処理（Gemini APIの制限を考慮）
    if len(processed_text) > 100000:
        # 最初の100,000文字に制限
        processed_text = processed_text[:100000]
        print("警告: テキストが長すぎるため、最初の100,000文字に制限されました。")

    return processed_text


def format_discharge_summary(summary_text, format_type="標準形式"):
    """
    生成された退院時サマリのフォーマットを整える関数

    Args:
        summary_text (str): Gemini APIから生成されたサマリテキスト
        format_type (str): サマリのフォーマットタイプ

    Returns:
        str: フォーマット済みのサマリテキスト
    """
    if not summary_text:
        return ""

    # 基本的なクリーニング
    formatted_text = summary_text.strip()

    # フォーマットタイプに基づく追加処理
    if format_type == "標準形式":
        # そのまま返す
        pass
    elif format_type == "詳細形式":
        # 見出しの強調
        formatted_text = re.sub(r'^(#+\s*.*?)$', r'\1\n', formatted_text, flags=re.MULTILINE)
    elif format_type == "簡易形式":
        # 箇条書きの整理
        formatted_text = re.sub(r'\n\s*[-•]\s+', '\n• ', formatted_text)

    return formatted_text


def extract_key_elements(text):
    """
    カルテテキストから重要な要素を抽出する関数

    Args:
        text (str): 入力カルテテキスト

    Returns:
        dict: 抽出された要素を含む辞書
    """
    elements = {
        "patient_id": None,
        "admission_date": None,
        "discharge_date": None,
        "diagnosis": []
    }

    # 患者IDの抽出（例：ID:12345 または 患者ID:12345 のようなパターン）
    id_match = re.search(r'(?:患者)?ID[：:]\s*(\w+)', text)
    if id_match:
        elements["patient_id"] = id_match.group(1)

    # 入院日の抽出（例：入院日:2023年5月1日 または 入院: 2023/5/1）
    admission_match = re.search(r'入院(?:日)?[：:]\s*(\d{4}[年/]\d{1,2}[月/]\d{1,2}日?)', text)
    if admission_match:
        elements["admission_date"] = admission_match.group(1)

    # 退院日の抽出
    discharge_match = re.search(r'退院(?:日)?[：:]\s*(\d{4}[年/]\d{1,2}[月/]\d{1,2}日?)', text)
    if discharge_match:
        elements["discharge_date"] = discharge_match.group(1)

    # 診断名の抽出（複数ある可能性）
    diagnosis_matches = re.finditer(r'(?:診断名|診断)[：:]\s*(.+?)(?:\n|$)', text)
    for match in diagnosis_matches:
        elements["diagnosis"].append(match.group(1).strip())

    return elements
