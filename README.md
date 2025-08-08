# VET-Assistant3

獣医師の専門知識を活用したコンテンツ生成システム

## 概要

VET-Assistant3は、獣医師の先生の専門知識とコンテンツ戦略をAIが実行し、高品質な投稿コンテンツを「分析→生成→出力」で自動化するシステムです。

## 主な機能

- **猫投稿コンテンツ生成**: 125-140字以内、#猫のあれこれ
- **犬投稿コンテンツ生成**: 125-135字以内、#獣医が教える犬のはなし
- **動的コンテンツ計画**: 過去3ヶ月の投稿分析に基づく重複回避
- **過去投稿データ分析**: tweets.jsファイルからの投稿履歴分析
- **CSV出力機能**: 1週間分の投稿案一括生成
- **週間コンテンツ生成**: 定期的な週間コンテンツ自動生成

# Security review test

## ディレクトリ構成

```
VET-Assistant3/
├── modules/
│   ├── data_manager.py      # データ管理（tweets.js読み書き）
│   ├── content_generator.py # コンテンツ生成
│   ├── twitter_poster.py    # Twitter API連携
│   └── csv_exporter.py     # CSV出力機能
├── config/
│   └── .env.example        # 環境変数テンプレート
├── 出力/                   # CSV出力フォルダ
├── scheduler.py            # メインスケジューラー
├── requirements.txt        # 依存パッケージ
└── README.md              # このファイル
```

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`config/.env.example`を`.env`にコピーして編集:

```bash
cp config/.env.example .env
```

### 3. APIキーの設定

`.env`ファイルに以下のAPIキーを設定:

- OpenAI API Key
- Twitter API Keys (API Key, API Secret, Access Token, Access Token Secret, Bearer Token)

### 4. tweets.jsファイルの配置

Twitterのデータダウンロードからtweets.jsファイルを取得し、指定パスに配置してください。

## 使用方法

### 基本的な使用方法

```bash
# スケジューラーを開始（デフォルト）
python scheduler.py

# 手動テスト投稿
python scheduler.py test

# 週間コンテンツ生成のみ
python scheduler.py generate

# スケジュール実行
python scheduler.py schedule
```

### モジュール単体テスト

```bash
# データ管理のテスト
python modules/data_manager.py

# コンテンツ生成のテスト
python modules/content_generator.py

# Twitter投稿のテスト
python modules/twitter_poster.py

# CSV出力のテスト
python modules/csv_exporter.py
```

## 投稿スケジュール

- **猫の投稿**: 毎日 07:00
- **犬の投稿**: 毎日 18:00
- **週間コンテンツ生成**: 毎週日曜日 20:00

## 犬投稿の週間構成

- **月曜**: クイズ・質問編
- **火曜**: 回答・解説編
- **水曜**: ケーススタディ・質問編
- **木曜**: 回答・解説編
- **金曜**: 体験談募集・質問募集
- **土曜**: お役立ちヒント・小ワザ
- **日曜**: 豆知識・コラム

## 出力ファイル

- `YYYY-MM-DD_posts.csv`: 週間投稿データ
- `YYYY-MM-DD_schedule.csv`: 投稿スケジュール
- `YYYY-MM-DD_posting_report.csv`: 投稿実行レポート
- `YYYY-MM-DD_猫_analysis.csv`: 猫投稿分析結果
- `YYYY-MM-DD_犬_analysis.csv`: 犬投稿分析結果

## 注意事項

- Twitter APIの利用制限に注意してください
- OpenAI APIの使用量を定期的に確認してください
- tweets.jsファイルは定期的にバックアップを取ることを推奨します
- 投稿内容は事前に確認し、必要に応じて手動調整してください

## ライセンス

このプロジェクトは個人利用を目的として作成されています。

## サポート

問題が発生した場合は、各モジュールの単体テストを実行して問題箇所を特定してください。
