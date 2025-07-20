import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any


class CSVExporter:
    def __init__(self, output_dir: str = "出力"):
        """
        CSV出力クラスの初期化
        """
        self.output_dir = output_dir
        # 出力ディレクトリが存在しない場合は作成
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def export_weekly_posts(self, weekly_content: List[Dict], filename_prefix: str = None) -> str:
        """
        週間投稿データをCSVファイルに出力
        
        Args:
            weekly_content: 週間コンテンツのリスト
            filename_prefix: ファイル名のプレフィックス
            
        Returns:
            str: 出力されたファイルのパス
        """
        try:
            # DataFrameに変換
            df = pd.DataFrame(weekly_content)
            
            # ファイル名の生成
            if filename_prefix:
                filename = f"{filename_prefix}_posts.csv"
            else:
                today = datetime.now()
                filename = f"{today.strftime('%Y-%m-%d')}_posts.csv"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # CSVファイルとして出力
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            print(f"✅ CSV出力完了: {filepath}")
            print(f"📊 出力件数: {len(weekly_content)}件")
            
            return filepath
            
        except Exception as e:
            print(f"❌ CSV出力エラー: {e}")
            return ""
    
    def export_combined_posts(self, cat_content: List[Dict], dog_content: List[Dict], filename_prefix: str = None) -> str:
        """
        猫と犬の投稿を結合してCSVファイルに出力
        
        Args:
            cat_content: 猫の週間コンテンツ
            dog_content: 犬の週間コンテンツ
            filename_prefix: ファイル名のプレフィックス
            
        Returns:
            str: 出力されたファイルのパス
        """
        try:
            # 両方のコンテンツを結合
            combined_content = cat_content + dog_content
            
            # 日付順にソート
            combined_content.sort(key=lambda x: x['date'])
            
            return self.export_weekly_posts(combined_content, filename_prefix)
            
        except Exception as e:
            print(f"❌ 結合CSV出力エラー: {e}")
            return ""
    
    def export_posting_schedule(self, weekly_content: List[Dict], filename_prefix: str = None) -> str:
        """
        投稿スケジュール表をCSVファイルに出力
        """
        try:
            # スケジュール用のデータを準備
            schedule_data = []
            
            for content in weekly_content:
                schedule_data.append({
                    '投稿日': content['date'],
                    '曜日': content['day'],
                    '時刻': content['scheduled_time'],
                    '動物種': content['animal_type'],
                    'テーマ': content['theme'],
                    '文字数': content['character_count'],
                    '投稿文(冒頭50文字)': content['post_text'][:50] + '...' if len(content['post_text']) > 50 else content['post_text']
                })
            
            df = pd.DataFrame(schedule_data)
            
            # ファイル名の生成
            if filename_prefix:
                filename = f"{filename_prefix}_schedule.csv"
            else:
                today = datetime.now()
                filename = f"{today.strftime('%Y-%m-%d')}_schedule.csv"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # CSVファイルとして出力
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            print(f"✅ スケジュールCSV出力完了: {filepath}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ スケジュールCSV出力エラー: {e}")
            return ""
    
    def export_content_analysis(self, analysis_data: Dict, animal_type: str, filename_prefix: str = None) -> str:
        """
        コンテンツ分析結果をCSVファイルに出力
        """
        try:
            # 分析データを整理
            analysis_rows = []
            
            # 最近のテーマ
            for theme in analysis_data.get('themes', []):
                analysis_rows.append({
                    '分析項目': '最近のテーマ',
                    '内容': theme,
                    '動物種': animal_type
                })
            
            # 季節性パターン
            for month, topics in analysis_data.get('seasonal_patterns', {}).items():
                for topic in topics:
                    analysis_rows.append({
                        '分析項目': f'{month}月のテーマ',
                        '内容': topic,
                        '動物種': animal_type
                    })
            
            # 投稿総数
            analysis_rows.append({
                '分析項目': '過去3ヶ月の投稿数',
                '内容': str(analysis_data.get('total_posts', 0)),
                '動物種': animal_type
            })
            
            df = pd.DataFrame(analysis_rows)
            
            # ファイル名の生成
            if filename_prefix:
                filename = f"{filename_prefix}_{animal_type}_analysis.csv"
            else:
                today = datetime.now()
                filename = f"{today.strftime('%Y-%m-%d')}_{animal_type}_analysis.csv"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # CSVファイルとして出力
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            print(f"✅ 分析CSV出力完了: {filepath}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ 分析CSV出力エラー: {e}")
            return ""
    
    def create_posting_report(self, posted_content: List[Dict], filename_prefix: str = None) -> str:
        """
        投稿完了レポートをCSVファイルに出力
        """
        try:
            # レポート用のデータを準備
            report_data = []
            
            for content in posted_content:
                report_data.append({
                    '投稿日時': content.get('posted_at', ''),
                    '動物種': content.get('animal_type', ''),
                    'テーマ': content.get('theme', ''),
                    '投稿文': content.get('post_text', ''),
                    '文字数': content.get('character_count', 0),
                    '投稿ID': content.get('tweet_id', ''),
                    '投稿結果': '成功' if content.get('success', False) else '失敗',
                    'エラー内容': content.get('error_message', '')
                })
            
            df = pd.DataFrame(report_data)
            
            # ファイル名の生成
            if filename_prefix:
                filename = f"{filename_prefix}_report.csv"
            else:
                today = datetime.now()
                filename = f"{today.strftime('%Y-%m-%d')}_posting_report.csv"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # CSVファイルとして出力
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            print(f"✅ 投稿レポートCSV出力完了: {filepath}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ レポートCSV出力エラー: {e}")
            return ""
    
    def list_output_files(self) -> List[str]:
        """
        出力ディレクトリ内のファイル一覧を取得
        """
        try:
            if not os.path.exists(self.output_dir):
                return []
            
            files = [f for f in os.listdir(self.output_dir) if f.endswith('.csv')]
            files.sort(reverse=True)  # 新しいファイル順
            
            return [os.path.join(self.output_dir, f) for f in files]
            
        except Exception as e:
            print(f"ファイル一覧取得エラー: {e}")
            return []
    
    def cleanup_old_files(self, keep_days: int = 30) -> int:
        """
        古いCSVファイルを削除
        
        Args:
            keep_days: 保持日数
            
        Returns:
            int: 削除されたファイル数
        """
        try:
            if not os.path.exists(self.output_dir):
                return 0
            
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
            deleted_count = 0
            
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.csv'):
                    filepath = os.path.join(self.output_dir, filename)
                    file_time = os.path.getmtime(filepath)
                    
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        deleted_count += 1
                        print(f"古いファイルを削除: {filename}")
            
            print(f"✅ クリーンアップ完了: {deleted_count}件のファイルを削除")
            return deleted_count
            
        except Exception as e:
            print(f"❌ クリーンアップエラー: {e}")
            return 0


