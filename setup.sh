mkdir -p ~/.streamlit/

echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
enableXsrfProtection=false\n\
port = $PORT\n\
" > ~/.streamlit/config.toml

# Herokuの環境変数を確認してデバッグログに出力
echo "環境変数のデバッグ開始..."
env | grep -i forward
env | grep -i remote
env | grep -i http

# HerokuでクライアントのリアルIPを取得するための環境変数を設定
# Heroku特有の環境変数からIPアドレス情報を取得
if [ -n "$HTTP_X_FORWARDED_FOR" ]; then
  export X_FORWARDED_FOR="$HTTP_X_FORWARDED_FOR"
  echo "X_FORWARDED_FORを設定: $X_FORWARDED_FOR"
fi