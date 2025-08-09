#!/usr/bin/env python3
"""
VET-Assistant3 メインエントリーポイント

獣医師の専門知識を活用したコンテンツ生成システム（X投稿なし版）
"""

# VET-Assistant3 メイン

import os
import sys
from dotenv import load_dotenv

# .env を一度だけ読み込む（ここが最重要）
load_dotenv()

# プロジェクトルートを Python パスへ
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from modules.data_manager import load_and_clean_tweets, analyze_recent_themes
from modules.content_generator import ContentGenerator
from modules.csv_exporter import CSVExporter
from scheduler import VETScheduler



def main():
    """
    メイン実行関数
    """
    print("VET-Assistant3 起動中...")
    print("=" * 50)
    
    # 環境変数チェック
    required_env_vars = [
        'GEMINI_API_KEY',
        'GOOGLE_SHEETS_CREDENTIALS_PATH',
        'GOOGLE_SHEETS_SPREADSHEET_ID'
    ]
    
    missing_vars = []

    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("WARNING: 必要な環境変数が設定されていません:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n.envファイルを確認してください。")
        print("Gemini APIキーなしでもデータ分析は可能です。")
        print("ただし Google Sheets 連携は上記2つの変数が必要です。")
    else:
        print("SUCCESS: 環境変数チェック完了")

    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "help" or command == "-h" or command == "--help":
            show_help()
        elif command == "test":
            run_tests()
        elif command == "generate":
            generate_weekly_content()
        elif command == "daily":
            if len(sys.argv) > 2:
                generate_daily_content(sys.argv[2])
            else:
                print("使用方法: python main.py daily [猫|犬]")
        elif command == "analyze":
            analyze_past_posts()
        elif command == "schedule":
            run_scheduler()
        else:
            print(f"ERROR: 不明なコマンド: {command}")
            show_help()
    else:
        # デフォルトは週間コンテンツ生成
        generate_weekly_content()


def show_help():
    """
    ヘルプメッセージを表示
    """
    print("""
VET-Assistant3 使用方法:

python main.py [command]

コマンド:
  help      このヘルプを表示
  test      システムテストを実行
  generate  週間コンテンツを生成
  daily     今日分のコンテンツを生成 (猫|犬)
  analyze   過去投稿の分析を実行
  schedule  週間コンテンツ生成スケジューラーを開始

例:
  python main.py                # 週間コンテンツ生成
  python main.py test          # システムテスト
  python main.py generate      # 週間コンテンツ生成
  python main.py daily 猫      # 今日分猫コンテンツ生成
  python main.py analyze       # 過去投稿分析
""")


def run_tests():
    """
    システムテストを実行
    """
    print("\nTEST: VET-Assistant3 システムテスト開始")
    print("=" * 50)
    
    # 1. データ管理テスト
    print("\nDATA: データ管理テスト...")
    try:
        df = load_and_clean_tweets()
        print(f"SUCCESS: tweets.js読み込み成功: {len(df)}件")
        
        cat_analysis = analyze_recent_themes(df, '猫')
        dog_analysis = analyze_recent_themes(df, '犬')
        print(f"SUCCESS: 分析完了 - 猫: {len(cat_analysis['themes'])}テーマ, 犬: {len(dog_analysis['themes'])}テーマ")
    except Exception as e:
        print(f"ERROR: データ管理テスト失敗: {e}")
    
    # 2. コンテンツ生成テスト
    print("\nINFO: コンテンツ生成テスト...")
    try:
        generator = ContentGenerator()
        cat_post = generator.generate_cat_post("猫の健康管理", "月曜")
        dog_post = generator.generate_dog_post("犬の健康管理", "月曜")
        print(f"SUCCESS: 猫投稿生成成功: {len(cat_post)}文字")
        print(f"SUCCESS: 犬投稿生成成功: {len(dog_post)}文字")
        
        # 文字数チェック
        if 125 <= len(cat_post) <= 140:
            print(f"SUCCESS: 猫投稿文字数OK: {len(cat_post)}文字")
        else:
            print(f"WARNING: 猫投稿文字数範囲外: {len(cat_post)}文字 (125-140字)")
            
        if 125 <= len(dog_post) <= 135:
            print(f"SUCCESS: 犬投稿文字数OK: {len(dog_post)}文字")
        else:
            print(f"WARNING: 犬投稿文字数範囲外: {len(dog_post)}文字 (125-135字)")
        
    except Exception as e:
        print(f"ERROR: コンテンツ生成テスト失敗: {e}")
    
    # 3. CSV出力テスト
    print("\nCSV: CSV出力テスト...")
    try:
        exporter = CSVExporter()
        test_data = [{
            'date': '2025-07-21',
            'day': '月曜',
            'animal_type': 'テスト',
            'theme': 'システムテスト',
            'post_text': 'テスト投稿',
            'character_count': 5,
            'scheduled_time': '12:00'
        }]
        output_path = exporter.export_weekly_posts(test_data, "test")
        if output_path:
            print(f"SUCCESS: CSV出力成功: {output_path}")
        else:
            print("ERROR: CSV出力失敗")
    except Exception as e:
        print(f"ERROR: CSV出力テスト失敗: {e}")
    
    print("\nFINISH: システムテスト完了")


