# API認証情報取得手順ガイド

## 1. LINE Bot API 設定

### 1.1 LINE Developers Console アクセス
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

## 2. Zoom API 設定

### 2.1 Zoom Marketplace アクセス
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

## 3. Google Calendar API 設定

### 3.1 Google Cloud Console アクセス
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

## 4. 環境変数設定

### 4.1 ローカル開発用
`.env` ファイルを作成：
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

### 4.2 Railway デプロイ用
```bash
# Railway CLI で環境変数設定
railway variables set LINE_CHANNEL_ACCESS_TOKEN=your_token
railway variables set LINE_CHANNEL_SECRET=your_secret
railway variables set ZOOM_API_KEY=your_zoom_key
railway variables set ZOOM_API_SECRET=your_zoom_secret
railway variables set GOOGLE_CREDENTIALS_JSON=your_google_credentials
```

## 5. 認証情報の確認

### 5.1 LINE Bot テスト
```python
import requests

# プロフィール取得テスト
headers = {
    'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
}
response = requests.get('https://api.line.me/v2/bot/profile/U1234567890', headers=headers)
print(response.json())
```

### 5.2 Zoom API テスト
```python
import jwt
import requests

# JWT トークン生成
payload = {
    "iss": ZOOM_API_KEY,
    "exp": int(time.time()) + 3600
}
token = jwt.encode(payload, ZOOM_API_SECRET, algorithm="HS256")

# ユーザー情報取得テスト
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}
response = requests.get('https://api.zoom.us/v2/users/me', headers=headers)
print(response.json())
```

### 5.3 Google Calendar API テスト
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 認証情報読み込み
credentials = service_account.Credentials.from_service_account_file(
    'credentials.json',
    scopes=['https://www.googleapis.com/auth/calendar']
)

# カレンダー一覧取得テスト
service = build('calendar', 'v3', credentials=credentials)
calendar_list = service.calendarList().list().execute()
print(calendar_list)
```

## 6. セキュリティ注意事項

### 6.1 認証情報の管理
- 認証情報は絶対にコードに直接記述しない
- 環境変数または設定ファイルで管理
- 本番環境では暗号化して保存

### 6.2 権限の最小化
- 必要最小限の権限のみ付与
- 定期的な権限見直し
- 不要な権限は削除

### 6.3 ログ管理
- 認証情報はログに出力しない
- エラーログは適切に管理
- 定期的なログローテーション

## 7. トラブルシューティング

### 7.1 LINE Bot エラー
- **401 Unauthorized**: アクセストークンが無効
- **403 Forbidden**: 権限が不足
- **Webhook エラー**: URLが正しく設定されていない

### 7.2 Zoom API エラー
- **401 Unauthorized**: JWT トークンが無効
- **403 Forbidden**: 権限が不足
- **429 Too Many Requests**: API制限に達した

### 7.3 Google Calendar API エラー
- **401 Unauthorized**: 認証情報が無効
- **403 Forbidden**: カレンダーへのアクセス権限が不足
- **404 Not Found**: カレンダーが存在しない

## 8. 次のステップ

認証情報の取得が完了したら、以下の手順で実装を進めます：

1. **プロジェクト構造作成**
2. **データベース実装**
3. **各API連携実装**
4. **LINE Bot 実装**
5. **統合テスト**
6. **Railway デプロイ**

各手順の詳細は `IMPLEMENTATION_PLAN.md` を参照してください。

