import tweepy
import os
from typing import Tuple, Optional
import time
from datetime import datetime


class TwitterPoster:
    def __init__(self, 
                 api_key: str = None,
                 api_secret: str = None,
                 access_token: str = None,
                 access_token_secret: str = None,
                 bearer_token: str = None):
        """
        Twitter APIクライアントの初期化
        """
        self.api_key = api_key or os.getenv('TWITTER_API_KEY')
        self.api_secret = api_secret or os.getenv('TWITTER_API_SECRET')
        self.access_token = access_token or os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = access_token_secret or os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.bearer_token = bearer_token or os.getenv('TWITTER_BEARER_TOKEN')
        
        # Twitter API v2クライアントの初期化
        try:
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            # Twitter API v1.1も必要に応じて初期化（メディアアップロード用）
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
            
            print("Twitter API接続成功")
            
        except Exception as e:
            print(f"Twitter API初期化エラー: {e}")
            self.client = None
            self.api_v1 = None
    
    def test_connection(self) -> bool:
        """
        Twitter API接続テスト
        """
        try:
            if self.client:
                user = self.client.get_me()
                print(f"接続確認成功: @{user.data.username}")
                return True
            else:
                print("Twitter APIクライアントが初期化されていません")
                return False
                
        except Exception as e:
            print(f"接続テストエラー: {e}")
            return False
    
    def post_tweet(self, text: str, media_path: str = None) -> Tuple[bool, Optional[str]]:
        """
        ツイートを投稿
        
        Args:
            text: 投稿テキスト
            media_path: 添付メディアのパス（オプション）
            
        Returns:
            Tuple[bool, Optional[str]]: (成功フラグ, 投稿ID)
        """
        try:
            if not self.client:
                print("Twitter APIクライアントが利用できません")
                return False, None
            
            # 文字数チェック
            if len(text) > 280:
                print(f"投稿文が長すぎます: {len(text)}文字")
                return False, None
            
            media_ids = None
            
            # メディアがある場合はアップロード
            if media_path and os.path.exists(media_path):
                try:
                    media = self.api_v1.media_upload(media_path)
                    media_ids = [media.media_id]
                    print(f"メディアアップロード成功: {media_path}")
                except Exception as e:
                    print(f"メディアアップロードエラー: {e}")
                    # メディアアップロードに失敗してもテキストのみで投稿を試行
            
            # ツイート投稿
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids
            )
            
            if response.data:
                tweet_id = response.data['id']
                print(f"投稿成功! ID: {tweet_id}")
                print(f"投稿内容: {text[:50]}...")
                return True, str(tweet_id)
            else:
                print("投稿に失敗しました（レスポンスが空）")
                return False, None
                
        except tweepy.TooManyRequests:
            print("レート制限に達しました。しばらく待ってから再試行してください。")
            return False, None
            
        except tweepy.Forbidden as e:
            print(f"投稿が禁止されました: {e}")
            return False, None
            
        except tweepy.BadRequest as e:
            print(f"不正なリクエスト: {e}")
            return False, None
            
        except Exception as e:
            print(f"投稿エラー: {e}")
            return False, None
    
    def get_recent_tweets(self, count: int = 10) -> list:
        """
        自分の最近のツイートを取得
        """
        try:
            if not self.client:
                return []
            
            user = self.client.get_me()
            tweets = self.client.get_users_tweets(
                id=user.data.id,
                max_results=count,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            if tweets.data:
                return [
                    {
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at,
                        'retweet_count': tweet.public_metrics['retweet_count'],
                        'like_count': tweet.public_metrics['like_count']
                    }
                    for tweet in tweets.data
                ]
            return []
            
        except Exception as e:
            print(f"ツイート取得エラー: {e}")
            return []
    
    def delete_tweet(self, tweet_id: str) -> bool:
        """
        ツイートを削除
        """
        try:
            if not self.client:
                return False
            
            response = self.client.delete_tweet(tweet_id)
            if response.data and response.data['deleted']:
                print(f"ツイート削除成功: {tweet_id}")
                return True
            else:
                print(f"ツイート削除失敗: {tweet_id}")
                return False
                
        except Exception as e:
            print(f"ツイート削除エラー: {e}")
            return False


# 従来の関数形式のインターフェースも提供
def post_tweet(text: str, media_path: str = None) -> Tuple[bool, Optional[str]]:
    """
    ツイートを投稿する関数（後方互換性のため）
    """
    poster = TwitterPoster()
    return poster.post_tweet(text, media_path)


def test_twitter_connection() -> bool:
    """
    Twitter API接続をテストする関数
    """
    poster = TwitterPoster()
    return poster.test_connection()


if __name__ == "__main__":
    # テスト実行
    poster = TwitterPoster()
    
    # 接続テスト
    if poster.test_connection():
        print("✅ Twitter API接続テスト成功")
        
        # 最近のツイート取得テスト
        recent_tweets = poster.get_recent_tweets(5)
        print(f"✅ 最近のツイート取得: {len(recent_tweets)}件")
        
        # テスト投稿（実際には投稿しない）
        test_text = "【テスト投稿】\n\nVET-Assistant3の動作確認です🤖\n\n#テスト"
        print(f"📝 テスト投稿文例({len(test_text)}文字):")
        print(test_text)
        
        # 実際に投稿する場合は以下のコメントアウトを外す
        # success, tweet_id = poster.post_tweet(test_text)
        # if success:
        #     print(f"✅ テスト投稿成功: {tweet_id}")
        # else:
        #     print("❌ テスト投稿失敗")
    else:
        print("❌ Twitter API接続テスト失敗")