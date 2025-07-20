import google.generativeai as genai
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
from modules.data_manager import analyze_recent_themes


class ContentGenerator:
    def __init__(self, api_key: str = None):
        """
        コンテンツ生成クラスの初期化
        """
        if api_key:
            genai.configure(api_key=api_key)
        else:
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Gemini 2.5 Pro モデルを設定
        self.model = genai.GenerativeModel('gemini-2.5-pro')
    
    def generate_cat_post(self, theme: str, day_of_week: str, recent_analysis: Dict = None) -> str:
        """
        猫投稿を生成する（125-140字以内, #猫のあれこれ）
        """
        prompt = f"""
あなたは19年目の猫と犬の救急医療を専門とする獣医師です。
猫を飼っている飼い主さん（高校生～40代が中心）に向けて、X(Twitter)投稿を作成してください。

【重要なルール】
- 文字数: 125-140文字以内（タイトル・本文・ハッシュタグ・絵文字すべて含む）
- 必ず【タイトル】で始める
- 最後は必ず「#猫のあれこれ」で終わる
- 絵文字を4-5個程度使用
- 専門的だが分かりやすい表現
- 温かく親しみやすいトーン

【今回のテーマ】: {theme}
【曜日】: {day_of_week}

【過去の投稿との重複回避】
{f"最近扱ったテーマ: {', '.join(recent_analysis.get('themes', [])[:10])}" if recent_analysis else ""}

【出力形式】
投稿文のみを出力してください。マークダウンや説明文は不要です。
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=300,
                    temperature=0.7,
                )
            )
            
            content = response.text.strip()
            
            # 文字数チェック
            char_count = len(content)
            if char_count < 125 or char_count > 140:
                # 文字数調整を試行
                content = self._adjust_post_length(content, 125, 140, "猫")
            
            return content
            
        except Exception as e:
            print(f"猫投稿生成エラー: {e}")
            return self._fallback_cat_post(theme)
    
    def generate_dog_post(self, theme: str, day_of_week: str, recent_analysis: Dict = None) -> str:
        """
        犬投稿を生成する（125-139字, #獣医が教える犬のはなし）
        """
        
        # 曜日に応じた投稿タイプの決定
        post_type = self._get_dog_post_type(day_of_week)
        
        prompt = f"""
あなたは19年目の犬と猫の救急医療を専門とする獣医師（FP2級も取得）です。
犬を飼っている飼い主さん（高校生～40代が中心）に向けて、X(Twitter)投稿を作成してください。

【重要なルール】
- 文字数: 125-135文字以内（タイトル・本文・ハッシュタグ・絵文字すべて含む）
- 必ず【タイトル】で始める
- 最後は必ず「#獣医が教える犬のはなし」で終わる
- 絵文字を4-5個程度使用
- 専門的だが分かりやすい表現
- やや固めで丁寧な言葉遣い

【今回のテーマ】: {theme}
【曜日・投稿タイプ】: {day_of_week} - {post_type}

【投稿タイプ別の指示】
{self._get_dog_post_instructions(post_type)}

【過去の投稿との重複回避】
{f"最近扱ったテーマ: {', '.join(recent_analysis.get('themes', [])[:10])}" if recent_analysis else ""}

