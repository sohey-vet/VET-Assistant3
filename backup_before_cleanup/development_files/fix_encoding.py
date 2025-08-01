#!/usr/bin/env python3
"""
エンコーディング問題の緊急修正スクリプト
"""

import sys
import os

# Windowsでの絵文字表示問題を修正
def setup_encoding():
    """コンソール出力のエンコーディングを設定"""
    try:
        # Windowsの場合、コンソールをUTF-8に設定
        if sys.platform.startswith('win'):
            os.system('chcp 65001 > nul')
            
        # stdout/stderrのエンコーディングを強制的にUTF-8に
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        
        print("エンコーディング設定完了")
        return True
        
    except Exception as e:
        print(f"エンコーディング設定エラー: {e}")
        return False

def safe_print(text):
    """安全な文字列出力（絵文字エラー回避）"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 絵文字を除去して出力
        safe_text = text.encode('ascii', errors='ignore').decode('ascii')
        print(f"[ENCODED] {safe_text}")

if __name__ == "__main__":
    setup_encoding()
    safe_print("🔧 エンコーディング修正テスト完了")