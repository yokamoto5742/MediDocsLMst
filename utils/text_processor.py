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

    # 当院の退院時サマリ構造に従ったフォーマット
    hospital_format = """# 退院時サマリ

## 入院期間
[入院期間]

## 現病歴
[入院日までの情報のみを記載]

## 入院時検査
[入院時の検査結果]

## 入院中の治療経過
### 投与薬剤
[入院中に投与された重要な薬剤]

### 手術情報
[手術日と術式のみ]

### 処置情報
[侵襲のある処置日と処置名のみ]

## 退院申し送り
### 退院時方針
[退院時方針]

### 退院時処方
[退院時処方]

## 禁忌/アレルギー
[禁忌/アレルギー情報]
"""

    # フォーマットタイプに基づく処理
    if format_type == "標準形式":
        # 当院フォーマットを標準として使用
        sections = {
            "入院期間": re.search(r'入院(?:日|期間)[：:]\s*(.*?)(?:\n|$)', formatted_text),
            "現病歴": re.search(r'現病歴[：:]\s*(.*?)(?:\n\n|$)', formatted_text, re.DOTALL),
            "入院時検査": re.search(r'検査[：:]\s*(.*?)(?:\n\n|$)', formatted_text, re.DOTALL),
            "投与薬剤": re.search(r'薬剤[：:]\s*(.*?)(?:\n\n|$)', formatted_text, re.DOTALL),
            "手術情報": re.search(r'手術[：:]\s*(.*?)(?:\n\n|$)', formatted_text, re.DOTALL),
            "処置情報": re.search(r'処置[：:]\s*(.*?)(?:\n\n|$)', formatted_text, re.DOTALL),
            "退院時方針": re.search(r'方針[：:]\s*(.*?)(?:\n\n|$)', formatted_text, re.DOTALL),
            "退院時処方": re.search(r'退院[時後]処方[：:]\s*(.*?)(?:\n\n|$)', formatted_text, re.DOTALL),
            "禁忌/アレルギー": re.search(r'(?:禁忌|アレルギー)[：:]\s*(.*?)(?:\n\n|$)', formatted_text, re.DOTALL)
        }

        result = "# 退院時サマリ\n\n"

        # 各セクションの内容を抽出して新しいフォーマットに適用
        result += "## 入院期間\n"
        result += sections["入院期間"].group(1) if sections["入院期間"] else "情報なし\n\n"

        result += "## 現病歴\n"
        result += sections["現病歴"].group(1) if sections["現病歴"] else "情報なし\n\n"

        result += "## 入院時検査\n"
        result += sections["入院時検査"].group(1) if sections["入院時検査"] else "情報なし\n\n"

        result += "## 入院中の治療経過\n"

        result += "### 投与薬剤\n"
        result += sections["投与薬剤"].group(1) if sections["投与薬剤"] else "情報なし\n\n"

        result += "### 手術情報\n"
        result += sections["手術情報"].group(1) if sections["手術情報"] else "情報なし\n\n"

        result += "### 処置情報\n"
        result += sections["処置情報"].group(1) if sections["処置情報"] else "情報なし\n\n"

        result += "## 退院申し送り\n"

        result += "### 退院時方針\n"
        result += sections["退院時方針"].group(1) if sections["退院時方針"] else "情報なし\n\n"

        result += "### 退院時処方\n"
        result += sections["退院時処方"].group(1) if sections["退院時処方"] else "情報なし\n\n"

        result += "## 禁忌/アレルギー\n"
        result += sections["禁忌/アレルギー"].group(1) if sections["禁忌/アレルギー"] else "情報なし"

        return result

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