【出力形式】
投稿文のみを出力してください。マークダウンや説明文は不要です。
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=300,
                    temperature=0.7,
                )
            )
            
            content = response.text.strip()
            
            # 文字数チェック
            char_count = len(content)
            if char_count < 125 or char_count > 135:
                content = self._adjust_post_length(content, 125, 135, "犬")
            
            return content
            
        except Exception as e:
            print(f"犬投稿生成エラー: {e}")
            return self._fallback_dog_post(theme, post_type)
    
    def _get_dog_post_type(self, day_of_week: str) -> str:
        """
        曜日に応じた犬投稿のタイプを決定
        """
        type_mapping = {
            '月曜': 'クイズ・質問編',
            '火曜': '回答・解説編', 
            '水曜': 'ケーススタディ・質問編',
            '木曜': '回答・解説編',
            '金曜': '体験談募集・質問募集',
            '土曜': 'お役立ちヒント・小ワザ',
            '日曜': '豆知識・コラム'
        }
        return type_mapping.get(day_of_week, 'お役立ち情報')
    
    def _get_dog_post_instructions(self, post_type: str) -> str:
        """
        投稿タイプ別の具体的な指示
        """
        instructions = {
            'クイズ・質問編': '選択肢形式のクイズを出題。「正解は明日！」で締める。',
            '回答・解説編': '前日のクイズの答えと詳しい解説。なぜその答えなのかを専門的に説明。',
            'ケーススタディ・質問編': '実際にありそうなシナリオを提示し、判断を求める。',
            '体験談募集・質問募集': '「教えてください！」「皆さんはどうですか？」など参加を促す。',
            'お役立ちヒント・小ワザ': 'すぐに実践できる具体的なコツや方法を紹介。',
            '豆知識・コラム': '興味深い犬の生態や、獣医師ならではの知識を紹介。'
        }
        return instructions.get(post_type, '有益な情報を分かりやすく伝える。')
    
    def _adjust_post_length(self, content: str, min_chars: int, max_chars: int, animal_type: str) -> str:
        """
        投稿の文字数を調整
        """
        current_length = len(content)
        
        if current_length > max_chars:
            # 長すぎる場合は短縮
            # まず絵文字以外の部分を調整
            lines = content.split('\n')
            if len(lines) > 1:
                # 本文部分を短縮
                for i in range(1, len(lines)-1):
                    if len(content) <= max_chars:
                        break
                    lines[i] = self._shorten_line(lines[i])
                content = '\n'.join(lines)
        
        elif current_length < min_chars:
            # 短すぎる場合は延長
            # 適切な位置に内容を追加
            content = self._extend_content(content, min_chars, animal_type)
        
        return content[:max_chars]  # 最終的な長さ制限
    
    def _shorten_line(self, line: str) -> str:
        """
        1行を短縮
        """
        # 不要な単語や表現を削除
        line = re.sub(r'とても|非常に|本当に', '', line)
        line = re.sub(r'ぜひ|きっと', '', line)
        line = re.sub(r'　+', '　', line)  # 連続スペースを単一に
        return line.strip()
    
    def _extend_content(self, content: str, target_length: int, animal_type: str) -> str:
        """
        コンテンツを延長
        """
        if animal_type == "猫":
            extensions = ["🐱", "愛猫の", "大切な", "健康な"]
        else:
            extensions = ["🐕", "愛犬の", "大切な", "健康管理を"]
        
        lines = content.split('\n')
        for ext in extensions:
            if len(content) >= target_length:
                break
            # 適切な位置に追加
            if len(lines) > 1:
                lines[1] += ext
                content = '\n'.join(lines)
        
        return content
    
    def _fallback_cat_post(self, theme: str) -> str:
        """
        猫投稿のフォールバック（125-140字）
        """
        return f"【{theme}の基本知識】\n\n愛猫の健康を守るためには、日頃からの観察と早期発見が最も重要です🐱\n\n19年の獣医経験から、猫ちゃんの小さな変化を見逃さないコツをお伝えしています。飼い主さんの愛情と専門知識で、一緒に猫ちゃんの幸せな生活を支えましょう✨\n\n#猫のあれこれ"
    
    def _fallback_dog_post(self, theme: str, post_type: str) -> str:
        """
        犬投稿のフォールバック（125-135字）
        """
        return f"【{theme}の重要ポイント】\n\n愛犬の健康管理は毎日の積み重ねが最も大切です🐕\n\n19年間の救急獣医として、飼い主さんに知っていただきたい基本的なケア方法と予防のコツをお伝えしています。愛犬の幸せで健康な生活をサポートします📚✨\n\n#獣医が教える犬のはなし"
    
    def generate_weekly_content(self, animal_type: str, tweets_df=None) -> List[Dict]:
        """
        1週間分のコンテンツを生成
        """
        from modules.data_manager import get_next_week_themes, analyze_recent_themes
        
        # 過去の投稿分析
        recent_analysis = analyze_recent_themes(tweets_df, animal_type) if tweets_df is not None else None
        
        # 週間テーマの取得
        weekly_themes = get_next_week_themes(animal_type, tweets_df)
        
        days = ['月曜', '火曜', '水曜', '木曜', '金曜', '土曜', '日曜']
        weekly_content = []
        
        for day in days:
            theme = weekly_themes.get(day, ['健康管理'])[0]
            
            if animal_type == '猫':
                post_content = self.generate_cat_post(theme, day, recent_analysis)
            else:
                post_content = self.generate_dog_post(theme, day, recent_analysis)
            
            # 投稿日時の計算（来週の該当曜日）
            today = datetime.now()
            days_ahead = (days.index(day) - today.weekday() + 7) % 7
            if days_ahead == 0:  # 今日が同じ曜日の場合は来週
                days_ahead = 7
            post_date = today + timedelta(days=days_ahead)
            
            weekly_content.append({
                'date': post_date.strftime('%Y-%m-%d'),
                'day': day,
                'animal_type': animal_type,
                'theme': theme,
                'post_text': post_content,
                'character_count': len(post_content),
                'scheduled_time': '07:00' if animal_type == '猫' else '18:00'
            })
        
        return weekly_content


if __name__ == "__main__":
    # テスト実行
    generator = ContentGenerator()
    
    # 猫投稿テスト
    cat_post = generator.generate_cat_post("猫の健康管理", "月曜")
    print(f"猫投稿例({len(cat_post)}文字):")
    print(cat_post)
    print()
    
    # 犬投稿テスト
    dog_post = generator.generate_dog_post("犬の熱中症対策", "月曜")
    print(f"犬投稿例({len(dog_post)}文字):")
    print(dog_post)