# 実装計画書

## 実装順序

### Phase 1: 基盤構築
1. **プロジェクト構造作成**
   - ディレクトリ構成
   - 基本ファイル作成
   - 依存関係設定

2. **データベース設計・実装**
   - SQLite データベース作成
   - テーブル定義
   - 初期化スクリプト

3. **設定管理**
   - 環境変数管理
   - 設定ファイル作成

### Phase 2: API連携
4. **Zoom API 実装**
   - 認証処理
   - 会議作成機能
   - エラーハンドリング

5. **Google Calendar API 実装**
   - 認証処理
   - イベント作成機能
   - エラーハンドリング

6. **LINE Bot 実装**
   - Webhook 処理
   - メッセージ処理
   - 対話フロー実装

### Phase 3: 統合・テスト
7. **メインアプリケーション統合**
   - 各サービス連携
   - エラーハンドリング
   - ログ機能

8. **テスト・デバッグ**
   - 単体テスト
   - 統合テスト
   - エラー修正

### Phase 4: デプロイ
9. **Railway デプロイ準備**
   - Dockerfile 作成
   - Railway 設定
   - 環境変数設定

10. **本番デプロイ**
    - Railway デプロイ
    - Webhook URL 設定
    - 動作確認

## 詳細実装仕様

### 1. プロジェクト構造

```
zoom-meeting-bot/
├── app.py                    # メインアプリケーション
├── requirements.txt          # 依存関係
├── config.py                # 設定管理
├── .env                     # 環境変数（開発用）
├── .gitignore               # Git除外設定
├── database/
│   ├── __init__.py
│   ├── models.py            # データベースモデル
│   └── init_db.py           # データベース初期化
├── services/
│   ├── __init__.py
│   ├── line_bot.py          # LINE Bot 処理
│   ├── zoom_api.py          # Zoom API 処理
│   └── google_calendar.py   # Google Calendar 処理
├── utils/
│   ├── __init__.py
│   └── helpers.py           # ヘルパー関数
├── tests/
│   ├── __init__.py
│   ├── test_zoom_api.py
│   ├── test_google_calendar.py
│   └── test_line_bot.py
├── Dockerfile               # Railway デプロイ用
├── railway.json             # Railway 設定
└── README.md
```

### 2. データベース設計

#### meetings テーブル
```sql
CREATE TABLE meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    line_user_id TEXT NOT NULL,           -- LINE ユーザーID
    meeting_id TEXT NOT NULL,             -- Zoom 会議ID
    meeting_password TEXT,                -- Zoom 会議パスワード
    meeting_url TEXT,                     -- Zoom 会議URL
    meeting_name TEXT NOT NULL,           -- 会議名
    start_time DATETIME NOT NULL,         -- 開始時間
    duration INTEGER NOT NULL,            -- 会議時間（分）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    google_event_id TEXT                  -- Google カレンダーイベントID
);
```

#### インデックス
```sql
CREATE INDEX idx_line_user_id ON meetings(line_user_id);
CREATE INDEX idx_start_time ON meetings(start_time);
```

### 3. LINE Bot 対話フロー詳細

#### 状態管理
```python
class ConversationState:
    WAITING_FOR_MEETING_NAME = "waiting_for_meeting_name"
    WAITING_FOR_DATE = "waiting_for_date"
    WAITING_FOR_TIME = "waiting_for_time"
    WAITING_FOR_DURATION = "waiting_for_duration"
    CONFIRMING = "confirming"
```

#### 対話フロー
1. **会議名入力**
   - プロンプト: "会議名を教えてください"
   - バリデーション: 空文字チェック

2. **日付入力**
   - プロンプト: "日付を教えてください（例：2024/01/15）"
   - バリデーション: 日付形式チェック、過去日チェック

3. **時間入力**
   - プロンプト: "開始時間を教えてください（例：14:00）"
   - バリデーション: 時間形式チェック

