#!/usr/bin/env python3
"""
CSV予約投稿機能のテストスクリプト
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# モジュールパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scheduler import VETScheduler


def create_test_csv():
    """
    テスト用のCSVファイルを作成
    """
    # 今日から5日後までのテストデータを作成
    test_data = []
    base_date = datetime.now()
    
    for i in range(5):
        date = base_date + timedelta(days=i)
        test_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'day': ['月曜', '火曜', '水曜', '木曜', '金曜', '土曜', '日曜'][date.weekday()],
            'animal_type': '猫' if i % 2 == 0 else '犬',
            'theme': f'テスト投稿{i+1}',
            'post_text': f'【テスト投稿{i+1}】\n\nVET-Assistant3の予約投稿テストです\n\n日付: {date.strftime("%Y-%m-%d")}\n\n#テスト #VET',
            'character_count': 50,
            'scheduled_time': '12:00' if i % 2 == 0 else '15:00'
        })
    
    # CSVファイルに保存
    df = pd.DataFrame(test_data)
    test_csv_path = os.path.join('出力', 'test_scheduled_posts.csv')
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs('出力', exist_ok=True)
    
    df.to_csv(test_csv_path, index=False, encoding='utf-8')
    print(f"テスト用CSVファイル作成: {test_csv_path}")
    print(f"テストデータ件数: {len(test_data)}件")
    
    return test_csv_path


def test_csv_loading():
    """
    CSVファイル読み込み機能のテスト
    """
    print("\nCSVファイル読み込みテスト開始")
    
    # テスト用CSVファイルを作成
    test_csv_path = create_test_csv()
    
    # スケジューラーを初期化
    scheduler = VETScheduler()
    
    # CSVファイル読み込みテスト
    success = scheduler.load_csv_schedule(test_csv_path)
    
    if success:
        print("CSVファイル読み込みテスト成功")
        return test_csv_path
    else:
        print("CSVファイル読み込みテスト失敗")
        return None


def test_twitter_connection():
    """
    Twitter API接続テスト
    """
    print("\nTwitter API接続テスト開始")
    
    scheduler = VETScheduler()
    
    if scheduler.twitter_poster.test_connection():
        print("Twitter API接続テスト成功")
        return True
    else:
        print("Twitter API接続テスト失敗")
        print(".envファイルでTwitter API認証情報を確認してください")
        return False


def main():
    """
    テストメイン実行
    """
    print("VET-Assistant3 予約投稿機能テスト開始")
    print("=" * 50)
    
    # 1. CSVファイル読み込みテスト
    test_csv_path = test_csv_loading()
    
    if not test_csv_path:
        print("CSVテスト失敗のため、テストを中止します")
        return
    
    # 2. Twitter API接続テスト
    twitter_ok = test_twitter_connection()
    
    # 3. 結果表示
    print("\n" + "=" * 50)
    print("テスト結果:")
    print(f"   CSV読み込み: {'成功' if test_csv_path else '失敗'}")
    print(f"   Twitter API: {'成功' if twitter_ok else '失敗'}")
    
    if test_csv_path and twitter_ok:
        print("\nすべてのテストが成功しました！")
        print(f"\n予約投稿を開始するには以下のコマンドを実行してください:")
        print(f"   python scheduler.py post \"{test_csv_path}\"")
    else:
        print("\n一部のテストが失敗しました")
        if not twitter_ok:
            print("   Twitter API認証情報を.envファイルで設定してください")
    
    print("\nテスト完了")


if __name__ == "__main__":
    main()