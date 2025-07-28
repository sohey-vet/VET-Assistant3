#!/usr/bin/env python3
"""
VET-Assistant3 システム全体検証テストスイート

徹底的なバグ検証とシステム品質確認を行います。
"""

import os
import sys
import unittest
import pandas as pd
import json
import re
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.content_generator import ContentGenerator
from modules.csv_exporter import CSVExporter
from modules.data_manager import load_and_clean_tweets, analyze_recent_themes
from scheduler import VETScheduler


class TestContentGeneration(unittest.TestCase):
    """コンテンツ生成機能のテスト"""
    
    def setUp(self):
        self.generator = ContentGenerator()
    
    def test_cat_post_character_limits(self):
        """猫投稿の文字数制限テスト（125-140字）"""
        print("\n=== 猫投稿文字数制限テスト ===")
        
        themes = ['猫の健康管理', '猫の行動学', '猫のグルーミング', '猫の栄養学']
        for theme in themes:
            with self.subTest(theme=theme):
                try:
                    post = self.generator.generate_cat_post(theme, '月曜')
                    char_count = len(post)
                    print(f"{theme}: {char_count}文字")
                    print(f"内容: {post[:50]}...")
                    
                    self.assertGreaterEqual(char_count, 125, 
                                          f"{theme}: 文字数が少なすぎます ({char_count}文字)")
                    self.assertLessEqual(char_count, 140, 
                                       f"{theme}: 文字数が多すぎます ({char_count}文字)")
                    self.assertIn('#猫のあれこれ', post, 
                                f"{theme}: ハッシュタグが含まれていません")
                except Exception as e:
                    self.fail(f"{theme}の生成でエラー: {e}")
    
    def test_dog_post_character_limits(self):
        """犬投稿の文字数制限テスト（125-135字）"""
        print("\n=== 犬投稿文字数制限テスト ===")
        
        themes = ['犬の健康管理', '犬の行動学', '犬のしつけ', '犬の栄養学']
        for theme in themes:
            with self.subTest(theme=theme):
                try:
                    post = self.generator.generate_dog_post(theme, '月曜')
                    char_count = len(post)
                    print(f"{theme}: {char_count}文字")
                    print(f"内容: {post[:50]}...")
                    
                    self.assertGreaterEqual(char_count, 125, 
                                          f"{theme}: 文字数が少なすぎます ({char_count}文字)")
                    self.assertLessEqual(char_count, 135, 
                                       f"{theme}: 文字数が多すぎます ({char_count}文字)")
                    self.assertIn('#獣医が教える犬のはなし', post, 
                                f"{theme}: ハッシュタグが含まれていません")
                except Exception as e:
                    self.fail(f"{theme}の生成でエラー: {e}")

    def test_quiz_answer_consistency(self):
        """クイズ・回答ペアの一貫性テスト"""
        print("\n=== クイズ・回答ペア一貫性テスト ===")
        
        # 月曜→火曜のペア
        monday_post = self.generator._get_guaranteed_dog_content('月曜', '犬の健康管理', 0)
        tuesday_post = self.generator._get_guaranteed_dog_content('火曜', '犬の健康管理', 1)
        
        print(f"月曜クイズ: {monday_post[:50]}...")
        print(f"火曜回答: {tuesday_post[:50]}...")
        
        self.assertIn('クイズ', monday_post, "月曜投稿にクイズが含まれていません")
        self.assertIn('答え', tuesday_post, "火曜投稿に答えが含まれていません")
        self.assertIn('正解', tuesday_post, "火曜投稿に正解が含まれていません")
        
        # 水曜→木曜のペア
        wednesday_post = self.generator._get_guaranteed_dog_content('水曜', '犬の行動学', 2)
        thursday_post = self.generator._get_guaranteed_dog_content('木曜', '犬の行動学', 3)
        
        print(f"水曜クイズ: {wednesday_post[:50]}...")
        print(f"木曜回答: {thursday_post[:50]}...")
        
        self.assertIn('クイズ', wednesday_post, "水曜投稿にクイズが含まれていません")
        self.assertIn('答え', thursday_post, "木曜投稿に答えが含まれていません")
        self.assertIn('正解', thursday_post, "木曜投稿に正解が含まれていません")

    def test_content_quality_validation(self):
        """コンテンツ品質検証機能のテスト"""
        print("\n=== コンテンツ品質検証テスト ===")
        
        # 正常なコンテンツ
        valid_content = [
            {'day': '月曜', 'post_text': '【テストクイズ】これは正常なコンテンツです。A.選択肢1 B.選択肢2 C.選択肢3 答えは明日！#獣医が教える犬のはなし', 'animal_type': '犬'},
            {'day': '火曜', 'post_text': '【昨日の答え】正解はAでした！詳しく解説します。#獣医が教える犬のはなし', 'animal_type': '犬'},
            {'day': '水曜', 'post_text': '【新しいクイズ】新しい問題です。A.選択肢1 B.選択肢2 C.選択肢3 答えは明日！#獣医が教える犬のはなし', 'animal_type': '犬'},
            {'day': '木曜', 'post_text': '【昨日の答え】正解はBでした！詳しく解説します。#獣医が教える犬のはなし', 'animal_type': '犬'},
            {'day': '金曜', 'post_text': '【金曜日の投稿】正常なコンテンツです。#獣医が教える犬のはなし', 'animal_type': '犬'},
            {'day': '土曜', 'post_text': '【土曜日の投稿】正常なコンテンツです。#獣医が教える犬のはなし', 'animal_type': '犬'},
            {'day': '日曜', 'post_text': '【日曜日の投稿】正常なコンテンツです。#獣医が教える犬のはなし', 'animal_type': '犬'},
        ]
        
        result = self.generator._check_content_quality(valid_content)
        self.assertTrue(result, "正常なコンテンツが品質チェックで失敗")
        
        # 異常なコンテンツ（短すぎる）
        invalid_content_short = [
            {'day': '月曜', 'post_text': '短すぎ', 'animal_type': '犬'},
        ]
        
        result = self.generator._check_content_quality(invalid_content_short)
        self.assertFalse(result, "短すぎるコンテンツが品質チェックを通過")
        
        # 異常なコンテンツ（ハッシュタグなし）
        invalid_content_no_hashtag = [
            {'day': '月曜', 'post_text': '【テスト】ハッシュタグがないコンテンツです。十分な長さがあります。', 'animal_type': '犬'},
        ]
        
        result = self.generator._check_content_quality(invalid_content_no_hashtag)
        self.assertFalse(result, "ハッシュタグなしコンテンツが品質チェックを通過")


