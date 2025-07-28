# Google Sheets 自動同期設定ガイド

VET-Assistant3で生成したコンテンツを自動的にGoogleスプレッドシートに同期する機能の設定方法です。

## 1. Google Cloud Consoleでプロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成（例：`vet-assistant-sheets`）
3. プロジェクトを選択

## 2. Google Sheets APIの有効化

1. 左メニューから「APIとサービス」→「ライブラリ」を選択
2. 「Google Sheets API」を検索
3. 「Google Sheets API」を選択し、「有効にする」をクリック

## 3. サービスアカウントの作成

1. 左メニューから「APIとサービス」→「認証情報」を選択
2. 「認証情報を作成」→「サービスアカウント」を選択
3. サービスアカウント名を入力（例：`vet-assistant-sync`）
4. 「作成して続行」をクリック
5. ロールは「編集者」または「プロジェクト編集者」を選択
6. 「完了」をクリック

## 4. サービスアカウントキーの作成

1. 作成したサービスアカウントをクリック
2. 「キー」タブを選択
3. 「鍵を追加」→「新しい鍵を作成」を選択
4. キーのタイプで「JSON」を選択
5. 「作成」をクリック
6. JSONファイルがダウンロードされます

## 5. Googleスプレッドシートの作成と共有

1. [Google Sheets](https://sheets.google.com/)で新しいスプレッドシートを作成
2. スプレッドシート名を設定（例：`VET-Assistant投稿管理`）
3. URLの`/d/`以降`/edit`以前の部分（スプレッドシートID）をメモ
   - 例：`https://docs.google.com/spreadsheets/d/1ABC123DEF456/edit` → `1ABC123DEF456`
4. 「共有」ボタンをクリック
5. サービスアカウントのメールアドレス（JSONファイル内の`client_email`）を追加
6. 権限を「編集者」に設定

## 6. 環境変数の設定

`.env`ファイルに以下を設定：

```env
# Google Sheets 自動同期設定
# サービスアカウントJSONファイルのパス
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/your/service-account-key.json

# GoogleスプレッドシートのID
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
```

## 7. 動作確認

1. ターミナルでプロジェクトディレクトリに移動
2. 以下のコマンドで接続テスト：

```bash
python -c "from modules.google_sheets_sync import test_google_sheets_sync; test_google_sheets_sync()"
```

3. 「✅ Google Sheets API接続テスト成功」が表示されれば設定完了

## 8. コンテンツ生成での自動同期

設定完了後、以下のコマンドでコンテンツを生成すると自動的にGoogleスプレッドシートに同期されます：

```bash
python main.py generate
```

## スプレッドシート構造

自動的に作成される列：

### 投稿データシート
- `date`: 投稿日
- `day`: 曜日
- `animal_type`: 動物種（猫/犬）
- `theme`: テーマ
- `post_text`: 投稿文
- `character_count`: 文字数
- `scheduled_time`: 投稿予定時刻
- `投稿状況`: 投稿状態（未投稿/投稿済み/エラー）
- `投稿日時`: 実際の投稿日時
- `投稿URL`: X投稿のURL
- `エラー情報`: エラー内容
- `手動確認`: 要確認/確認済み
- `備考`: 備考欄

### 投稿スケジュールシート
- `投稿日`: 投稿予定日
- `曜日`: 曜日
- `時刻`: 投稿時刻
- `動物種`: 猫/犬
- `テーマ`: 投稿テーマ
- `文字数`: 投稿文字数
- `投稿文(冒頭50文字)`: 投稿文の冒頭部分

## トラブルシューティング

### 認証エラーが発生する場合
1. サービスアカウントのJSONファイルのパスが正しいか確認
2. スプレッドシートがサービスアカウントと共有されているか確認
3. Google Sheets APIが有効になっているか確認

### 同期が実行されない場合
1. `.env`ファイルの設定を確認
2. インターネット接続を確認
3. スプレッドシートIDが正しいか確認

### 手動で同期を無効にしたい場合
CSVExporterのインスタンス作成時に`enable_google_sheets=False`を指定：

```python
from modules.csv_exporter import CSVExporter
exporter = CSVExporter(enable_google_sheets=False)
```

## 将来的なX投稿自動化について

このスプレッドシート構造は、将来的にX（Twitter）APIを使った自動投稿に対応しています：

1. 「投稿状況」列で投稿管理
2. 「手動確認」列で投稿前の最終チェック
3. 「投稿日時」「投稿URL」で投稿履歴管理
4. 「エラー情報」で失敗した投稿の追跡

スプレッドシートから直接X投稿を管理する機能は、X API v2の利用規約に従って今後実装予定です。