"""
Google Sheets 連携モジュール
VET-Assistant3の投稿データをGoogleスプレッドシートに自動同期
将来のX投稿自動化を考慮した設計
"""

import os
import json
from typing import List, Dict, Optional
import pandas as pd
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 環境変数を読み込み
load_dotenv()


class GoogleSheetsSync:
    def __init__(self, credentials_path: str = None, spreadsheet_id: str = None):
        """
        Google Sheets同期クラスの初期化
        
        Args:
            credentials_path: サービスアカウントJSONファイルのパス
            spreadsheet_id: GoogleスプレッドシートのID
        """
        self.credentials_path = credentials_path or os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
        self.spreadsheet_id = spreadsheet_id or os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """
        Google Sheets APIの認証
        """
        try:
            if not self.credentials_path or not os.path.exists(self.credentials_path):
                print("WARNING: Google Sheets認証情報が見つかりません")
                print("   サービスアカウントJSONファイルのパスを.envに設定してください")
                return
            
            # サービスアカウント認証
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
            credentials = Credentials.from_service_account_file(
                self.credentials_path, scopes=SCOPES
            )
            
            self.service = build('sheets', 'v4', credentials=credentials)
            print("SUCCESS: Google Sheets API認証成功")
            
        except Exception as e:
            print(f"ERROR: Google Sheets認証エラー: {e}")
            self.service = None
    
    def upload_posts_data(self, csv_file_path: str, sheet_name: str = "Posts") -> bool:
        """
        投稿データCSVをGoogleスプレッドシートにアップロード
        
        Args:
            csv_file_path: CSVファイルのパス
            sheet_name: アップロード先のシート名
            
        Returns:
            bool: アップロード成功の可否
        """
        if not self.service or not self.spreadsheet_id:
            print("ERROR: Google Sheets APIまたはスプレッドシートIDが設定されていません")
            return False
        
        try:
            # CSVデータを読み込み
            df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
            
            # データを2次元リストに変換（ヘッダー含む）
            values = [df.columns.tolist()] + df.values.tolist()
            
            # X投稿自動化用の追加カラムを準備
            enhanced_values = self._prepare_for_auto_posting(values)
            
            # スプレッドシートのシートをクリアして新しいデータを書き込み
            range_name = f"{sheet_name}!A1"
            
            # 既存データをクリア
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:Z"
            ).execute()
            
            # 新しいデータを書き込み
            body = {
                'values': enhanced_values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print(f"SUCCESS: Google Sheetsアップロード成功: {result.get('updatedCells', 0)}セル更新")
            print(f"DATA: データ件数: {len(enhanced_values)-1}件")
            
            # シートの書式設定を適用
            self._format_sheet(sheet_name, len(enhanced_values), len(enhanced_values[0]) if enhanced_values else 0)
            
            return True
            
        except HttpError as e:
            print(f"ERROR: Google Sheets APIエラー: {e}")
            return False
        except Exception as e:
            print(f"ERROR: アップロードエラー: {e}")
            return False
    
    def _prepare_for_auto_posting(self, values: List[List]) -> List[List]:
        """
        X投稿自動化のための追加カラムを準備
        
        Args:
            values: 元のCSVデータ（2次元リスト）
            
        Returns:
            List[List]: 拡張されたデータ
        """
        if not values:
            return values
        
        # ヘッダー行に追加カラムを挿入
        header = values[0]
        enhanced_header = header + [
            '投稿状況', '投稿日時', '投稿URL', 'エラー情報', '手動確認', '備考'
        ]
        
        # データ行に空の値を追加
        enhanced_values = [enhanced_header]
        for row in values[1:]:
            enhanced_row = row + ['未投稿', '', '', '', '要確認', '']
            enhanced_values.append(enhanced_row)
        
        return enhanced_values
    
    def _format_sheet(self, sheet_name: str, rows: int, cols: int):
        """
        スプレッドシートの書式設定
        
        Args:
            sheet_name: シート名
            rows: 行数
            cols: 列数
        """
        try:
            # シートIDを取得
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheet_id = None
            for sheet in sheet_metadata.get('sheets', []):
                if sheet.get('properties', {}).get('title') == sheet_name:
                    sheet_id = sheet.get('properties', {}).get('sheetId')
                    break
            
            if sheet_id is None:
                print(f"WARNING: シート '{sheet_name}' が見つかりません")
                return
            
            # 書式設定のリクエスト
            requests = [
                # ヘッダー行のスタイル設定
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": cols
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                                "textFormat": {"bold": True},
                                "horizontalAlignment": "CENTER"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                    }
                },
                # 列幅の自動調整
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": cols
                        }
                    }
                }
            ]
            
            body = {'requests': requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            print("SUCCESS: スプレッドシート書式設定完了")
            
        except Exception as e:
            print(f"WARNING: 書式設定エラー: {e}")
    
    def upload_schedule_data(self, csv_file_path: str, sheet_name: str = "Schedule") -> bool:
        """
        投稿スケジュールCSVをGoogleスプレッドシートにアップロード
        
        Args:
            csv_file_path: CSVファイルのパス
            sheet_name: アップロード先のシート名
            
        Returns:
            bool: アップロード成功の可否
        """
        return self.upload_posts_data(csv_file_path, sheet_name)
    
    def get_spreadsheet_url(self) -> str:
        """
        GoogleスプレッドシートのURLを取得
        
        Returns:
            str: スプレッドシートのURL
        """
        if self.spreadsheet_id:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"
        return ""


def test_google_sheets_sync():
    """
    Google Sheets同期のテスト
    """
    print("🧪 Google Sheets同期テスト開始")
    print("=" * 50)
    
    # 環境変数チェック
    credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    
    if not credentials_path:
        print("ERROR: GOOGLE_SHEETS_CREDENTIALS_PATH が設定されていません")
        return False
    
    if not spreadsheet_id:
        print("ERROR: GOOGLE_SHEETS_SPREADSHEET_ID が設定されていません")
        return False
    
    # 同期クラスのテスト
    sync = GoogleSheetsSync()
    
    if sync.service:
        print("SUCCESS: Google Sheets API接続テスト成功")
        print(f"📋 スプレッドシートURL: {sync.get_spreadsheet_url()}")
        return True
    else:
        print("ERROR: Google Sheets API接続テスト失敗")
        return False


if __name__ == "__main__":
    test_google_sheets_sync()