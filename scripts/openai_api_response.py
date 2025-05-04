import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


def load_environment_variables():
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if openai_api_key:
        print("システム環境変数からAPIキーを読み込みました")
        return

    base_dir = Path(__file__).parent
    env_path = os.path.join(base_dir, '.env')

    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(".envファイルから環境変数を読み込みました")
    else:
        print("警告: .envファイルが見つかりません。")

def test_openai_api_key():
    load_environment_variables()

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("❌ OPENAI_API_KEYが環境変数に設定されていません")
        return False

    if len(api_key) > 5:
        key_preview = f"{api_key[:3]}...{api_key[-3:]}"
        print(f"ℹ️ APIキー: {key_preview} (セキュリティのため一部のみ表示)")
    else:
        print("❌ APIキーの形式が不正です")
        return False

    try:
        client = OpenAI(api_key=api_key)

        print("🔄 OpenAI APIに接続しています...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "短く返答してください。"},
                {"role": "user", "content": "こんにちは"}
            ],
            max_tokens=5
        )

        if response.choices and response.choices[0].message.content:
            print("✅ APIキーは正常に動作しています")
            print(f"📝 応答: {response.choices[0].message.content}")
            print(f"🔢 使用トークン数: 入力={response.usage.prompt_tokens}, 出力={response.usage.completion_tokens}")
            return True
        else:
            print("❌ APIからの応答はありますが、内容が空です")
            return False

    except Exception as e:
        print(f"❌ APIキーテストエラー: {str(e)}")
        return False


if __name__ == "__main__":
    test_openai_api_key()
