# セットアップ手順書

## 1. LINE Bot API の設定

### 1.1 LINE Developers Console にアクセス
1. [LINE Developers Console](https://developers.line.biz/) にアクセス
2. LINE アカウントでログイン

### 1.2 プロバイダー作成
1. 「Create」ボタンをクリック
2. プロバイダー名を入力（例：「会議管理Bot」）
3. 「Create」をクリック

### 1.3 チャンネル作成
1. 「Create a new channel」をクリック
2. 「Messaging API」を選択
3. チャンネル情報を入力：
   - **Channel name**: 会議管理Bot
   - **Channel description**: Zoom会議作成Bot
   - **Category**: Tools
   - **Subcategory**: Other
4. 「Create」をクリック

### 1.4 認証情報取得
1. 「Basic settings」タブで以下を取得：
   - **Channel access token**: アクセストークン
   - **Channel secret**: シークレットキー

### 1.5 Webhook設定
1. 「Messaging API」タブに移動
2. 「Use webhook」を有効化
3. **Webhook URL**: `https://your-app.railway.app/webhook`（後で設定）
4. **Webhook events**: 「Message」を選択

## 2. Zoom API の設定

### 2.1 Zoom Marketplace にアクセス
1. [Zoom Marketplace](https://marketplace.zoom.us/) にアクセス
2. Zoom アカウントでログイン

### 2.2 アプリケーション作成
1. 「Develop」→「Build App」をクリック
2. 「JWT」を選択
3. アプリ情報を入力：
   - **App name**: 会議管理システム
   - **Short description**: LINE Bot連携会議作成システム
   - **Company name**: あなたの会社名
   - **Developer contact information**: 連絡先情報

### 2.3 アプリ設定
1. 「App Credentials」で以下を取得：
   - **API Key**: アプリケーションキー
   - **API Secret**: シークレットキー

### 2.4 権限設定
1. 「Scopes」タブで以下を有効化：
   - **Meeting**: Write
   - **User**: Read

### 2.5 アプリ公開
1. 「Activation」タブで「Activate your app」をクリック
2. アプリを有効化

## 3. Google Calendar API の設定

### 3.1 Google Cloud Console にアクセス
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. Google アカウントでログイン

### 3.2 プロジェクト作成
1. 「プロジェクトを選択」→「新しいプロジェクト」をクリック
2. プロジェクト名を入力（例：「会議管理システム」）
3. 「作成」をクリック

### 3.3 API有効化
1. 「APIとサービス」→「ライブラリ」をクリック
2. 「Google Calendar API」を検索
3. 「有効にする」をクリック

### 3.4 サービスアカウント作成
1. 「APIとサービス」→「認証情報」をクリック
2. 「認証情報を作成」→「サービスアカウント」を選択
3. サービスアカウント情報を入力：
   - **サービスアカウント名**: 会議管理システム
   - **サービスアカウントID**: meeting-management-system
   - **説明**: LINE Bot連携会議作成システム

### 3.5 認証情報作成
1. サービスアカウント作成後、「キー」タブをクリック
2. 「キーを追加」→「新しいキーを作成」を選択
3. 「JSON」を選択して「作成」をクリック
4. ダウンロードされたJSONファイルを保存

### 3.6 カレンダー共有設定
1. Googleカレンダーにアクセス
2. 対象カレンダーの「設定と共有」をクリック
3. 「特定のユーザーと共有」でサービスアカウントのメールアドレスを追加
4. 権限を「変更イベントの管理」に設定

## 4. 環境変数の設定

### 4.1 .env ファイル作成
プロジェクトルートに `.env` ファイルを作成し、以下の内容を記入：

```bash
# LINE Bot
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# Zoom API
ZOOM_API_KEY=your_zoom_api_key
ZOOM_API_SECRET=your_zoom_api_secret

# Google Calendar
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
```

### 4.2 認証情報の確認
各APIの認証情報が正しく設定されているか確認：

```bash
python -c "
from config import Config
print('LINE_CHANNEL_ACCESS_TOKEN:', '設定済み' if Config.LINE_CHANNEL_ACCESS_TOKEN else '未設定')
print('LINE_CHANNEL_SECRET:', '設定済み' if Config.LINE_CHANNEL_SECRET else '未設定')
print('ZOOM_API_KEY:', '設定済み' if Config.ZOOM_API_KEY else '未設定')
print('ZOOM_API_SECRET:', '設定済み' if Config.ZOOM_API_SECRET else '未設定')
print('GOOGLE_CREDENTIALS_JSON:', '設定済み' if Config.GOOGLE_CREDENTIALS_JSON else '未設定')
"
```

## 5. ローカルテスト

### 5.1 アプリケーション起動
```bash
python app.py
```

### 5.2 ngrok でWebhook設定
```bash
# ngrok インストール（未インストールの場合）
# https://ngrok.com/download

# ngrok 起動
ngrok http 8000
```

### 5.3 LINE Bot Webhook設定
1. LINE Developers Console でWebhook URL設定
2. URL: `https://your-ngrok-url.ngrok.io/webhook`
3. 「Verify」で検証

## 6. Railway デプロイ

### 6.1 Railway CLI インストール
```bash
npm install -g @railway/cli
```

### 6.2 Railway ログイン・初期化
```bash
railway login
railway init
```

### 6.3 環境変数設定
```bash
railway variables set LINE_CHANNEL_ACCESS_TOKEN=your_token
railway variables set LINE_CHANNEL_SECRET=your_secret
railway variables set ZOOM_API_KEY=your_zoom_key
railway variables set ZOOM_API_SECRET=your_zoom_secret
railway variables set GOOGLE_CREDENTIALS_JSON=your_google_credentials
```

### 6.4 デプロイ実行
```bash
railway up
```

### 6.5 Webhook URL 設定
1. Railway ダッシュボードでURLを取得
2. LINE Bot のWebhook URLに設定: `https://your-app.railway.app/webhook`

## 7. 動作確認

### 7.1 ヘルスチェック
```bash
curl https://your-app.railway.app/health
```

### 7.2 LINE Bot テスト
1. LINE アプリでBotを友達追加
2. 「会議作成」と送信
3. 対話フローが正常に動作するか確認

## トラブルシューティング

### よくあるエラー
1. **認証エラー**: 環境変数が正しく設定されているか確認
2. **Webhook エラー**: URLが正しく設定されているか確認
3. **データベースエラー**: ファイル権限を確認

### ログ確認
```bash
# ローカル
python app.py

# Railway
railway logs --follow
```

## 完了！

これで Zoom API + Google Calendar + LINE Bot 会議管理システムが完全に動作します！

### 主な機能
- LINE Bot による対話形式での会議作成
- Zoom API による会議ID、パスワード、リンク生成
- Googleカレンダーへの自動追加
- SQLite によるデータ管理
- Railway によるデプロイ

