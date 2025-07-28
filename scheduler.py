import schedule
import time
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# モジュールの追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.content_generator import ContentGenerator
from modules.csv_exporter import CSVExporter


class VETScheduler:
    def __init__(self):
        """
        VET-Assistant3スケジューラーの初期化（コンテンツ生成専用）
        """
        self.content_generator = ContentGenerator()
        self.csv_exporter = CSVExporter()
        self.output_dir = "出力"
        
        print("BOT: VET-Assistant3 コンテンツ生成システム起動")
        
        # Gemini API接続確認
        try:
            # 簡単なテスト生成で接続確認
            test_response = self.content_generator.generate_cat_post("テスト", "月曜")
            if "テスト" in test_response or len(test_response) > 10:
                print("SUCCESS: Gemini API接続確認完了")
            else:
                print("WARNING: Gemini APIの動作に問題がある可能性があります")
        except Exception as e:
            print(f"WARNING: Gemini API接続確認エラー: {e}")
    
    def generate_weekly_content(self):
        """
        1週間分のコンテンツを生成してCSVに出力
        """
        try:
            print("\nINFO: 週間コンテンツ生成開始...")
            
            from modules.data_manager import load_and_clean_tweets
            
            # 過去の投稿データを読み込み
            tweets_df = load_and_clean_tweets()
            print(f"DATA: 過去の投稿データ読み込み: {len(tweets_df)}件")
            
            # 猫と犬のコンテンツを生成
            cat_content = self.content_generator.generate_weekly_content('猫', tweets_df)
            dog_content = self.content_generator.generate_weekly_content('犬', tweets_df)
            
            print(f"SUCCESS: 猫コンテンツ生成: {len(cat_content)}件")
            print(f"SUCCESS: 犬コンテンツ生成: {len(dog_content)}件")
            
            # CSVファイルに出力
            next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
            filename_prefix = next_monday.strftime('%Y-%m-%d')
            
            # 結合してCSV出力
            csv_path = self.csv_exporter.export_combined_posts(cat_content, dog_content, filename_prefix)
            schedule_path = self.csv_exporter.export_posting_schedule(cat_content + dog_content, filename_prefix)
            
            print(f"SUCCESS: 週間コンテンツCSV出力完了:")
            print(f"   📄 投稿データ: {csv_path}")
            print(f"   📅 スケジュール: {schedule_path}")
            
            return csv_path, schedule_path
            
        except Exception as e:
            print(f"ERROR: 週間コンテンツ生成エラー: {e}")
            return None, None
    
    def generate_daily_content(self, animal_type: str):
        """
        今日分のコンテンツを生成
        """
        try:
            print(f"\nINFO: {animal_type}の今日分コンテンツ生成開始...")
            
            from modules.data_manager import load_and_clean_tweets, analyze_recent_themes
            
            # 過去の投稿データを読み込み
            tweets_df = load_and_clean_tweets()
            recent_analysis = analyze_recent_themes(tweets_df, animal_type)
            
            # 今日の曜日を取得
            current_time = datetime.now()
            day_of_week = ['月曜', '火曜', '水曜', '木曜', '金曜', '土曜', '日曜'][current_time.weekday()]
            
            # テーマを決定（簡易版）
            if animal_type == '猫':
                themes = ['猫の健康管理', '猫の行動学', '猫のグルーミング', '猫の栄養学']
            else:
                themes = ['犬の健康管理', '犬の行動学', '犬のしつけ', '犬の栄養学']
            
            theme = themes[current_time.weekday() % len(themes)]
            
            # コンテンツ生成
            if animal_type == '猫':
                content = self.content_generator.generate_cat_post(theme, day_of_week, recent_analysis)
            else:
                content = self.content_generator.generate_dog_post(theme, day_of_week, recent_analysis)
            
            print(f"SUCCESS: {animal_type}コンテンツ生成完了:")
            print(f"   テーマ: {theme}")
            print(f"   文字数: {len(content)}文字")
            print(f"   内容: {content[:50]}...")
            
            # 今日のデータとしてCSV出力
            today_data = [{
                'date': current_time.strftime('%Y-%m-%d'),
                'day': day_of_week,
                'animal_type': animal_type,
                'theme': theme,
                'post_text': content,
                'character_count': len(content),
                'scheduled_time': '07:00' if animal_type == '猫' else '18:00'
            }]
            
            filename = f"{current_time.strftime('%Y-%m-%d')}_{animal_type}_daily"
            csv_path = self.csv_exporter.export_weekly_posts(today_data, filename)
            
            print(f"SUCCESS: 今日分CSV出力完了: {csv_path}")
            
            return content, csv_path
            
        except Exception as e:
            print(f"ERROR: 今日分コンテンツ生成エラー: {e}")
            return None, None
    
    def setup_weekly_schedule(self):
        """
        週間コンテンツ生成のスケジュールを設定
        """
        # 毎週日曜日の20時に次週のコンテンツを生成
        schedule.every().sunday.at("20:00").do(self.generate_weekly_content)
        print("⏰ 週間コンテンツ生成スケジュール設定: 毎週日曜日 20:00")
    
    def run_weekly_scheduler(self):
        """
        週間コンテンツ生成スケジューラーを実行
        """
        print("\n🚀 VET-Assistant3 週間コンテンツ生成スケジューラー開始")
        print("⏰ スケジュール:")
        print("   INFO: 週間コンテンツ生成: 毎週日曜日 20:00")
        print("\n終了するには Ctrl+C を押してください\n")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分間隔でチェック
    
    def manual_content_test(self):
        """
        手動コンテンツ生成テスト
        """
        print("\n🧪 手動コンテンツ生成テスト開始")
        
        # 猫のコンテンツテスト
        print("\n=== 猫コンテンツテスト ===")
        cat_content, cat_csv = self.generate_daily_content('猫')
        
        print("\n=== 犬コンテンツテスト ===")
        dog_content, dog_csv = self.generate_daily_content('犬')
        
        print(f"\nDATA: テスト結果:")
        print(f"   🐱 猫: {'成功' if cat_content else '失敗'}")
        print(f"   🐕 犬: {'成功' if dog_content else '失敗'}")
        
        return cat_content, dog_content


def main():
    """
    メイン実行関数
    """
    scheduler = VETScheduler()
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            # テスト実行
            scheduler.manual_content_test()
        elif command == "generate":
            # 週間コンテンツ生成のみ
            scheduler.generate_weekly_content()
        elif command == "daily":
            # 今日分のコンテンツ生成
            if len(sys.argv) > 2:
                animal_type = sys.argv[2]
                scheduler.generate_daily_content(animal_type)
            else:
                print("使用方法: python scheduler.py daily [猫|犬]")
        elif command == "schedule":
            # スケジュール設定して実行
            scheduler.setup_weekly_schedule()
            scheduler.run_weekly_scheduler()
        else:
            print("使用方法:")
            print("  python scheduler.py test           # 手動コンテンツ生成テスト")
            print("  python scheduler.py generate       # 週間コンテンツ生成")
            print("  python scheduler.py daily 猫       # 今日分猫コンテンツ生成")
            print("  python scheduler.py daily 犬       # 今日分犬コンテンツ生成")
            print("  python scheduler.py schedule       # 週間スケジューラー実行")
    else:
        # デフォルトは週間コンテンツ生成
        scheduler.generate_weekly_content()


if __name__ == "__main__":
    main()