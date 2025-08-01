"""
Kid-Friendly Response Service for Phone Call Mode
Filters and adjusts AI responses to be appropriate for children
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class KidFriendlyService:
    """Service to ensure AI responses are appropriate for children"""
    
    def __init__(self):
        # Inappropriate words/phrases to filter (basic list)
        self.inappropriate_words = {
            'english': [
                'stupid', 'dumb', 'idiot', 'hate', 'kill', 'die', 'death',
                'violent', 'scary', 'frightening', 'terrifying', 'horror',
                'bad word', 'curse', 'damn', 'hell'
            ],
            'chinese': [
                '笨蛋', '白痴', '愚蠢', '讨厌', '杀', '死', '暴力',
                '可怕', '恐怖', '吓人', '坏话', '骂人'
            ]
        }
        
        # Positive replacement words
        self.positive_replacements = {
            'english': {
                'stupid': 'silly',
                'dumb': 'confused',
                'idiot': 'friend',
                'hate': 'dislike',
                'kill': 'stop',
                'die': 'sleep',
                'death': 'rest',
                'violent': 'energetic',
                'scary': 'surprising',
                'frightening': 'exciting',
                'terrifying': 'amazing',
                'horror': 'adventure'
            },
            'chinese': {
                '笨蛋': '小糊涂',
                '白痴': '小朋友',
                '愚蠢': '不太懂',
                '讨厌': '不喜欢',
                '杀': '停止',
                '死': '睡觉',
                '暴力': '有活力',
                '可怕': '有趣',
                '恐怖': '神奇',
                '吓人': '令人兴奋',
                '坏话': '不好的话',
                '骂人': '说不好听的话'
            }
        }
        
        # Kid-friendly conversation starters and responses
        self.kid_friendly_prompts = {
            'english': {
                'greeting': "Hi there, little friend! What would you like to talk about today?",
                'encouragement': ["That's wonderful!", "You're so smart!", "Great question!", "I love talking with you!"],
                'learning': ["Let's learn something fun!", "Did you know that...", "That's interesting! Tell me more!"],
                'goodbye': "It was so nice talking with you! Have a wonderful day!"
            },
            'chinese': {
                'greeting': "你好，小朋友！今天想聊什么呢？",
                'encouragement': ["太棒了！", "你真聪明！", "问得真好！", "我喜欢和你聊天！"],
                'learning': ["我们来学点有趣的吧！", "你知道吗...", "真有意思！告诉我更多吧！"],
                'goodbye': "和你聊天真开心！祝你有美好的一天！"
            }
        }
        
        # Topics that are kid-appropriate
        self.safe_topics = [
            'animals', 'nature', 'colors', 'numbers', 'letters', 'games',
            'friends', 'family', 'school', 'toys', 'books', 'music',
            'art', 'science (basic)', 'space', 'dinosaurs', 'fairy tales'
        ]
        
        logger.info("Kid-friendly service initialized")

    def is_kid_friendly_mode(self, session_data: Dict) -> bool:
        """Check if the session is in kid-friendly mode"""
        return session_data.get('kid_friendly_mode', False)

    def filter_response(self, text: str, language: str = 'english') -> str:
        """Filter inappropriate content from AI responses"""
        if not text:
            return text
            
        filtered_text = text.lower()
        lang_key = 'chinese' if language in ['zh', 'chinese', '中文'] else 'english'
        
        # Replace inappropriate words with positive alternatives
        inappropriate_words = self.inappropriate_words.get(lang_key, [])
        replacements = self.positive_replacements.get(lang_key, {})
        
        for word in inappropriate_words:
            if word in filtered_text:
                replacement = replacements.get(word, '[友好词语]' if lang_key == 'chinese' else '[nice word]')
                # Case-insensitive replacement while preserving original case
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                filtered_text = pattern.sub(replacement, filtered_text)
                logger.info(f"Filtered inappropriate word: {word} -> {replacement}")
        
        return filtered_text

    def enhance_for_kids(self, text: str, language: str = 'english') -> str:
        """Enhance response to be more kid-friendly"""
        lang_key = 'chinese' if language in ['zh', 'chinese', '中文'] else 'english'
        
        # Add encouraging words
        encouragements = self.kid_friendly_prompts[lang_key]['encouragement']
        
        # Simplify complex sentences
        if lang_key == 'english':
            # Replace complex words with simpler ones
            simple_replacements = {
                'difficult': 'hard',
                'complicated': 'tricky',
                'magnificent': 'amazing',
                'enormous': 'very big',
                'tiny': 'very small',
                'fascinating': 'really cool'
            }
        else:
            simple_replacements = {
                '困难的': '有点难',
                '复杂的': '有点复杂',
                '巨大的': '很大很大',
                '微小的': '很小很小',
                '迷人的': '很有趣'
            }
        
        enhanced_text = text
        for complex_word, simple_word in simple_replacements.items():
            enhanced_text = enhanced_text.replace(complex_word, simple_word)
        
        return enhanced_text

    def get_kid_friendly_prompt_prefix(self, language: str = 'english') -> str:
        """Get system prompt prefix for kid-friendly mode"""
        if language in ['zh', 'chinese', '中文']:
            return """你正在和一个小朋友对话。请：
- 使用简单、友好的语言
- 保持积极正面的态度
- 避免任何不适合儿童的内容
- 多使用鼓励和表扬的话语
- 如果遇到不合适的话题，温和地转移话题
- 回答要简短易懂"""
        else:
            return """You are talking with a child. Please:
- Use simple, friendly language
- Stay positive and encouraging
- Avoid any inappropriate content for children
- Use lots of praise and encouragement
- If inappropriate topics come up, gently redirect the conversation
- Keep answers short and easy to understand"""

    def validate_topic(self, topic: str) -> bool:
        """Check if a topic is appropriate for children"""
        topic_lower = topic.lower()
        
        # Check against safe topics
        for safe_topic in self.safe_topics:
            if safe_topic in topic_lower:
                return True
        
        # Check for inappropriate keywords
        inappropriate_keywords = [
            'violence', 'death', 'scary', 'adult', 'mature',
            '暴力', '死亡', '恐怖', '成人', '成熟'
        ]
        
        for keyword in inappropriate_keywords:
            if keyword in topic_lower:
                return False
        
        return True

    def get_topic_redirect_message(self, language: str = 'english') -> str:
        """Get a message to redirect inappropriate topics"""
        if language in ['zh', 'chinese', '中文']:
            return "让我们聊点别的有趣的事情吧！比如你最喜欢的动物是什么？"
        else:
            return "Let's talk about something else that's fun! What's your favorite animal?"

    def log_kid_interaction(self, session_id: str, user_input: str, ai_response: str, filtered: bool):
        """Log interactions in kid-friendly mode for monitoring"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'user_input_length': len(user_input),
            'ai_response_length': len(ai_response),
            'content_filtered': filtered,
            'mode': 'kid_friendly'
        }
        
        logger.info(f"Kid-friendly interaction logged: {log_entry}")

# Global instance
kid_friendly_service = KidFriendlyService()
