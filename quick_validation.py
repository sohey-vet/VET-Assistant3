#!/usr/bin/env python3
"""
VET-Assistant3 クイック検証スクリプト

発見された問題を迅速に調査します。
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# エンコーディング問題の回避
def safe_print(text):
    """安全な文字列出力（絵文字エラー回避）"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 絵文字を[EMOJI]に置換して出力
        import re
        safe_text = re.sub(r'[^\x00-\x7F]', '[EMOJI]', text)
        print(safe_text)

from modules.content_generator import ContentGenerator
import pandas as pd


def test_character_limits():
    """文字数制限の詳細検証"""
    print("=== 文字数制限検証 ===")
    
    generator = ContentGenerator()
    
    # 犬投稿のテスト（問題が発見された箇所）
    print("\n[犬投稿テスト]")
    dog_themes = ['犬の健康管理', '犬の行動学', '犬のしつけ', '犬の栄養学']
    
    for theme in dog_themes:
        try:
            print(f"\nテーマ: {theme}")
            post = generator.generate_dog_post(theme, '月曜')
            char_count = len(post)
            
            safe_print(f"文字数: {char_count}")
            safe_print(f"制限範囲: 125-135字")
            safe_print(f"範囲内: {'YES' if 125 <= char_count <= 135 else 'NO'}")
            safe_print(f"内容: {post}")
            safe_print("-" * 50)
            
            if char_count < 125:
                print(f"[ERROR] 文字数不足: {char_count}文字 (最低125字必要)")
            elif char_count > 135:
                print(f"[ERROR] 文字数超過: {char_count}文字 (最大135字)")
            else:
                print(f"[OK] 文字数適正")
                
        except Exception as e:
            print(f"[ERROR] 生成エラー: {e}")
    
    # 猫投稿のテスト（参考）
    print("\n[猫投稿テスト]")
    cat_themes = ['猫の健康管理', '猫の行動学']
    
    for theme in cat_themes:
        try:
            print(f"\nテーマ: {theme}")
            post = generator.generate_cat_post(theme, '月曜')
            char_count = len(post)
            
            safe_print(f"文字数: {char_count}")
            safe_print(f"制限範囲: 125-140字")
            safe_print(f"範囲内: {'YES' if 125 <= char_count <= 140 else 'NO'}")
            safe_print(f"内容: {post[:100]}...")
            safe_print("-" * 50)
            
        except Exception as e:
            print(f"[ERROR] 生成エラー: {e}")


def test_quiz_answer_pairs():
    """クイズ・回答ペアの検証"""
    print("\n=== クイズ・回答ペア検証 ===")
    
    generator = ContentGenerator()
    
    # フォールバック機能でのペア確認
    print("\n[フォールバック機能でのペア確認]")
    
    monday_post = generator._get_guaranteed_dog_content('月曜', '犬の健康管理', 0)
    tuesday_post = generator._get_guaranteed_dog_content('火曜', '犬の健康管理', 1)
    wednesday_post = generator._get_guaranteed_dog_content('水曜', '犬の行動学', 2)
    thursday_post = generator._get_guaranteed_dog_content('木曜', '犬の行動学', 3)
    
    safe_print(f"\n月曜クイズ ({len(monday_post)}字): {monday_post}")
    safe_print(f"\n火曜回答 ({len(tuesday_post)}字): {tuesday_post}")
    safe_print(f"\n水曜クイズ ({len(wednesday_post)}字): {wednesday_post}")
    safe_print(f"\n木曜回答 ({len(thursday_post)}字): {thursday_post}")
    
    # ペアの一貫性確認
    print("\n[ペア一貫性確認]")
    print(f"月曜にクイズ含有: {'クイズ' in monday_post}")
    print(f"火曜に回答含有: {'答え' in tuesday_post and '正解' in tuesday_post}")
    print(f"水曜にクイズ含有: {'クイズ' in wednesday_post}")
    print(f"木曜に回答含有: {'答え' in thursday_post and '正解' in thursday_post}")


def test_csv_output():
    """CSV出力の検証"""
    print("\n=== CSV出力検証 ===")
    
    # 現在の出力ファイルを確認
    output_dir = "出力"
    if os.path.exists(output_dir):
        csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
        print(f"出力ファイル数: {len(csv_files)}")
        
        if csv_files:
            latest_file = max([os.path.join(output_dir, f) for f in csv_files], key=os.path.getmtime)
            print(f"最新ファイル: {latest_file}")
            
            try:
                df = pd.read_csv(latest_file, encoding='utf-8-sig')
                print(f"データ行数: {len(df)}")
                print(f"列: {list(df.columns)}")
                
                # 文字数の実際の分布確認
                if '文字数' in df.columns:
                    char_counts = df['文字数'].tolist()
                    print(f"文字数分布: 最小{min(char_counts)}, 最大{max(char_counts)}, 平均{sum(char_counts)/len(char_counts):.1f}")
                    
                    # 制限違反の確認
                    violations = []
                    for i, row in df.iterrows():
                        animal_type = row.get('動物種', '')
                        char_count = row.get('文字数', 0)
                        
                        if animal_type == '猫' and not (125 <= char_count <= 140):
                            violations.append(f"行{i+1}: 猫 {char_count}字 (125-140字範囲外)")
                        elif animal_type == '犬' and not (125 <= char_count <= 135):
                            violations.append(f"行{i+1}: 犬 {char_count}字 (125-135字範囲外)")
                    
                    if violations:
                        print(f"\n[ERROR] 文字数制限違反 {len(violations)}件:")
                        for violation in violations:
                            print(f"  - {violation}")
                    else:
                        print("[OK] 全投稿が文字数制限を遵守")
                        
            except Exception as e:
                print(f"[ERROR] CSVファイル読み込みエラー: {e}")
    else:
        print("[WARN] 出力ディレクトリが存在しません")


def main():
    """メイン検証実行"""
    print("VET-Assistant3 クイック検証開始")
    print("=" * 50)
    
    try:
        test_character_limits()
        test_quiz_answer_pairs()
        test_csv_output()
        
        print("\n" + "=" * 50)
        print("クイック検証完了")
        
    except Exception as e:
        print(f"[CRITICAL ERROR] 検証中に重大なエラー: {e}")


if __name__ == "__main__":
    main()