import os
from pathlib import Path
from dotenv import load_dotenv


def load_environment_variables():
    """
    環境変数を読み込む関数
    1. システム環境変数が設定されている場合はそれを優先
    2. .envファイルが存在する場合はそこから読み込む
    """
    # システム環境変数の存在確認
    mongodb_uri = os.environ.get("MONGODB_URI")

    # システム環境変数がすでに設定されている場合（Heroku環境など）
    if mongodb_uri:
        print("システム環境変数が検出されました。.envファイルの読み込みはスキップします。")
        return

    # .envファイルのパスを取得（現在のファイルの親ディレクトリの親ディレクトリ）
    base_dir = Path(__file__).parent.parent
    env_path = os.path.join(base_dir, '.env')

    # .envファイルが存在する場合、環境変数を読み込む
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("環境変数を.envファイルから読み込みました")
    else:
        print("警告: .envファイルが見つかりません。システム環境変数が設定されていることを確認してください。")
