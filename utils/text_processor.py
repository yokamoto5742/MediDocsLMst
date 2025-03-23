def preprocess_text(text):
    """
    前処理を行わずにそのまま返す関数

    Args:
        text (str): 入力テキスト

    Returns:
        str: 同じテキスト
    """
    return text


def format_discharge_summary(summary_text):
    """
    サマリテキストの後処理を行う関数

    Args:
        summary_text (str): サマリテキスト

    Returns:
        str: 処理されたテキスト
    """
    # 半角および全角のアスタリスク（＊印）、シャープ(#)、スペースを削除
    processed_text = summary_text.replace('*', '').replace('＊', '').replace('#', '').replace(' ', '')

    return processed_text


def parse_discharge_summary(summary_text):
    """
    退院時サマリを項目ごとに分割する関数

    Args:
        summary_text (str): 退院時サマリのテキスト

    Returns:
        dict: 項目ごとに分割されたテキスト
    """
    # 初期化
    summary_dict = {
        "入院期間": "",
        "現病歴": "",
        "入院時検査": "",
        "入院中の治療経過": "",
        "退院申し送り": "",
        "禁忌/アレルギー": "",
    }

    # 行ごとに分割
    lines = summary_text.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 項目の判定
        if "入院期間" in line:
            current_section = "入院期間"
            # タイトル部分を除去（コロンも含めて除去）
            line = line.replace("入院期間", "").replace(":", "").strip()
        elif "現病歴" in line:
            current_section = "現病歴"
            line = line.replace("現病歴", "").replace(":", "").strip()
        elif "入院時検査" in line:
            current_section = "入院時検査"
            line = line.replace("入院時検査", "").replace(":", "").strip()
        elif "入院中の治療経過" in line:
            current_section = "入院中の治療経過"
            line = line.replace("入院中の治療経過", "").replace(":", "").strip()
        elif "退院申し送り" in line:
            current_section = "退院申し送り"
            line = line.replace("退院申し送り", "").replace(":", "").strip()
        elif "禁忌/アレルギー" in line or "禁忌・アレルギー" in line:
            current_section = "禁忌/アレルギー"
            line = line.replace("禁忌/アレルギー", "").replace("禁忌・アレルギー", "").replace(":", "").strip()

        # 現在のセクションにテキストを追加
        if current_section and line:
            if summary_dict[current_section]:
                summary_dict[current_section] += "\n" + line
            else:
                summary_dict[current_section] = line

    return summary_dict