if __name__ == "__main__":
    # テスト実行
    exporter = CSVExporter()
    
    # テスト用のサンプルデータ
    sample_content = [
        {
            'date': '2025-07-21',
            'day': '月曜',
            'animal_type': '猫',
            'theme': '猫の健康管理',
            'post_text': '【猫の健康チェック】\n\n愛猫の様子を毎日観察することが大切です🐱\n\n#猫のあれこれ',
            'character_count': 45,
            'scheduled_time': '07:00'
        },
        {
            'date': '2025-07-21',
            'day': '月曜',
            'animal_type': '犬',
            'theme': '犬の熱中症対策',
            'post_text': '【夏のクイズ！】\n\nQ. 散歩に最適な時間は？\n①朝夕の涼しい時間\n②昼間でも水分補給すれば平気\n\n正解は明日！🐕\n\n#獣医が教える犬のはなし',
            'character_count': 78,
            'scheduled_time': '18:00'
        }
    ]
    
    # CSV出力テスト
    output_path = exporter.export_weekly_posts(sample_content, "test")
    print(f"テスト出力完了: {output_path}")
    
    # ファイル一覧表示
    files = exporter.list_output_files()
    print(f"出力ファイル一覧: {len(files)}件")
    for f in files[:5]:  # 最新5件のみ表示
        print(f"  - {os.path.basename(f)}")