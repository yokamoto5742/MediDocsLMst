import os
from pathlib import Path

from dotenv import load_dotenv


def load_environment_variables():
    mongodb_uri = os.environ.get("MONGODB_URI")

    if mongodb_uri:
        print("システム環境変数が検出されました。")
        return

    base_dir = Path(__file__).parent.parent
    env_path = os.path.join(base_dir, '.env')

    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("環境変数を.envファイルから読み込みました")
    else:
        print("警告: .envファイルが見つかりません。システム環境変数が設定されていることを確認してください。")
