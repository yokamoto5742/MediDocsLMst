def preprocess_text(text):
    """
    前処理を行わずにそのまま返す関数

    Args:
        text (str): 入力テキスト

    Returns:
        str: 同じテキスト
    """
    return text


def format_discharge_summary(summary_text, format_type=None):
    """
    後処理を行わずにそのまま返す関数

    Args:
        summary_text (str): サマリテキスト
        format_type (str): 不使用

    Returns:
        str: 同じテキスト
    """
    return summary_text