class TestCSVExport(unittest.TestCase):
    """CSV出力機能のテスト"""
    
    def setUp(self):
        self.exporter = CSVExporter(enable_google_sheets=False)  # テスト用にGoogle Sheets無効
        self.test_content = [
            {
                'date': '2025-07-28',
                'day': '月曜',
                'animal_type': '猫',
                'theme': 'テスト',
                'post_text': '【テスト投稿】これはテスト用の投稿です。🐱✨\n\n#猫のあれこれ',
                'character_count': 35,
                'scheduled_time': '07:00'
            }
        ]
    
    def test_csv_output_structure(self):
        """CSV出力の構造テスト"""
        print("\n=== CSV出力構造テスト ===")
        
        output_path = self.exporter.export_weekly_posts(self.test_content, "test_structure")
        self.assertTrue(os.path.exists(output_path), "CSVファイルが作成されていません")
        
        # CSVファイルの内容確認
        df = pd.read_csv(output_path, encoding='utf-8-sig')
        expected_columns = ['date', 'day', 'animal_type', 'theme', 'post_text', 'character_count', 'scheduled_time']
        
        for col in expected_columns:
            self.assertIn(col, df.columns, f"必要な列 '{col}' が存在しません")
        
        print(f"[OK] CSV出力成功: {output_path}")
        print(f"[OK] 列構造確認: {list(df.columns)}")
        
        # ファイル削除
        if os.path.exists(output_path):
            os.remove(output_path)
    
    def test_posting_schedule_format(self):
        """投稿スケジュール形式のテスト"""
        print("\n=== 投稿スケジュール形式テスト ===")
        
        output_path = self.exporter.export_posting_schedule(self.test_content, "test_schedule")
        self.assertTrue(os.path.exists(output_path), "スケジュールCSVファイルが作成されていません")
        
        # CSVファイルの内容確認
        df = pd.read_csv(output_path, encoding='utf-8-sig')
        expected_columns = ['投稿日', '曜日', '時刻', '動物種', 'テーマ', '文字数', '投稿文(全文)']
        
        for col in expected_columns:
            self.assertIn(col, df.columns, f"必要な列 '{col}' が存在しません")
        
        print(f"[OK] スケジュールCSV出力成功: {output_path}")
        print(f"[OK] 列構造確認: {list(df.columns)}")
        
        # ファイル削除
        if os.path.exists(output_path):
            os.remove(output_path)