def generate_weekly_content():
    """
    週間コンテンツを生成
    """
    print("\nINFO: 週間コンテンツ生成開始")
    print("=" * 50)
    
    try:
        scheduler = VETScheduler()
        csv_path, schedule_path = scheduler.generate_weekly_content()
        
        if csv_path and schedule_path:
            print(f"\nSUCCESS: 週間コンテンツ生成完了!")
            print(f"CSV: 投稿データ: {csv_path}")
            print(f"📅 スケジュール: {schedule_path}")
        else:
            print("ERROR: 週間コンテンツ生成に失敗しました")
            
    except Exception as e:
        print(f"ERROR: 週間コンテンツ生成エラー: {e}")


def generate_daily_content(animal_type: str):
    """
    今日分のコンテンツを生成
    """
    print(f"\nINFO: {animal_type}の今日分コンテンツ生成開始")
    print("=" * 50)
    
    try:
        scheduler = VETScheduler()
        content, csv_path = scheduler.generate_daily_content(animal_type)
        
        if content and csv_path:
            print(f"\nSUCCESS: {animal_type}コンテンツ生成完了!")
            print(f"CSV: CSV出力: {csv_path}")
            print(f"INFO: 生成内容:\n{content}")
        else:
            print(f"ERROR: {animal_type}コンテンツ生成に失敗しました")
            
    except Exception as e:
        print(f"ERROR: {animal_type}コンテンツ生成エラー: {e}")


def analyze_past_posts():
    """
    過去投稿の分析を実行
    """
    print("\nDATA: 過去投稿分析開始")
    print("=" * 50)
    
    try:
        df = load_and_clean_tweets()
        print(f"DATA: 読み込み完了: {len(df)}件の投稿")
        
        # 猫の分析
        print("\n🐱 猫投稿分析...")
        cat_analysis = analyze_recent_themes(df, '猫')
        print(f"   最近のテーマ数: {len(cat_analysis['themes'])}")
        print(f"   過去3ヶ月の投稿数: {cat_analysis['total_posts']}")
        
        # 犬の分析
        print("\n🐕 犬投稿分析...")
        dog_analysis = analyze_recent_themes(df, '犬')
        print(f"   最近のテーマ数: {len(dog_analysis['themes'])}")
        print(f"   過去3ヶ月の投稿数: {dog_analysis['total_posts']}")
        
        # CSV出力
        exporter = CSVExporter()
        cat_csv = exporter.export_content_analysis(cat_analysis, '猫')
        dog_csv = exporter.export_content_analysis(dog_analysis, '犬')
        
        print(f"\nSUCCESS: 分析結果CSV出力完了:")
        print(f"   🐱 猫: {cat_csv}")
        print(f"   🐕 犬: {dog_csv}")
        
    except Exception as e:
        print(f"ERROR: 分析エラー: {e}")


def run_scheduler():
    """
    週間コンテンツ生成スケジューラーを実行
    """
    print("\n🚀 VET-Assistant3 週間コンテンツ生成スケジューラー開始")
    print("=" * 50)
    
    try:
        scheduler = VETScheduler()
        scheduler.setup_weekly_schedule()
        scheduler.run_weekly_scheduler()
    except KeyboardInterrupt:
        print("\n\n⏹️ スケジューラーを停止しました")
    except Exception as e:
        print(f"ERROR: スケジューラーエラー: {e}")


if __name__ == "__main__":
    main()