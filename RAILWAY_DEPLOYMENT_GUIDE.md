# Railway デプロイ手順ガイド

## 1. Railway アカウント作成・準備

### 1.1 Railway アカウント作成
1. [Railway](https://railway.app/) にアクセス
2. 「Sign up」をクリック
3. GitHub アカウントでログイン（推奨）

### 1.2 Railway CLI インストール
```bash
# npm を使用
npm install -g @railway/cli

# または yarn を使用
yarn global add @railway/cli
```

### 1.3 Railway ログイン
```bash
railway login
```

## 2. プロジェクト準備

### 2.1 プロジェクト構造
```
zoom-meeting-bot/
├── app.py                 # メインアプリケーション
├── requirements.txt       # 依存関係
├── config.py             # 設定管理
├── .env                  # 環境変数（開発用）
├── .gitignore            # Git除外設定
├── database/
│   ├── __init__.py
│   ├── models.py         # データベースモデル
│   └── init_db.py        # データベース初期化
├── services/
│   ├── __init__.py
│   ├── line_bot.py       # LINE Bot 処理
│   ├── zoom_api.py       # Zoom API 処理
│   └── google_calendar.py # Google Calendar 処理
├── utils/
│   ├── __init__.py
│   └── helpers.py        # ヘルパー関数
├── Dockerfile            # Railway デプロイ用
├── railway.json          # Railway 設定
└── README.md
```

### 2.2 必要なファイル作成

#### requirements.txt
```txt
Flask==2.3.3
line-bot-sdk==3.5.0
requests==2.31.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0
PyJWT==2.8.0
python-dotenv==1.0.0
```

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# ポート公開
EXPOSE 8000

# アプリケーション起動
CMD ["python", "app.py"]
```

#### railway.json
```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "python app.py",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

#### .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 環境変数
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# データベース
*.db
*.sqlite
*.sqlite3

# ログ
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# 認証情報
credentials.json
*.pem
*.key
```

## 3. Railway プロジェクト作成

### 3.1 プロジェクト初期化
```bash
# プロジェクトディレクトリで実行
railway init
```

### 3.2 プロジェクト設定
1. プロジェクト名を入力（例：「zoom-meeting-bot」）
2. リージョンを選択（推奨：US West）
3. 「Create Project」をクリック

## 4. 環境変数設定

### 4.1 Railway CLI で設定
```bash
# LINE Bot 設定
railway variables set LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
railway variables set LINE_CHANNEL_SECRET=your_line_channel_secret

# Zoom API 設定
railway variables set ZOOM_API_KEY=your_zoom_api_key
railway variables set ZOOM_API_SECRET=your_zoom_api_secret

# Google Calendar 設定
railway variables set GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
```

### 4.2 Railway ダッシュボードで設定
1. Railway ダッシュボードにアクセス
2. プロジェクトを選択
3. 「Variables」タブをクリック
4. 環境変数を追加

## 5. デプロイ実行

### 5.1 初回デプロイ
```bash
# デプロイ実行
railway up

# ログ確認
railway logs

# 環境変数確認
railway variables
```

### 5.2 デプロイ状況確認
```bash
# デプロイ状況確認
railway status

# ログのリアルタイム確認
railway logs --follow
```

## 6. Webhook URL 設定

### 6.1 Railway URL 取得
1. Railway ダッシュボードでプロジェクトを選択
2. 「Deployments」タブでURLを確認
3. URL形式：`https://your-app.railway.app`

### 6.2 LINE Bot Webhook 設定
1. [LINE Developers Console](https://developers.line.biz/) にアクセス
2. チャンネルを選択
3. 「Messaging API」タブをクリック
4. **Webhook URL** に設定：`https://your-app.railway.app/webhook`
5. 「Verify」をクリックして検証
6. 「Use webhook」を有効化

## 7. 動作確認

### 7.1 ヘルスチェック
```bash
# ヘルスチェックエンドポイント確認
curl https://your-app.railway.app/health
```

### 7.2 LINE Bot テスト
1. LINE アプリでBotを友達追加
2. 「会議作成」と送信
3. 対話フローが正常に動作するか確認

### 7.3 ログ確認
```bash
# リアルタイムログ確認
railway logs --follow

# 特定の時間のログ確認
railway logs --since 1h
```

## 8. 継続的デプロイ設定

### 8.1 GitHub 連携
1. Railway ダッシュボードでプロジェクトを選択
2. 「Settings」→「Git」をクリック
3. GitHub リポジトリを選択
4. ブランチを選択（通常は `main`）
5. 「Connect」をクリック

### 8.2 自動デプロイ設定
- プッシュ時に自動デプロイ
- プルリクエスト時にプレビューデプロイ
- 本番環境とステージング環境の分離

## 9. 監視・運用

### 9.1 ヘルスチェック実装
```python
@app.route('/health')
def health_check():
    try:
        # データベース接続確認
        conn = sqlite3.connect('meetings.db')
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }, 500
```

### 9.2 ログ管理
```python
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ログ出力例
logger.info("会議作成開始: %s", meeting_name)
logger.error("API エラー: %s", str(error))
```

### 9.3 エラー監視
- Railway ダッシュボードでエラーログ確認
- アラート設定（Slack、メール通知）
- パフォーマンス監視

## 10. トラブルシューティング

### 10.1 デプロイエラー
```bash
# デプロイログ確認
railway logs --deployment your-deployment-id

# ローカルでテスト
python app.py
```

### 10.2 環境変数エラー
```bash
# 環境変数確認
railway variables

# 環境変数設定
railway variables set KEY=value
```

### 10.3 データベースエラー
```bash
# データベース接続確認
railway connect

# データベース初期化
python database/init_db.py
```

## 11. セキュリティ設定

### 11.1 環境変数の暗号化
- 機密情報は環境変数で管理
- 本番環境では暗号化して保存
- 定期的な認証情報の更新

### 11.2 アクセス制御
- Railway プロジェクトのアクセス権限設定
- 本番環境へのアクセス制限
- ログの適切な管理

## 12. バックアップ・復旧

### 12.1 データベースバックアップ
```bash
# データベースダウンロード
railway connect
sqlite3 meetings.db ".backup backup.db"
```

### 12.2 設定のバックアップ
- 環境変数の記録
- 設定ファイルのバージョン管理
- デプロイ設定の文書化

## 13. パフォーマンス最適化

### 13.1 リソース設定
- Railway ダッシュボードでリソース設定
- CPU・メモリ使用量の監視
- 必要に応じたスケーリング

### 13.2 データベース最適化
- インデックスの設定
- クエリの最適化
- 接続プールの設定

## 14. 次のステップ

デプロイが完了したら、以下の作業を行います：

1. **本番環境テスト**
2. **パフォーマンス監視**
3. **セキュリティ監査**
4. **ドキュメント整備**
5. **運用マニュアル作成**

各手順の詳細は `IMPLEMENTATION_PLAN.md` を参照してください。