4. **会議時間入力**
   - プロンプト: "会議時間を教えてください（例：60分）"
   - バリデーション: 数値チェック、範囲チェック（1-480分）

5. **確認**
   - プロンプト: "以下の内容で会議を作成しますか？\n会議名: {name}\n日時: {date} {time}\n時間: {duration}分"
   - 選択肢: "はい" / "いいえ"

### 4. Zoom API 実装仕様

#### 認証
```python
def get_zoom_token():
    # JWT トークン生成
    payload = {
        "iss": ZOOM_API_KEY,
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, ZOOM_API_SECRET, algorithm="HS256")
    return token
```

#### 会議作成
```python
def create_meeting(meeting_data):
    # Zoom API 会議作成
    # パラメータ:
    # - topic: 会議名
    # - start_time: 開始時間
    # - duration: 会議時間
    # - password: パスワード（自動生成）
    # - settings: 会議設定
```

### 5. Google Calendar API 実装仕様

#### 認証
```python
def get_google_credentials():
    # サービスアカウント認証
    credentials = service_account.Credentials.from_service_account_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    return credentials
```

#### イベント作成
```python
def create_calendar_event(event_data):
    # Google Calendar API イベント作成
    # パラメータ:
    # - summary: 会議名
    # - start: 開始時間
    # - end: 終了時間
    # - description: Zoom URL + パスワード
    # - location: Zoom URL
```

### 6. エラーハンドリング

#### エラー分類
1. **認証エラー**
   - API キー無効
   - トークン期限切れ

2. **API制限エラー**
   - Zoom API 制限
   - Google API 制限

3. **ネットワークエラー**
   - 接続タイムアウト
   - サーバーエラー

4. **データエラー**
   - 無効な日時
   - データベースエラー

#### 対応策
```python
def handle_api_error(error):
    if isinstance(error, requests.exceptions.Timeout):
        return "タイムアウトが発生しました。しばらく待ってから再試行してください。"
    elif isinstance(error, requests.exceptions.ConnectionError):
        return "ネットワークエラーが発生しました。接続を確認してください。"
    else:
        return "エラーが発生しました。管理者にお問い合わせください。"
```

### 7. ログ機能

#### ログレベル
- **INFO**: 正常な処理
- **WARNING**: 警告（API制限等）
- **ERROR**: エラー（処理失敗）
- **DEBUG**: デバッグ情報

#### ログ出力
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 8. テスト仕様

#### 単体テスト
- Zoom API テスト
- Google Calendar API テスト
- LINE Bot テスト
- データベーステスト

#### 統合テスト
- 会議作成フロー全体
- エラーハンドリング
- パフォーマンステスト

### 9. デプロイ仕様

#### Railway 設定
```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "python app.py",
    "healthcheckPath": "/health"
  }
}
```

#### 環境変数
- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`
- `ZOOM_API_KEY`
- `ZOOM_API_SECRET`
- `GOOGLE_CREDENTIALS_JSON`

### 10. 監視・運用

#### ヘルスチェック
```python
@app.route('/health')
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}
```

#### メトリクス
- API 呼び出し回数
- エラー率
- レスポンス時間
- データベース接続状況

## 実装スケジュール

### Week 1: 基盤構築
- プロジェクト構造作成
- データベース設計・実装
- 設定管理実装

### Week 2: API連携
- Zoom API 実装
- Google Calendar API 実装
- LINE Bot 実装

### Week 3: 統合・テスト
- メインアプリケーション統合
- テスト実装
- デバッグ・修正

### Week 4: デプロイ・運用
- Railway デプロイ
- 本番環境テスト
- ドキュメント整備

## リスク管理

### 技術的リスク
- API制限による機能停止
- 認証エラー
- データベースエラー

### 対応策
- リトライ機能実装
- エラーログ記録
- バックアップ機能

### 運用リスク
- サーバー停止
- データ損失
- セキュリティ問題

### 対応策
- ヘルスチェック実装
- データベースバックアップ
- セキュリティ監査

