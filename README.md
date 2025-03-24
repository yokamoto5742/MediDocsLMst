# 退院時サマリ作成アプリ

## 概要
このアプリケーションは、医療機関における退院時サマリを効率的に作成するためのWebツールです。Google Gemini AIを活用して、カルテ情報から構造化された退院時サマリを自動生成します。Streamlitベースのインターフェースで、医療従事者が簡単に利用できます。

## 主な機能
- 📝 カルテ情報から退院時サマリの自動生成
- 🔍 生成されたサマリの項目別表示（入院期間、現病歴、検査結果など）
- 🔐 ユーザー認証システム（ログイン、新規登録、パスワード変更）
- 👥 管理者権限の設定（最初のユーザーに自動付与）
- 🌐 Webブラウザからのアクセス

## インストール手順

### 前提条件
- Python 3.11以上
- MongoDB アカウント
- Google Gemini API キー

### セットアップ
1. リポジトリをクローン
   ```bash
   git clone https://github.com/yourusername/discharge-summary-app.git
   cd discharge-summary-app
   ```

2. 仮想環境を作成して有効化（推奨）
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. 必要なパッケージをインストール
   ```bash
   pip install -r requirements.txt
   ```

4. `.env`ファイルを作成して環境変数を設定
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   MONGODB_DB_NAME=discharge_summary_app
   MONGODB_USERS_COLLECTION=users
   GEMINI_CREDENTIALS=your_gemini_api_key
   ```

## 使用方法

### アプリの起動
```bash
streamlit run app.py
```

### 初回利用時
1. 新規ユーザー登録（最初のユーザーには管理者権限が自動付与されます）
2. ログイン
3. カルテ情報をテキストエリアに貼り付け
4. 「退院時サマリ作成」ボタンをクリック
5. 生成されたサマリを確認（全文または項目別に表示）

## 設定
`config.ini`ファイルで以下の設定が可能です：

```ini
[AUTH]
require_login = true/false  # ログイン要否の設定

[GEMINI]
model = gemini-2.0-pro-exp-02-05  # 使用するGeminiモデル

[PROMPTS]
discharge_summary = プロンプトテンプレート  # AIへの指示テンプレート
```

## ファイル構造
- `app.py` - メインアプリケーション（Streamlit UI）
- `config.ini` - アプリケーション設定
- `requirements.txt` - 依存パッケージリスト
- `utils/` - ユーティリティモジュール
  - `auth.py` - 認証関連機能
  - `config.py` - 設定読み込み
  - `env_loader.py` - 環境変数読み込み
  - `gemini_api.py` - Gemini API連携
  - `text_processor.py` - テキスト処理機能

## 技術スタック
- **フロントエンド**: Streamlit
- **バックエンド**: Python
- **データベース**: MongoDB Atlas
- **AI**: Google Gemini
- **認証**: bcrypt（パスワードハッシュ化）

## 環境変数
アプリケーションには以下の環境変数が必要です：

| 環境変数 | 説明 | 必須 |
|----------|------|------|
| MONGODB_URI | MongoDB接続URI | はい |
| MONGODB_DB_NAME | データベース名 | いいえ（デフォルト: discharge_summary_app） |
| MONGODB_USERS_COLLECTION | ユーザーコレクション名 | いいえ（デフォルト: users） |
| GEMINI_CREDENTIALS | Gemini APIキー | はい |

## セキュリティ情報
- ユーザーパスワードはbcryptでハッシュ化されています
- 入力および出力テキストはデータベースに保存されません
- 環境変数で機密情報を管理しています

## トラブルシューティング
- MongoDB接続エラー: MONGODB_URI環境変数が正しく設定されているか確認してください
- Gemini API認証エラー: GEMINI_CREDENTIALS環境変数が正しく設定されているか確認してください
- パッケージのインストールエラー: Python環境が正しく設定されているか確認してください
