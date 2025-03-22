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
