import os
from pathlib import Path
from dotenv import load_dotenv

def load_environment_variables():
    """環境変数を.envファイルから読み込む"""
    # .envファイルのパスを取得（現在のファイルの親ディレクトリの親ディレクトリ）
    base_dir = Path(__file__).parent.parent
    env_path = os.path.join(base_dir, '.env')
    
    # .envファイルが存在する場合、環境変数を読み込む
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("環境変数を.envファイルから読み込みました")
    else:
        print("警告: .envファイルが見つかりません。環境変数は既に設定されているか、config.iniから読み込まれます。")
