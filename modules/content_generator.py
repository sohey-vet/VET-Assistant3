import google.generativeai as genai
import os
import time
import json
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
            # 環境変数が読み込めない場合の直接設定
            env_key = os.getenv('GEMINI_API_KEY')
            if not env_key:
                env_key = 'AIzaSyBquQQNlpC_YnLoyyRKdo0lIptKMH4x3V8'
            genai.configure(api_key=env_key)
        
        # Gemini 2.5 Pro モデルを設定
        self.model = genai.GenerativeModel('gemini-2.5-pro')
    
    def generate_cat_post(self, theme: str, day_of_week: str, recent_analysis: Dict = None) -> str:
        """
        猫投稿を生成する（125-140字以内, #猫のあれこれ）
        """
        prompt = f"""{theme}の猫投稿130字。【タイトル】#猫のあれこれ。絵文字2個。"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=4000,
                    temperature=0.6,
                )
            )
            
            if response and hasattr(response, 'text') and response.text and response.text.strip():
                content = response.text.strip()
                
                # 不適切な前置きを除去
                content = self._clean_generated_content(content)
                
                # 文字数チェック
                char_count = len(content)
                print(f"SUCCESS: API生成成功: {char_count}文字")
                
                if char_count < 125 or char_count > 140:
                    print(f"WARNING: 文字数範囲外({char_count}文字) - 調整中...")
                    content = self._adjust_post_length(content, 125, 140, "猫")
                    print(f"SUCCESS: 文字数調整完了: {len(content)}文字")
                
                return content
            else:
                # APIレスポンスが無効な場合はエラーとして扱う
                error_msg = "APIから有効なコンテンツが生成されませんでした"
                if response:
                    error_msg += f" - Response: {response}"
                print(f"ERROR: {error_msg}")
                raise Exception(error_msg)
            
        except Exception as e:
            print(f"ERROR: 猫投稿API呼び出し失敗: {e}")
            print("WARNING: API呼び出しが必須です。フォールバック投稿は使用しません。")
            raise Exception(f"猫投稿API生成失敗: {theme} - {e}")
    
    def generate_dog_post(self, theme: str, day_of_week: str, recent_analysis: Dict = None) -> str:
        """
        犬投稿を生成する（125-139字, #獣医が教える犬のはなし）
        """
        
        # 曜日とテーマに応じた投稿タイプの決定
        post_type = self._get_dog_post_type(day_of_week, theme)
        
        prompt = f"""{theme}の犬投稿130字。{post_type}。【タイトル】#獣医が教える犬のはなし。絵文字2個。"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=4000,
                    temperature=0.6,
                )
            )
            
            if response and hasattr(response, 'text') and response.text and response.text.strip():
                content = response.text.strip()
                
                # 不適切な前置きを除去
                content = self._clean_generated_content(content)
                
                # 文字数チェック
                char_count = len(content)
                print(f"SUCCESS: API生成成功: {char_count}文字")
                
                if char_count < 125 or char_count > 135:
                    print(f"WARNING: 文字数範囲外({char_count}文字) - 調整中...")
                    content = self._adjust_post_length(content, 125, 135, "犬")
                    print(f"SUCCESS: 文字数調整完了: {len(content)}文字")
                
                return content
            else:
                # APIレスポンスが無効な場合はエラーとして扱う
                error_msg = "APIから有効なコンテンツが生成されませんでした"
                if response:
                    error_msg += f" - Response: {response}"
                print(f"ERROR: {error_msg}")
                raise Exception(error_msg)
            
        except Exception as e:
            print(f"ERROR: 犬投稿API呼び出し失敗: {e}")
            print("WARNING: API呼び出しが必須です。フォールバック投稿は使用しません。")
            raise Exception(f"犬投稿API生成失敗: {theme} - {e}")
    
    def _get_dog_post_type(self, day_of_week: str, theme: str = None) -> str:
        """
        曜日とテーマに応じた犬投稿のタイプを決定
        月曜→火曜、水曜→木曜でクイズ・解答のペアにする
        """
        type_mapping = {
            '月曜': 'クイズ・質問編',
            '火曜': '回答・解説編',  # 月曜のクイズに対する解答
            '水曜': 'クイズ・質問編', 
            '木曜': '回答・解説編',  # 水曜のクイズに対する解答
            '金曜': '体験談募集・質問募集',
            '土曜': 'お役立ちヒント・小ワザ',
            '日曜': '豆知識・コラム'
        }
        return type_mapping.get(day_of_week, 'お役立ち情報')
    
    def _get_dog_post_instructions(self, post_type: str, theme: str = None) -> str:
        """
        投稿タイプ別の具体的な指示
        """
        instructions = {
            'クイズ・質問編': f'{theme}に関する選択肢形式のクイズを出題。「正解は明日お伝えします！」で締める。',
            '回答・解説編': f'{theme}に関する前日のクイズの答えと詳しい解説。なぜその答えなのかを専門的に説明。',
            'ケーススタディ・質問編': f'{theme}に関する実際にありそうなシナリオを提示し、判断を求める。',
            '体験談募集・質問募集': f'{theme}について「教えてください！」「皆さんはどうですか？」など参加を促す。',
            'お役立ちヒント・小ワザ': f'{theme}についてすぐに実践できる具体的なコツや方法を紹介。',
            '豆知識・コラム': f'{theme}に関する興味深い犬の生態や、獣医師ならではの知識を紹介。'
        }
        return instructions.get(post_type, f'{theme}について有益な情報を分かりやすく伝える。')
    
    def _clean_generated_content(self, content: str) -> str:
        """
        生成されたコンテンツから不適切な前置きや文字化けを除去
        """
        # 不適切な前置きパターンを除去
        unwanted_patterns = [
            r"はい、承知いたしました。[^。]*。\s*",
            r"[^。]*について[^。]*投稿を作成します。\s*",
            r"以下の投稿を作成いたします。\s*",
            r"投稿文を作成します。\s*",
        ]
        
        for pattern in unwanted_patterns:
            content = re.sub(pattern, "", content)
        
        # 文字化けパターンを除去（絵文字の後に続く不適切な文字列）
        content = re.sub(r"🐱愛猫の[^#]*", "", content)
        content = re.sub(r"🐕愛犬の[^#]*", "", content)
        
        # 改行の正規化
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = content.strip()
        
        return content
    
    def _adjust_post_length(self, content: str, min_chars: int, max_chars: int, animal_type: str) -> str:
        """
        投稿の文字数を調整（確実な制限遵守を保証）
        """
        current_length = len(content)
        max_attempts = 5  # 無限ループ防止
        
        for attempt in range(max_attempts):
            current_length = len(content)
            
            if current_length > max_chars:
                # 長すぎる場合は段階的短縮
                content = self._force_shorten_to_limit(content, max_chars)
                print(f"ADJUST: 短縮実行 試行{attempt+1}: {len(content)}文字")
                
            elif current_length < min_chars:
                # 短すぎる場合は延長
                content = self._extend_content(content, min_chars, animal_type)
                print(f"ADJUST: 延長実行 試行{attempt+1}: {len(content)}文字")
                
            else:
                # 適正範囲に到達
                print(f"ADJUST: 調整完了 {current_length}文字 (範囲: {min_chars}-{max_chars})")
                break
        
        # 最終確認: まだ範囲外の場合は強制修正
        final_length = len(content)
        if final_length > max_chars:
            print(f"WARNING: 最終強制短縮 {final_length}文字 → {max_chars}文字")
            content = self._emergency_truncate(content, max_chars)
        elif final_length < min_chars:
            print(f"WARNING: 最終強制延長 {final_length}文字 → {min_chars}文字")
            content = self._emergency_extend(content, min_chars, animal_type)
        
        return content
    
    def _shorten_content(self, content: str, target_length: int) -> str:
        """
        コンテンツを指定長まで短縮
        """
        if len(content) <= target_length:
            return content
        
        # 不要な表現を削除
        content = re.sub(r'とても|非常に|本当に|きっと|ぜひ', '', content)
        content = re.sub(r'　+', '　', content)  # 連続スペースを単一に
        content = re.sub(r'\s+', ' ', content)  # 連続空白を単一に
        
        # まだ長い場合は文章を短縮
        if len(content) > target_length:
            sentences = content.split('。')
            result = ""
            for sentence in sentences:
                if len(result + sentence + '。') <= target_length:
                    result += sentence + '。'
                else:
                    break
            content = result.rstrip('。')
        
        return content.strip()
    
    def _force_shorten_to_limit(self, content: str, max_chars: int) -> str:
        """
        強制的に指定文字数まで短縮（確実な制限遵守）
        """
        if len(content) <= max_chars:
            return content
        
        # ハッシュタグを保護
        if "#" in content:
            main_content, hashtag = content.rsplit('#', 1)
            hashtag = '#' + hashtag
            
            # 改行を考慮した利用可能文字数を計算
            newline_chars = content.count('\n')
            available_chars = max_chars - len(hashtag) - newline_chars
            
            # メインコンテンツを段階的に短縮
            main_content = self._shorten_content(main_content, available_chars)
            
            # 再構築
            if '\n' in content:
                content = main_content + '\n' + hashtag
            else:
                content = main_content + hashtag
        else:
            # ハッシュタグがない場合は単純に切り詰め
            content = content[:max_chars]
        
        # まだ長い場合は強制切り詰め
        if len(content) > max_chars:
            content = content[:max_chars]
        
        return content.rstrip()
    
    def _emergency_truncate(self, content: str, max_chars: int) -> str:
        """
        緊急時の強制切り詰め
        """
        if len(content) <= max_chars:
            return content
        
        # ハッシュタグを最優先で保護
        if "#" in content:
            parts = content.rsplit('#', 1)
            if len(parts) == 2:
                main_content, hashtag = parts
                hashtag = '#' + hashtag
                
                # ハッシュタグ分を確保
                available_chars = max_chars - len(hashtag)
                
                if available_chars > 0:
                    main_content = main_content[:available_chars].rstrip()
                    return main_content + hashtag
                else:
                    # ハッシュタグだけでも制限を超える場合
                    return hashtag[:max_chars]
        
        # 単純切り詰め
        return content[:max_chars]
    
    def _emergency_extend(self, content: str, min_chars: int, animal_type: str) -> str:
        """
        緊急時の強制延長
        """
        current_length = len(content)
        if current_length >= min_chars:
            return content
        
        needed_chars = min_chars - current_length
        
        # 適切な延長文字列
        if animal_type == "猫":
            padding = "愛猫の健康管理は大切です。" * (needed_chars // 12 + 1)
        else:
            padding = "愛犬の健康管理は重要です。" * (needed_chars // 12 + 1)
        
        # ハッシュタグの前に挿入
        if "#" in content:
            main_content, hashtag = content.rsplit('#', 1)
            hashtag = '#' + hashtag
            result = main_content + padding[:needed_chars] + hashtag
        else:
            result = content + padding[:needed_chars]
        
        return result
    
    def _extend_content(self, content: str, target_length: int, animal_type: str) -> str:
        """
        コンテンツを延長
        """
        current_length = len(content)
        if current_length >= target_length:
            return content
        
        # ハッシュタグを分離
        if "#" in content:
            main_content, hashtag = content.rsplit('#', 1)
            hashtag = '#' + hashtag
        else:
            main_content = content
            hashtag = ""
        
        # 延長用フレーズ
        if animal_type == "猫":
            extensions = [
                "愛猫の健康を第一に考えて",
                "日々の観察が重要です",
                "気になることがあれば獣医師に相談を",
            ]
        else:
            extensions = [
                "愛犬の健康管理は飼い主の責任です",
                "日常的なケアが病気予防に繋がります",
                "早期発見・早期治療が大切",
            ]
        
        # 適切な延長フレーズを追加
        for ext in extensions:
            if hashtag:
                test_content = main_content + ext + "\n" + hashtag
            else:
                test_content = main_content + ext
                
            if len(test_content) >= target_length:
                main_content += ext
                break
        
        final_content = main_content + ("\n" + hashtag if hashtag else "")
        
        # まだ短い場合は、追加のパディング文字を挿入
        while len(final_content) < target_length:
            if hashtag:
                # 現在の不足文字数を計算
                needed_chars = target_length - len(final_content)
                
                # 長い補完テキスト
                long_padding = "。飼い主さんの愛情深い観察と日々のケアが、愛犬・愛猫の健康を守る最も大切なポイントです。小さな変化に気づいてあげることで、病気の早期発見と予防に繋がります。定期的な健康チェックと適切な栄養管理で、大切な家族の健康を維持しましょう。"
                
                # 必要な分だけテキストを追加
                main_content += long_padding[:needed_chars]
                final_content = main_content + "\n" + hashtag
                break
            else:
                # ハッシュタグがない場合
                needed_chars = target_length - len(final_content)
                padding = "。飼い主さんの観察が重要です。" * (needed_chars // 15 + 1)
                final_content += padding[:needed_chars]
                break
        
        return final_content
    
    def _fallback_cat_post(self, theme: str) -> str:
        """
        猫投稿のフォールバック（125-140字）- テーマ別具体的内容
        """
        cat_posts = {
            '猫の健康管理': "【愛猫の健康チェックポイント】\n毎日の食事量・水分摂取・排尿回数をチェック🐱\n\nトイレの砂の固まり方で脱水がわかります💧毛艶・目の輝き・鼻の湿り気も重要なサイン✨\n\n些細な変化に気づけるのは飼い主さんだけ。早期発見で猫ちゃんを守りましょう🩺\n#猫のあれこれ",
            '猫の行動学': "【猫の鳴き声の意味を知ろう】\n短い「ニャッ」は挨拶、長い「ニャーン」は要求、「ゴロゴロ」は安心のサイン🐱\n\nしっぽの動きも重要で、ピンと立てば嬉しい、バタバタは興奮状態💫\n\n愛猫の気持ちを理解して、より深い絆を築きませんか❤️\n#猫のあれこれ",
            '猫のグルーミング': "【猫のブラッシングの正しい方法】\n毛の流れに沿って優しくブラッシング🐱\n長毛種は毎日、短毛種は週2-3回が目安✨\n\n耳の後ろ・脇・お腹は毛玉ができやすいポイント💡\n嫌がる子は短時間から慣らして。スキンシップにもなりますよ😊\n#猫のあれこれ",
            '猫の栄養学': "【猫に必要な栄養素とは？】\n猫は完全肉食動物なのでタンパク質が最重要🐱\nタウリン不足は心筋症の原因に💔\n\n年齢別フードを選び、おやつは1日のカロリーの10%以内に✨\n人間の食べ物は塩分過多で危険。愛猫専用フードで健康維持を🍽️\n#猫のあれこれ",
            '猫の病気予防': "【猫の予防接種スケジュール】\n\n子猫：8・12・16週齢で3回接種🐱成猫：年1回の追加接種が基本💉混合ワクチンで猫風邪・パルボウイルスを予防✨室内猫でも接種推奨。ワクチン前後は安静に過ごし、体調変化があれば即連絡を📞\n\n#猫のあれこれ",
            '猫のストレス管理': "【猫のストレスサインを見逃すな】\n\n食欲不振・隠れる・過度なグルーミング・トイレの失敗は要注意🐱引っ越し・新しいペット・来客がストレス原因に💦安心できる隠れ場所と一定のルーティンが大切✨フェロモン製品も効果的です🌿\n\n#猫のあれこれ",
            '猫の老齢ケア': "【シニア猫の健康管理ポイント】\n\n7歳以上は年2回の健康診断を🐱腎臓・甲状腺の数値チェックが重要💡段差を減らし、トイレは浅めに変更✨食事は消化の良いシニア用フードへ🍽️関節痛のサインは動きの鈍さ。早めの対策で快適な老後を😊\n\n#猫のあれこれ"
        }
        return cat_posts.get(theme, cat_posts['猫の健康管理'])
    
    def _fallback_dog_post(self, theme: str, post_type: str, day_of_week: str = '月曜') -> str:
        """
        犬投稿のフォールバック（125-135字）
        """
        if post_type == 'クイズ・質問編':
            dog_quiz = {
                '犬の健康管理': "【犬の健康管理クイズ】\n愛犬の健康状態を見極めるポイントは？🐕\n\nA: 食欲と元気さ\nB: 鼻の湿り具合\nC: 歯茎の色\n\n実は全て重要なサインです💡正解は明日お伝えします！\n#獣医が教える犬のはなし",
                '犬の行動学': "【犬の行動学クイズ】\n\n犬が飼い主の顔を舐める行動の意味は？🐕\n\nA: 愛情表現\nB: 塩分補給\nC: 順位確認\n\n実は複数の意味があります💡皆さんはどれだと思いますか？正解は明日お伝えします！\n\n#獣医が教える犬のはなし",
                '犬のしつけ': "【犬のしつけクイズ】\n\n散歩で引っ張る犬への対処法は？🐕\n\nA: 強く引き戻す\nB: 立ち止まって待つ\nC: おやつで気を引く\n\n正しい方法で快適な散歩を💪皆さんはどれだと思いますか？正解は明日お伝えします！\n\n#獣医が教える犬のはなし"
            }
            return dog_quiz.get(theme, dog_quiz['犬の健康管理'])
        elif post_type == '回答・解説編':
            # 前日のクイズに対する正しい解答を提供
            return self._get_previous_day_quiz_answer(day_of_week, theme)
        elif post_type == 'ケーススタディ・質問編':
            return f"【{theme}のケース】\n\n散歩中に愛犬が突然立ち止まって動かなくなりました🐕\n\nこの時、飼い主さんはどう対応すべきでしょうか？皆さんならどうしますか？経験談もお聞かせください✨\n\n#獣医が教える犬のはなし"
        elif post_type == '体験談募集・質問募集':
            return f"【{theme}の体験談募集】\n\n愛犬の{theme}について、皆さんの体験談を教えてください🐕\n\n「うちの子はこんな症状が...」「こんな時どうすれば？」など、お気軽にコメントください。獣医師としてお答えします💡\n\n#獣医が教える犬のはなし"
        elif post_type == 'お役立ちヒント・小ワザ':
            return f"【{theme}の小ワザ】\n\n愛犬の{theme}でお困りの飼い主さんへ🐕\n\n獣医師としてお伝えできる、すぐに実践できる簡単なコツをご紹介します。明日から試してみてください✨\n\n#獣医が教える犬のはなし"
        else:  # 豆知識・コラム
            dog_trivia = {
                '犬の老齢ケア': "【犬の老齢ケア・豆知識】\n\nシニア犬の「認知症」は意外と多く、夜鳴き・徘徊・トイレの失敗が典型的症状🐕👴\n\n日光浴・規則正しい生活・適度な運動が予防に効果的☀️早期発見で進行を遅らせることも可能。愛犬の変化を見逃さないで💡\n\n#獣医が教える犬のはなし",
                '犬の栄養学': "【犬の栄養学・豆知識】\n\n犬は「甘味」を感じられるが、人間の1/6程度の感度🐕🍯\n\n進化の過程で肉食に特化したため、炭水化物への反応が低下💡だからこそタンパク質が重要で、糖分の与えすぎは肥満の原因にWARNING:適切な食事で健康維持を✨\n\n#獣医が教える犬のはなし"
            }
            return dog_trivia.get(theme, dog_trivia['犬の老齢ケア'])
    
    def _get_previous_day_quiz_answer(self, current_day: str, theme: str = None) -> str:
        """
        前日のクイズに対する正確な解答を提供（テーマに基づく）
        """
        if current_day == '火曜':  # 月曜のクイズに対する解答
            if theme == '犬の健康管理':
                return "【昨日のクイズ解答】\n愛犬の健康状態を見極めるポイント、正解は「全て重要」でした🎯\n\n食欲・元気さは基本、鼻の湿り具合で体調確認、歯茎の色で血行状態がわかります💡日々の観察が早期発見に繋がります🐕\n#獣医が教える犬のはなし"
            else:
                return f"【昨日のクイズ解答】\n{theme}に関するクイズの正解をお伝えします🎯\n\n獣医師の専門知識に基づいた詳しい解説で、愛犬の健康管理に役立つ情報をお届けします💡\n#獣医が教える犬のはなし"
        elif current_day == '木曜':  # 水曜のクイズに対する解答  
            if theme == '犬の行動学':
                return "【昨日のクイズの答え🎯】\n正解はB「あくびをする」でした！\n\nあくびは眠い時だけでなく、ストレスや緊張を感じた時の「カーミングシグナル」です。自分や相手を落ち着かせようとする行動。愛犬がどんな場面であくびをするか観察してみてくださいね🐕💡\n#獣医が教える犬のはなし"
            else:
                return f"【昨日のクイズ解答】\n{theme}に関するクイズの正解をお伝えします🎯\n\n獣医師の専門知識に基づいた詳しい解説で、愛犬の健康管理に役立つ情報をお届けします💡\n#獣医が教える犬のはなし"
        else:
            return f"【昨日のクイズ解答】\n{theme}に関する正解はBでした🎯\n\n獣医師として、この理由は愛犬の健康に直結する重要なポイントです。詳しい解説で飼い主さんの知識向上をサポートします📚\n#獣医が教える犬のはなし"
    
    def generate_weekly_content(self, animal_type: str, tweets_df=None) -> List[Dict]:
        """
        構造化プロンプトを使用して、1週間分のコンテンツを一度に生成します。
        """
        print(f"\nINFO: 構造化プロンプトによる週間コンテンツ一括生成を開始します...")
        
        # 猫と犬のテーマを決定
        cat_themes = self._determine_weekly_themes('猫', tweets_df)
        dog_themes = self._determine_weekly_themes('犬', tweets_df)

        # モデルに渡すためのテーマリストを作成
        request_data = {
            "cat_themes": [{"day": day, "theme": theme} for day, theme in zip(["月曜", "火曜", "水曜", "木曜", "金曜", "土曜", "日曜"], cat_themes)],
            "dog_themes": [{"day": day, "theme": theme} for day, theme in zip(["月曜", "火曜", "水曜", "木曜", "金曜", "土曜", "日曜"], dog_themes)]
        }
        
        # トークン効率の良いJSON形式でテーマを文字列化
        themes_json_string = json.dumps(request_data, ensure_ascii=False)

        prompt = f"""あなたは救急を専門とする19年目の獣医師です。猫と犬の1週間分のX投稿を生成してください。

# 投稿ルール（厳守）
- 猫: 125～140字厳守「【タイトル】\\n本文\\n\\n#猫のあれこれ」絵文字2個
- 犬: 125～135字厳守「【タイトル】\\n本文\\n\\n#獣医が教える犬のはなし」絵文字2個
- 文字数超過は絶対禁止
- スマホで読みやすいように自然な改行を入れる

# 重要：クイズ・回答ペアの厳格な指示
**犬の投稿について（最重要）:**
- 月曜: クイズを出題「【○○クイズ】質問文？ A.選択肢1 B.選択肢2 C.選択肢3 答えは明日！」
- 火曜: 月曜のクイズに対する正確な回答「【昨日のクイズの答え】正解はA『選択肢1』でした！理由の解説」
- 水曜: 新しいクイズを出題「【○○クイズ】質問文？ A.選択肢1 B.選択肢2 C.選択肢3 答えは明日！」  
- 木曜: 水曜のクイズに対する正確な回答「【昨日のクイズの答え】正解はB『選択肢2』でした！理由の解説」

**猫の投稿について:**
- 月曜: クイズを出題
- 火曜: 月曜のクイズに対する正確な回答
- 水曜-日曜: テーマに沿った情報提供

# テーマ: {themes_json_string}

# 必須：クイズ・回答の連続性確保
月曜→火曜、水曜→木曜のクイズ・回答は完全に対応させること。選択肢と正解を絶対に一致させる。

# 出力（JSON形式のみ）:
{{"cat_posts":[{{"day":"月曜","post":"投稿文"}},{{"day":"火曜","post":"投稿文"}},{{"day":"水曜","post":"投稿文"}},{{"day":"木曜","post":"投稿文"}},{{"day":"金曜","post":"投稿文"}},{{"day":"土曜","post":"投稿文"}},{{"day":"日曜","post":"投稿文"}}],"dog_posts":[{{"day":"月曜","post":"投稿文"}},{{"day":"火曜","post":"投稿文"}},{{"day":"水曜","post":"投稿文"}},{{"day":"木曜","post":"投稿文"}},{{"day":"金曜","post":"投稿文"}},{{"day":"土曜","post":"投稿文"}},{{"day":"日曜","post":"投稿文"}}]}}"""

        # 最大3回まで再試行
        for attempt in range(3):
            try:
                print(f"INFO: Gemini APIにリクエストを送信します... (試行 {attempt + 1}/3)")
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=8192, 
                        temperature=0.7 
                    )
                )

                # レスポンスからJSON部分を抽出
                match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if not match:
                    print(f"ERROR: レスポンスから有効なJSONが見つかりませんでした (試行 {attempt + 1})。")
                    if attempt < 2:
                        print("INFO: 再試行します...")
                        time.sleep(2)
                        continue
                    else:
                        print("ERROR: 最大試行回数に達しました。フォールバック生成を開始します。")
                        return self._generate_fallback_weekly_content(animal_type, cat_themes if animal_type == '猫' else dog_themes)

                json_text = match.group(0)
                try:
                    generated_data = json.loads(json_text)
                except json.JSONDecodeError as e:
                    print(f"ERROR: JSONパースエラー (試行 {attempt + 1}): {e}")
                    if attempt < 2:
                        print("INFO: 再試行します...")
                        time.sleep(2)
                        continue
                    else:
                        print("ERROR: 最大試行回数に達しました。フォールバック生成を開始します。")
                        return self._generate_fallback_weekly_content(animal_type, cat_themes if animal_type == '猫' else dog_themes)
                
                # 指定された動物タイプのコンテンツを返す
                if animal_type == '猫':
                    content = self._format_output(generated_data.get('cat_posts', []), cat_themes, animal_type)
                else:
                    content = self._format_output(generated_data.get('dog_posts', []), dog_themes, animal_type)
                
                # 文字数チェックと調整を最優先で実行
                content = self._validate_and_adjust_content(content, animal_type)
                
                # 調整後の厳格な品質チェック
                if self._check_content_quality_strict(content, animal_type):
                    print("SUCCESS: 週間コンテンツの一括生成に成功しました。")
                    return content
                else:
                    print(f"WARNING: 調整後も品質基準未達 (試行 {attempt + 1})。")
                    if attempt < 2:
                        print("INFO: 再試行します...")
                        time.sleep(2)
                        continue
                    else:
                        print("ERROR: 最大試行回数に達しました。フォールバック生成を開始します。")
                        return self._generate_fallback_weekly_content(animal_type, cat_themes if animal_type == '猫' else dog_themes)

            except Exception as e:
                print(f"ERROR: 週間コンテンツの生成中にエラーが発生しました (試行 {attempt + 1}): {e}")
                if attempt < 2:
                    print("INFO: 再試行します...")
                    time.sleep(2)
                    continue
                else:
                    print("ERROR: 最大試行回数に達しました。フォールバック生成を開始します。")
                    return self._generate_fallback_weekly_content(animal_type, cat_themes if animal_type == '猫' else dog_themes)

    def _determine_weekly_themes(self, animal_type: str, tweets_df=None) -> List[str]:
        """
        1週間分のテーマを決定する
        """
        from modules.data_manager import get_next_week_themes
        
        weekly_themes = get_next_week_themes(animal_type, tweets_df)
        days = ['月曜', '火曜', '水曜', '木曜', '金曜', '土曜', '日曜']
        
        themes = []
        for day in days:
            theme = weekly_themes.get(day, ['健康管理'])[0]
            themes.append(theme)
        
        return themes

    def _format_output(self, posts_data: List[Dict], themes: List[str], animal_type: str) -> List[Dict]:
        """
        APIからの出力を既存のデータ構造に変換するヘルパー関数
        """
        content_list = []
        days = ['月曜', '火曜', '水曜', '木曜', '金曜', '土曜', '日曜']
        
        for i, post_item in enumerate(posts_data):
            # 投稿日時の計算（今週または来週の該当曜日）
            today = datetime.now()
            current_weekday = today.weekday()  # 月曜=0, 日曜=6
            target_weekday = i  # 月曜=0, 火曜=1, ..., 日曜=6
            
            # 今週の月曜日を基準とする
            this_monday = today - timedelta(days=current_weekday)
            post_date = this_monday + timedelta(days=target_weekday)
            
            # もし計算した日付が過去の場合は来週にする
            if post_date < today:
                post_date += timedelta(days=7)
            
            content_list.append({
                'date': post_date.strftime('%Y-%m-%d'),
                'day': days[i],
                'animal_type': animal_type,
                'theme': themes[i] if i < len(themes) else '健康管理',
                'post_text': post_item.get('post', ''),
                'character_count': len(post_item.get('post', '')),
                'scheduled_time': '07:00' if animal_type == '猫' else '18:00'
            })
        
        return content_list

    def _validate_and_adjust_content(self, content_list: List[Dict], animal_type: str) -> List[Dict]:
        """
        生成されたコンテンツの文字数を検証・調整し、スマホ用改行を追加する
        """
        min_chars = 125
        max_chars = 140 if animal_type == '猫' else 135
        
        for item in content_list:
            post_text = item['post_text']
            char_count = len(post_text)
            
            # 生成失敗チェック（極端に短い場合）
            if char_count < 30:
                print(f"ERROR: {item['day']} 生成失敗 ({char_count}文字) - フォールバック使用")
                post_text = self._get_fallback_content(item['theme'], item['day'], animal_type)
                char_count = len(post_text)
                print(f"INFO: フォールバック適用後: {char_count}文字")
            
            # 文字数調整
            if char_count < min_chars or char_count > max_chars:
                print(f"WARNING: {item['day']} 文字数範囲外({char_count}文字) - 調整中...")
                adjusted_text = self._adjust_post_length(post_text, min_chars, max_chars, animal_type)
                post_text = adjusted_text
                
                # 調整後も範囲外の場合は強制修正
                final_count = len(adjusted_text)
                if final_count < min_chars or final_count > max_chars:
                    print(f"ERROR: 調整失敗 ({final_count}文字) - 強制修正実行")
                    post_text = self._force_fix_content(adjusted_text, min_chars, max_chars, animal_type, item['theme'])
                
                print(f"SUCCESS: {item['day']} 文字数調整完了: {len(post_text)}文字")
            else:
                print(f"SUCCESS: {item['day']} 文字数OK: {char_count}文字")
            
            # スマホ用自然改行を追加
            formatted_text = self._format_for_mobile(post_text)
            item['post_text'] = formatted_text
            item['character_count'] = len(formatted_text)
            
            # 最終確認
            final_chars = len(formatted_text)
            if final_chars < min_chars or final_chars > max_chars:
                print(f"CRITICAL: {item['day']} 最終文字数範囲外 ({final_chars}文字) - 緊急修正")
                item['post_text'] = self._emergency_fix(formatted_text, min_chars, max_chars, animal_type)
                item['character_count'] = len(item['post_text'])
        
        return content_list

    def _format_for_mobile(self, post_text: str) -> str:
        """
        スマホで読みやすいように自然な改行を追加する
        """
        # ハッシュタグを分離
        if "#" in post_text:
            main_content, hashtag = post_text.rsplit('#', 1)
            hashtag = '#' + hashtag
        else:
            main_content = post_text
            hashtag = ""
        
        # 【タイトル】を分離
        if main_content.startswith('【') and '】' in main_content:
            title_end = main_content.find('】') + 1
            title = main_content[:title_end]
            body = main_content[title_end:].strip()
        else:
            title = ""
            body = main_content.strip()
        
        # 本文に自然な改行を追加
        # 句読点や区切りで改行を入れる
        formatted_body = body
        
        # 長い文章を適度な位置で改行
        if len(body) > 40:
            # 「。」「！」「？」の後に改行を追加（ただし最後ではない場合）
            formatted_body = re.sub(r'([。！？])(?!$)', r'\1\n', body)
            
            # 「、」の後に適度に改行を追加（40文字以上の場合）
            lines = formatted_body.split('\n')
            final_lines = []
            for line in lines:
                if len(line) > 40:
                    # 「、」で分割して適度な長さにする
                    parts = line.split('、')
                    current_line = ""
                    for part in parts:
                        if len(current_line + part + '、') <= 40:
                            current_line += part + '、'
                        else:
                            if current_line:
                                final_lines.append(current_line.rstrip('、'))
                            current_line = part + '、'
                    if current_line:
                        final_lines.append(current_line.rstrip('、'))
                else:
                    final_lines.append(line)
            formatted_body = '\n'.join(final_lines)
        
        # 最終的な組み立て
        result = ""
        if title:
            result += title + "\n"
        if formatted_body:
            result += formatted_body
        if hashtag:
            result += "\n\n" + hashtag
        
        return result.strip()

    def _get_fallback_content(self, theme: str, day: str, animal_type: str) -> str:
        """
        生成失敗時のフォールバックコンテンツを提供
        """
        post_type = self._get_dog_post_type(day) if animal_type == '犬' else '一般情報'
        
        if animal_type == '猫':
            return self._fallback_cat_post(theme)
        else:
            return self._fallback_dog_post(theme, post_type, day)
    
    def _force_fix_content(self, content: str, min_chars: int, max_chars: int, animal_type: str, theme: str) -> str:
        """
        文字数調整が失敗した場合の強制修正
        """
        current_length = len(content)
        
        if current_length < min_chars:
            # 短すぎる場合: 基本テンプレートで再構築
            if animal_type == '猫':
                base_content = f"【{theme}のポイント】\n愛猫の健康管理で大切なことは、日々の観察と適切なケアです。小さな変化に気づくことで、病気の早期発見につながります。\n\n#猫のあれこれ"
            else:
                base_content = f"【{theme}のコツ】\n愛犬の健康維持には、飼い主さんの正しい知識と日常的なケアが欠かせません。獣医師として大切なポイントをお伝えします。\n\n#獣医が教える犬のはなし"
            
            # 文字数調整
            if len(base_content) < min_chars:
                padding = "定期的な健康チェックと適切な栄養管理で、大切な家族の健康を守りましょう。"
                base_content = base_content.replace('\n\n#', f"。{padding}\n\n#")
            
            content = base_content
        
        # まだ範囲外の場合は切り詰め
        if len(content) > max_chars:
            # ハッシュタグを保護して切り詰め
            if "#" in content:
                main_part, hashtag = content.rsplit('#', 1)
                hashtag = '#' + hashtag
                available_chars = max_chars - len(hashtag) - 1
                main_part = main_part[:available_chars].rstrip()
                content = main_part + '\n' + hashtag
            else:
                content = content[:max_chars]
        
        return content
    
    def _emergency_fix(self, content: str, min_chars: int, max_chars: int, animal_type: str) -> str:
        """
        最終手段の緊急修正
        """
        current_length = len(content)
        
        if current_length < min_chars:
            # 絶対に満たすべき最低文字数を確保
            if animal_type == '猫':
                emergency_content = f"【重要なお知らせ】\n愛猫の健康管理について、獣医師として大切なポイントをお伝えします。日々の観察と適切なケアで、猫ちゃんの健康を守りましょう。定期的な健康チェックをお忘れなく。\n\n#猫のあれこれ"
            else:
                emergency_content = f"【重要なお知らせ】\n愛犬の健康管理について、獣医師として大切なポイントをお伝えします。日々の観察と適切なケアで、わんちゃんの健康を守りましょう。定期的な健康チェックをお忘れなく。\n\n#獣医が教える犬のはなし"
            
            # 必要に応じて文字数調整
            while len(emergency_content) < min_chars:
                emergency_content = emergency_content.replace('健康を守りましょう。', '健康を守りましょう。早期発見・早期治療が重要です。')
                break
            
            content = emergency_content
        
        # 最大文字数を超えている場合は切り詰め
        if len(content) > max_chars:
            if "#" in content:
                main_part, hashtag = content.rsplit('#', 1)
                hashtag = '#' + hashtag
                available_chars = max_chars - len(hashtag) - 1
                main_part = main_part[:available_chars].rstrip()
                content = main_part + '\n' + hashtag
            else:
                content = content[:max_chars]
        
        return content

    def _check_content_quality(self, content_list: List[Dict]) -> bool:
        """
        生成されたコンテンツの品質をチェック（クイズ・回答ペアの一貫性含む）
        """
        if not content_list or len(content_list) != 7:
            print("ERROR: コンテンツ数が不正です")
            return False
        
        for item in content_list:
            post_text = item.get('post_text', '')
            if not post_text or len(post_text) < 20:
                print(f"ERROR: {item.get('day', '不明')}の投稿が短すぎます: {len(post_text)}文字")
                return False
            
            # ハッシュタグの存在確認
            if '#' not in post_text:
                print(f"ERROR: {item.get('day', '不明')}の投稿にハッシュタグがありません")
                return False
        
        # 犬のクイズ・回答ペアの一貫性チェック
        if content_list[0].get('animal_type') == '犬':
            if not self._validate_quiz_answer_pairs(content_list):
                print("ERROR: 犬のクイズ・回答ペアに不整合があります")
                return False
        
        print("SUCCESS: コンテンツ品質チェック合格")
        return True
    
    def _check_content_quality_strict(self, content_list: List[Dict], animal_type: str) -> bool:
        """
        調整後の厳格な品質チェック（文字数制限を最優先で確認）
        """
        if not content_list or len(content_list) != 7:
            print("ERROR: コンテンツ数が不正です")
            return False
        
        min_chars = 125
        max_chars = 140 if animal_type == '猫' else 135
        
        violations = []
        
        for item in content_list:
            post_text = item.get('post_text', '')
            char_count = len(post_text)
            day = item.get('day', '不明')
            
            # 基本チェック
            if not post_text or char_count < 20:
                violations.append(f"{day}: 投稿が短すぎます ({char_count}文字)")
                continue
            
            # ハッシュタグチェック
            if '#' not in post_text:
                violations.append(f"{day}: ハッシュタグがありません")
                continue
            
            # 文字数制限チェック（最重要）
            if char_count < min_chars:
                violations.append(f"{day}: 文字数不足 ({char_count}文字 < {min_chars}文字)")
            elif char_count > max_chars:
                violations.append(f"{day}: 文字数超過 ({char_count}文字 > {max_chars}文字)")
            
            # 実際の文字数を再確認
            actual_char_count = len(post_text)
            if actual_char_count != char_count:
                violations.append(f"{day}: 文字数計算ミス (記録:{char_count} 実際:{actual_char_count})")
        
        # 犬のクイズペアチェック
        if animal_type == '犬':
            if not self._validate_quiz_answer_pairs(content_list):
                violations.append("クイズ・回答ペアに不整合があります")
        
        if violations:
            print("ERROR: 厳格品質チェック失敗:")
            for violation in violations:
                print(f"  - {violation}")
            return False
        
        print("SUCCESS: 厳格品質チェック合格（文字数制限完全遵守）")
        return True
    
    def _validate_quiz_answer_pairs(self, content_list: List[Dict]) -> bool:
        """
        クイズ・回答ペアの一貫性を検証
        """
        try:
            # 月曜（クイズ）→火曜（回答）のペア検証
            monday_post = content_list[0]['post_text']  # 月曜
            tuesday_post = content_list[1]['post_text']  # 火曜
            
            # 水曜（クイズ）→木曜（回答）のペア検証
            wednesday_post = content_list[2]['post_text']  # 水曜
            thursday_post = content_list[3]['post_text']   # 木曜
            
            # 月曜がクイズ形式か確認
            if not ('クイズ' in monday_post and ('A.' in monday_post or '①' in monday_post)):
                print("WARNING: 月曜の投稿がクイズ形式ではありません")
                return False
            
            # 火曜が回答形式か確認
            if not ('答え' in tuesday_post and ('正解' in tuesday_post or '解答' in tuesday_post)):
                print("WARNING: 火曜の投稿が回答形式ではありません")
                return False
            
            # 水曜がクイズ形式か確認
            if not ('クイズ' in wednesday_post and ('A.' in wednesday_post or '①' in wednesday_post)):
                print("WARNING: 水曜の投稿がクイズ形式ではありません")
                return False
            
            # 木曜が回答形式か確認
            if not ('答え' in thursday_post and ('正解' in thursday_post or '解答' in thursday_post)):
                print("WARNING: 木曜の投稿が回答形式ではありません")
                return False
            
            print("SUCCESS: クイズ・回答ペアの形式チェック合格")
            return True
            
        except Exception as e:
            print(f"ERROR: クイズ・回答ペア検証中にエラー: {e}")
            return False
    
    def _generate_fallback_weekly_content(self, animal_type: str, themes: List[str]) -> List[Dict]:
        """
        API生成が失敗した場合のフォールバック週間コンテンツ生成（クイズ・回答ペア保証）
        """
        print("INFO: フォールバック週間コンテンツ生成を開始します...")
        
        content_list = []
        days = ['月曜', '火曜', '水曜', '木曜', '金曜', '土曜', '日曜']
        
        for i, day in enumerate(days):
            # 投稿日時の計算
            today = datetime.now()
            current_weekday = today.weekday()
            target_weekday = i
            
            this_monday = today - timedelta(days=current_weekday)
            post_date = this_monday + timedelta(days=target_weekday)
            
            if post_date < today:
                post_date += timedelta(days=7)
            
            # テーマの決定
            theme = themes[i] if i < len(themes) else ('猫の健康管理' if animal_type == '猫' else '犬の健康管理')
            
            # フォールバックコンテンツ生成（クイズ・回答ペア考慮）
            if animal_type == '犬':
                post_text = self._get_guaranteed_dog_content(day, theme, i)
            else:
                post_text = self._get_fallback_content(theme, day, animal_type)
            
            content_list.append({
                'date': post_date.strftime('%Y-%m-%d'),
                'day': day,
                'animal_type': animal_type,
                'theme': theme,
                'post_text': post_text,
                'character_count': len(post_text),
                'scheduled_time': '07:00' if animal_type == '猫' else '18:00'
            })
        
        # 文字数チェックと調整
        content_list = self._validate_and_adjust_content(content_list, animal_type)
        
        print(f"SUCCESS: フォールバック週間コンテンツ生成完了: {len(content_list)}件")
        return content_list
    
    def _get_guaranteed_dog_content(self, day: str, theme: str, day_index: int) -> str:
        """
        犬の投稿で確実にクイズ・回答ペアになるコンテンツを生成
        """
        if day == '月曜':  # クイズ
            return f"【{theme}クイズ🤔】\n愛犬の健康管理で最も重要なポイントは次のうちどれでしょう？\n\nA. 毎日の運動\nB. 定期的な健康診断\nC. 高級なフード\n\n獣医師として、どれも大切ですが特に重要なものがあります。答えは明日！\n#獣医が教える犬のはなし"
        
        elif day == '火曜':  # 月曜の回答
            return f"【昨日のクイズの答え🎯】\n正解はB「定期的な健康診断」でした！\n\n早期発見が最も重要です。毎日の観察も大切ですが、飼い主さんが気づけない病気もあります。年1-2回の健康診断で、愛犬の健康を守りましょう🩺\n#獣医が教える犬のはなし"
        
        elif day == '水曜':  # クイズ
            return f"【{theme}クイズ💡】\n犬のストレスサインとして正しくないものはどれでしょう？\n\nA. 過度なあくび\nB. 尻尾を振る\nC. 隠れたがる\n\nストレスを理解して愛犬との関係を深めましょう。答えは明日お伝えします！\n#獣医が教える犬のはなし"
        
        elif day == '木曜':  # 水曜の回答
            return f"【昨日のクイズの答え📝】\n正解はB「尻尾を振る」でした！\n\n尻尾を振るのは嬉しい時だけでなく、興奮や警戒の時もあります。あくびや隠れるのは代表的なストレスサインです。愛犬の気持ちを理解してあげましょう🐕💕\n#獣医が教える犬のはなし"
        
        else:  # 金土日は通常コンテンツ
            return self._get_fallback_content(theme, day, '犬')


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