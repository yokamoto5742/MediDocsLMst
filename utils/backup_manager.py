import os
import json
import datetime
from pathlib import Path
from utils.config import get_mongodb_connection
from utils.prompt_manager import get_prompt_collection, get_all_prompts, get_department_collection, get_all_departments


def backup_prompts(backup_dir=None):
    """
    データベースに保存されているプロンプトをJSONファイルにバックアップする関数

    Args:
        backup_dir (str, optional): バックアップファイルを保存するディレクトリ
            指定がない場合はプロジェクトルートの下に 'backups/prompts' ディレクトリを作成

    Returns:
        str: バックアップファイルのパス
    """
    # バックアップディレクトリの設定
    if backup_dir is None:
        # プロジェクトルートディレクトリを取得
        root_dir = Path(__file__).parent.parent
        backup_dir = os.path.join(root_dir, 'backups', 'prompts')

    # バックアップディレクトリが存在しない場合は作成
    os.makedirs(backup_dir, exist_ok=True)

    # タイムスタンプをファイル名に含める
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prompts_backup_{timestamp}.json"
    backup_path = os.path.join(backup_dir, filename)

    # プロンプトデータを取得
    prompt_collection = get_prompt_collection()
    prompts = list(prompt_collection.find({}, {'_id': False}))  # _idフィールドは除外

    # データをJSONファイルに書き込む
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2, default=str)

    print(f"プロンプトのバックアップが完了しました: {backup_path}")
    return backup_path


def backup_departments(backup_dir=None):
    """
    データベースに保存されている診療科をJSONファイルにバックアップする関数

    Args:
        backup_dir (str, optional): バックアップファイルを保存するディレクトリ

    Returns:
        str: バックアップファイルのパス
    """
    # バックアップディレクトリの設定
    if backup_dir is None:
        root_dir = Path(__file__).parent.parent
        backup_dir = os.path.join(root_dir, 'backups', 'departments')

    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"departments_backup_{timestamp}.json"
    backup_path = os.path.join(backup_dir, filename)

    # 診療科データを取得
    department_collection = get_department_collection()
    departments = list(department_collection.find({}, {'_id': False}))

    # データをJSONファイルに書き込む
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(departments, f, ensure_ascii=False, indent=2, default=str)

    print(f"診療科のバックアップが完了しました: {backup_path}")
    return backup_path


def restore_prompts(backup_file):
    """
    バックアップファイルからプロンプトを復元する関数

    Args:
        backup_file (str): バックアップJSONファイルのパス

    Returns:
        bool: 復元が成功したかどうか
    """
    if not os.path.exists(backup_file):
        print(f"エラー: バックアップファイルが見つかりません: {backup_file}")
        return False

    try:
        # バックアップデータを読み込む
        with open(backup_file, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)

        prompt_collection = get_prompt_collection()

        # 既存のプロンプトをすべて削除（オプション）
        # 注意: この操作は取り消せません
        if input("既存のプロンプトをすべて削除しますか？ (y/n): ").lower() == 'y':
            prompt_collection.delete_many({})
            print("既存のプロンプトをすべて削除しました")

        # バックアップデータを挿入
        for prompt in prompts_data:
            # created_at と updated_at を日付オブジェクトに変換
            if 'created_at' in prompt and isinstance(prompt['created_at'], str):
                prompt['created_at'] = datetime.datetime.fromisoformat(prompt['created_at'].replace('Z', '+00:00'))
            if 'updated_at' in prompt and isinstance(prompt['updated_at'], str):
                prompt['updated_at'] = datetime.datetime.fromisoformat(prompt['updated_at'].replace('Z', '+00:00'))

            # department をキーにして既存のプロンプトを検索
            existing = prompt_collection.find_one({"department": prompt["department"]})

            if existing:
                # 既存のプロンプトを更新
                prompt_collection.update_one(
                    {"department": prompt["department"]},
                    {"$set": prompt}
                )
            else:
                # 新規プロンプトを挿入
                prompt_collection.insert_one(prompt)

        print(f"{len(prompts_data)}件のプロンプトを正常に復元しました")
        return True

    except Exception as e:
        print(f"プロンプト復元中にエラーが発生しました: {str(e)}")
        return False


