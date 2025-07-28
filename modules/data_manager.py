import pandas as pd
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple


def load_and_clean_tweets(filepath: str = "C:\\Users\\souhe\\Desktop\\tweets.js") -> pd.DataFrame:
    """
    tweets.jsファイルを読み込み、分析可能な形式に変換する関数
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # JSONオブジェクトの部分を抽出
        json_str_match = re.search(r'\[.*\]', content, re.DOTALL)
        if not json_str_match:
            raise ValueError("tweets.jsファイルの形式が不正です")
        
        tweets_data = json.loads(json_str_match.group(0))
        
        # データを整理してDataFrameに変換
        processed_tweets = []
        for item in tweets_data:
            tweet = item.get('tweet', {})
            
            # 基本情報の抽出
            tweet_info = {
                'id': tweet.get('id_str', ''),
                'created_at': tweet.get('created_at', ''),
                'full_text': tweet.get('full_text', ''),
                'retweet_count': int(tweet.get('retweet_count', 0)),
                'favorite_count': int(tweet.get('favorite_count', 0)),
                'lang': tweet.get('lang', ''),
            }
            
            # ハッシュタグの抽出
            hashtags = []
            entities = tweet.get('entities', {})
            if 'hashtags' in entities:
                hashtags = [tag['text'] for tag in entities['hashtags']]
            tweet_info['hashtags'] = hashtags
            
            # 猫・犬の分類
            if '#猫のあれこれ' in hashtags:
                tweet_info['animal_type'] = '猫'
            elif '#獣医が教える犬のはなし' in hashtags:
                tweet_info['animal_type'] = '犬'
            else:
                tweet_info['animal_type'] = 'その他'
            
            # 日付の変換
            if tweet_info['created_at']:
                try:
                    # Twitter日付形式をパース
                    dt = datetime.strptime(tweet_info['created_at'], '%a %b %d %H:%M:%S %z %Y')
                    tweet_info['date'] = dt.strftime('%Y-%m-%d')
                    tweet_info['datetime'] = dt
                except:
                    tweet_info['date'] = ''
                    tweet_info['datetime'] = None
            
            processed_tweets.append(tweet_info)
        
        df = pd.DataFrame(processed_tweets)
        
        # 最新順にソート
        if 'datetime' in df.columns:
            df = df.sort_values('datetime', ascending=False)
        
        return df
        
    except Exception as e:
        print(f"tweets.jsファイルの読み込みエラー: {e}")
        return pd.DataFrame()


def analyze_recent_themes(df: pd.DataFrame, animal_type: str, months: int = 3) -> Dict[str, Any]:
    """
    過去の投稿テーマを分析し、重複を避けるための情報を提供
    """
    if df.empty:
        return {'themes': [], 'recent_topics': [], 'seasonal_patterns': {}}
    
    # 指定された動物タイプでフィルタ
    filtered_df = df[df['animal_type'] == animal_type].copy()
    
    if filtered_df.empty:
        return {'themes': [], 'recent_topics': [], 'seasonal_patterns': {}}
    
    # 過去指定月分のデータを抽出
    cutoff_date = datetime.now() - pd.DateOffset(months=months)
    recent_df = filtered_df[pd.to_datetime(filtered_df['date']) >= cutoff_date]
    
    # テーマの抽出（投稿文から）
    recent_topics = []
    for text in recent_df['full_text']:
        if text:
            # 【】で囲まれたタイトル部分を抽出
            title_match = re.search(r'【(.+?)】', text)
            if title_match:
                recent_topics.append(title_match.group(1))
    
    # 季節性パターンの分析
    seasonal_patterns = {}
    if 'datetime' in recent_df.columns:
        for _, row in recent_df.iterrows():
            if row['datetime']:
                month = row['datetime'].month
                if month not in seasonal_patterns:
                    seasonal_patterns[month] = []
                title_match = re.search(r'【(.+?)】', row['full_text'])
                if title_match:
                    seasonal_patterns[month].append(title_match.group(1))
    
    return {
        'themes': list(set(recent_topics)),
        'recent_topics': recent_topics,
        'seasonal_patterns': seasonal_patterns,
        'total_posts': len(recent_df)
    }


# Twitter投稿関連の関数は削除されました（X投稿なし版）


def get_next_week_themes(animal_type: str, tweets_df: pd.DataFrame = None) -> Dict[str, List[str]]:
    """
    過去の投稿を分析して、次週の投稿テーマを提案
    """
    if tweets_df is None:
        tweets_df = load_and_clean_tweets()
    
    analysis = analyze_recent_themes(tweets_df, animal_type)
    recent_themes = set(analysis['themes'])
    
    # 現在の月を取得
    current_month = datetime.now().month
    
    if animal_type == '猫':
        # 猫の基本テーマリスト
        base_themes = [
            '猫の健康管理', '猫の行動学', '猫のグルーミング', '猫の栄養学',
            '猫の病気予防', '猫のストレス管理', '猫の老齢ケア', '猫の応急手当',
            '猫の室内環境', '猫の社会化', '猫の睡眠', '猫の遊び',
            '猫の季節ケア', '猫の体重管理', '猫の歯のケア', '猫の目のケア'
        ]
        
        # 季節に応じたテーマ
        if current_month in [6, 7, 8]:  # 夏
            seasonal_themes = ['熱中症対策', '夏の水分補給', '冷房対策', '夏バテ予防']
        elif current_month in [12, 1, 2]:  # 冬
            seasonal_themes = ['寒さ対策', '乾燥対策', '冬の運動不足', '暖房器具の注意']
        elif current_month in [3, 4, 5]:  # 春
            seasonal_themes = ['換毛期ケア', '花粉対策', '春の健康チェック', 'ワクチン接種']
        else:  # 秋
            seasonal_themes = ['秋の健康管理', '食欲の秋注意', '換毛期対策', '冬支度']
    
    else:  # 犬
        base_themes = [
            '犬の健康管理', '犬の行動学', '犬のしつけ', '犬の栄養学',
            '犬の病気予防', '犬のストレス管理', '犬の老齢ケア', '犬の応急手当',
            '犬の散歩', '犬の社会化', '犬の睡眠', '犬の遊び',
            '犬の季節ケア', '犬の体重管理', '犬の歯のケア', '犬種特集'
        ]
        
        if current_month in [6, 7, 8]:  # 夏
            seasonal_themes = ['熱中症対策', '散歩時間調整', 'プールケア', '夏の皮膚トラブル']
        elif current_month in [12, 1, 2]:  # 冬
            seasonal_themes = ['寒さ対策', '関節ケア', '冬の散歩注意', '室内運動']
        elif current_month in [3, 4, 5]:  # 春
            seasonal_themes = ['狂犬病予防接種', 'フィラリア予防', '春の健康チェック', '換毛期ケア']
        else:  # 秋
            seasonal_themes = ['秋の健康管理', '食欲管理', '運動量調整', 'ワクチン接種']
    
    # 最近使用していないテーマを選出
    available_themes = []
    for theme in base_themes + seasonal_themes:
        if not any(theme in recent for recent in recent_themes):
            available_themes.append(theme)
    
    # 週間スケジュール提案
    if animal_type == '犬':
        # 犬の場合：月曜→火曜、水曜→木曜で同じテーマのクイズ・解答ペア
        weekly_schedule = {
            '月曜': [available_themes[0] if available_themes else '犬の健康管理'],      # クイズ
            '火曜': [available_themes[0] if available_themes else '犬の健康管理'],      # 解答（同じテーマ）
            '水曜': [available_themes[1] if len(available_themes) > 1 else '犬の行動学'], # クイズ
            '木曜': [available_themes[1] if len(available_themes) > 1 else '犬の行動学'], # 解答（同じテーマ）
            '金曜': [available_themes[2] if len(available_themes) > 2 else '犬のしつけ'],
            '土曜': [available_themes[3] if len(available_themes) > 3 else '犬の栄養学'],
            '日曜': [available_themes[4] if len(available_themes) > 4 else '犬の老齢ケア']
        }
    else:
        # 猫の場合：従来通り各曜日異なるテーマ
        weekly_schedule = {
            '月曜': [available_themes[0] if available_themes else '猫の健康管理'],
            '火曜': [available_themes[1] if len(available_themes) > 1 else '猫の行動学'],
            '水曜': [available_themes[2] if len(available_themes) > 2 else '猫のグルーミング'],
            '木曜': [available_themes[3] if len(available_themes) > 3 else '猫の栄養学'],
            '金曜': [available_themes[4] if len(available_themes) > 4 else '猫の病気予防'],
            '土曜': [available_themes[5] if len(available_themes) > 5 else '猫のストレス管理'],
            '日曜': [available_themes[6] if len(available_themes) > 6 else '猫の老齢ケア']
        }
    
    return weekly_schedule


if __name__ == "__main__":
    # テスト実行
    df = load_and_clean_tweets()
    print(f"読み込み完了: {len(df)}件の投稿")
    
    cat_analysis = analyze_recent_themes(df, '猫')
    print(f"猫の最近のテーマ数: {len(cat_analysis['themes'])}")
    
    dog_analysis = analyze_recent_themes(df, '犬')
    print(f"犬の最近のテーマ数: {len(dog_analysis['themes'])}")