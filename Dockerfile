FROM python:3.9-slim

WORKDIR /app

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# アプリケーション起動
CMD ["python", "app.py"]