def restore_departments(backup_file):
    """
    バックアップファイルから診療科を復元する関数

    Args:
        backup_file (str): バックアップJSONファイルのパス

    Returns:
        bool: 復元が成功したかどうか
    """
    if not os.path.exists(backup_file):
        print(f"エラー: バックアップファイルが見つかりません: {backup_file}")
        return False

    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            departments_data = json.load(f)

        department_collection = get_department_collection()

        if input("既存の診療科をすべて削除しますか？ (y/n): ").lower() == 'y':
            department_collection.delete_many({})
            print("既存の診療科をすべて削除しました")

        for dept in departments_data:
            # 日付形式の変換
            if 'created_at' in dept and isinstance(dept['created_at'], str):
                dept['created_at'] = datetime.datetime.fromisoformat(dept['created_at'].replace('Z', '+00:00'))
            if 'updated_at' in dept and isinstance(dept['updated_at'], str):
                dept['updated_at'] = datetime.datetime.fromisoformat(dept['updated_at'].replace('Z', '+00:00'))

            existing = department_collection.find_one({"name": dept["name"]})

            if existing:
                department_collection.update_one(
                    {"name": dept["name"]},
                    {"$set": dept}
                )
            else:
                department_collection.insert_one(dept)

        print(f"{len(departments_data)}件の診療科を正常に復元しました")
        return True

    except Exception as e:
        print(f"診療科復元中にエラーが発生しました: {str(e)}")
        return False


def list_backup_files():
    """
    バックアップファイルの一覧を表示する関数
    """
    root_dir = Path(__file__).parent.parent
    prompts_dir = os.path.join(root_dir, 'backups', 'prompts')
    departments_dir = os.path.join(root_dir, 'backups', 'departments')

    print("\n=== プロンプトバックアップファイル ===")
    if os.path.exists(prompts_dir):
        files = os.listdir(prompts_dir)
        if files:
            for idx, file in enumerate(sorted(files, reverse=True)):
                full_path = os.path.join(prompts_dir, file)
                size = os.path.getsize(full_path) // 1024  # KB単位
                mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                print(f"{idx + 1}. {file} ({size}KB) - {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("バックアップファイルが見つかりません")
    else:
        print("バックアップディレクトリが見つかりません")

    print("\n=== 診療科バックアップファイル ===")
    if os.path.exists(departments_dir):
        files = os.listdir(departments_dir)
        if files:
            for idx, file in enumerate(sorted(files, reverse=True)):
                full_path = os.path.join(departments_dir, file)
                size = os.path.getsize(full_path) // 1024  # KB単位
                mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                print(f"{idx + 1}. {file} ({size}KB) - {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("バックアップファイルが見つかりません")
    else:
        print("バックアップディレクトリが見つかりません")


if __name__ == "__main__":
    # スクリプト単体で実行した場合のメイン処理
    print("データベースバックアップユーティリティ")
    print("1. バックアップの作成")
    print("2. バックアップの復元")
    print("3. バックアップファイルの一覧表示")
    print("0. 終了")

    action = input("操作を選択してください: ")

    if action == "1":
        print("バックアップを作成します...")
        prompt_file = backup_prompts()
        dept_file = backup_departments()
        print(f"\nバックアップが完了しました。")
        print(f"プロンプト: {prompt_file}")
        print(f"診療科: {dept_file}")

    elif action == "2":
        # バックアップファイルの一覧を表示
        list_backup_files()

        print("\n--- プロンプトの復元 ---")
        prompt_file = input("プロンプトバックアップファイルのパスを入力: ")
        if prompt_file:
            restore_prompts(prompt_file)

        print("\n--- 診療科の復元 ---")
        dept_file = input("診療科バックアップファイルのパスを入力: ")
        if dept_file:
            restore_departments(dept_file)

    elif action == "3":
        list_backup_files()

    elif action == "0":
        print("プログラムを終了します。")
    else:
        print("無効な選択です。")