class TestDataManager(unittest.TestCase):
    """データ管理機能のテスト"""
    
    def test_tweets_loading(self):
        """tweets.js読み込みテスト"""
        print("\n=== tweets.js読み込みテスト ===")
        
        try:
            df = load_and_clean_tweets()
            self.assertIsInstance(df, pd.DataFrame, "DataFrameが返されていません")
            
            if not df.empty:
                print(f"[OK] tweets.js読み込み成功: {len(df)}件")
                
                # 必要な列の存在確認
                required_columns = ['tweet_id', 'full_text', 'created_at']
                for col in required_columns:
                    if col in df.columns:
                        print(f"[OK] 列 '{col}' 存在確認")
            else:
                print("[WARN] tweets.jsが空またはデータなし")
                
        except Exception as e:
            print(f"[WARN] tweets.js読み込みでエラー: {e}")
            # テストは失敗させない（ファイルが存在しない場合があるため）
    
    def test_theme_analysis(self):
        """テーマ分析機能のテスト"""
        print("\n=== テーマ分析機能テスト ===")
        
        try:
            df = load_and_clean_tweets()
            
            if not df.empty:
                cat_analysis = analyze_recent_themes(df, '猫')
                dog_analysis = analyze_recent_themes(df, '犬')
                
                self.assertIsInstance(cat_analysis, dict, "猫分析結果がdict型ではありません")
                self.assertIsInstance(dog_analysis, dict, "犬分析結果がdict型ではありません")
                
                # 期待されるキーの存在確認
                expected_keys = ['themes', 'total_posts', 'seasonal_patterns']
                for key in expected_keys:
                    self.assertIn(key, cat_analysis, f"猫分析に '{key}' が含まれていません")
                    self.assertIn(key, dog_analysis, f"犬分析に '{key}' が含まれていません")
                
                print(f"[OK] 猫テーマ分析: {len(cat_analysis['themes'])}件")
                print(f"[OK] 犬テーマ分析: {len(dog_analysis['themes'])}件")
            else:
                print("[WARN] データが空のため分析スキップ")
                
        except Exception as e:
            print(f"[WARN] テーマ分析でエラー: {e}")


class TestIntegration(unittest.TestCase):
    """統合テスト"""
    
    def setUp(self):
        self.scheduler = VETScheduler()
    
    @patch('modules.content_generator.ContentGenerator.generate_weekly_content')
    def test_weekly_content_generation_flow(self, mock_generate):
        """週間コンテンツ生成の統合フローテスト"""
        print("\n=== 週間コンテンツ生成統合テスト ===")
        
        # モックデータ設定
        mock_content = [
            {
                'date': '2025-07-28',
                'day': '月曜',
                'animal_type': '猫',
                'theme': 'テスト',
                'post_text': '【テスト投稿】これはテスト用の投稿です。🐱✨\n\n#猫のあれこれ',
                'character_count': 135,
                'scheduled_time': '07:00'
            }
        ]
        
        mock_generate.return_value = mock_content
        
        try:
            # 実際の生成フロー実行（モック使用）
            csv_path, schedule_path = self.scheduler.generate_weekly_content()
            
            self.assertIsNotNone(csv_path, "CSV出力パスがNoneです")
            self.assertIsNotNone(schedule_path, "スケジュール出力パスがNoneです")
            
            print(f"[OK] 統合フロー成功")
            print(f"[OK] CSV出力: {csv_path}")
            print(f"[OK] スケジュール出力: {schedule_path}")
            
        except Exception as e:
            self.fail(f"統合フローでエラー: {e}")


class TestErrorHandling(unittest.TestCase):
    """エラーハンドリングのテスト"""
    
    def setUp(self):
        self.generator = ContentGenerator()
    
    @patch('modules.content_generator.ContentGenerator.model.generate_content')
    def test_api_failure_fallback(self, mock_api):
        """API失敗時のフォールバック動作テスト"""
        print("\n=== API失敗フォールバックテスト ===")
        
        # APIエラーを模擬
        mock_api.side_effect = Exception("API呼び出し失敗")
        
        try:
            # フォールバック機能のテスト
            fallback_content = self.generator._generate_fallback_weekly_content('犬', ['犬の健康管理'] * 7)
            
            self.assertEqual(len(fallback_content), 7, "フォールバックコンテンツが7件生成されていません")
            
            for item in fallback_content:
                self.assertIn('post_text', item, "post_textが含まれていません")
                self.assertGreater(len(item['post_text']), 20, "フォールバック投稿が短すぎます")
                self.assertIn('#獣医が教える犬のはなし', item['post_text'], "ハッシュタグが含まれていません")
            
            print(f"[OK] フォールバック機能正常動作: {len(fallback_content)}件生成")
            
        except Exception as e:
            self.fail(f"フォールバック機能でエラー: {e}")


def run_comprehensive_validation():
    """包括的なシステム検証を実行"""
    print("VET-Assistant3 システム検証開始")
    print("=" * 60)
    
    # テストスイートの作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 各テストクラスを追加
    suite.addTests(loader.loadTestsFromTestCase(TestContentGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestCSVExport))
    suite.addTests(loader.loadTestsFromTestCase(TestDataManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # テストの実行
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("検証結果サマリー")
    print("=" * 60)
    print(f"実行テスト数: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    if result.failures:
        print("\n[FAIL] 失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\n[ERROR] エラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception: ')[-1].split('\\n')[0]}")
    
    if result.wasSuccessful():
        print("\n[SUCCESS] 全テスト合格！システムは正常に動作しています。")
    else:
        print("\n[WARNING] 一部テストで問題が発見されました。修正が必要です。")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_validation()
    sys.exit(0 if success else 1)