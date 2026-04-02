#!/usr/bin/env python3
"""
Analyze sentiment and emotional tone of chat conversations.
"""

import json
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from collections import Counter


@dataclass
class SentimentResult:
    overall_sentiment: str  # positive, neutral, negative, mixed
    sentiment_score: float  # -1.0 to 1.0
    breakdown: Dict[str, float]
    emotions: List[str]
    key_moments: List[Dict]
    concerns: List[str]
    positives: List[str]
    controversy_score: float  # 0.0 to 1.0


class SentimentAnalyzer:
    """Analyze sentiment of chat messages."""
    
    # Positive indicators
    POSITIVE_EMOJI = ['😊', '👍', '❤️', '💪', '🎉', '✅', '🙌', '👏', '🔥', '💯', '✨', '🌟']
    POSITIVE_WORDS = [
        '好', '棒', '赞', '优秀', '完美', '感谢', '谢谢', '同意', '支持', '期待',
        'good', 'great', 'awesome', 'excellent', 'perfect', 'thanks', 'agree', 'support',
        '期待', '兴奋', '开心', '满意', '顺利', '成功', '解决', '完成',
        'excited', 'happy', 'satisfied', 'smooth', 'success', 'solved', 'done',
    ]
    
    # Negative indicators
    NEGATIVE_EMOJI = ['😞', '👎', '❌', '😤', '😠', '💔', '😰', '😨', '🤬', '😡']
    NEGATIVE_WORDS = [
        '差', '糟', '问题', '错误', '失败', '延迟', '困难', '麻烦', '担心', '焦虑',
        'bad', 'terrible', 'problem', 'error', 'fail', 'delay', 'difficult', 'trouble', 'worry',
        '不行', '不对', '不好', '不满', '失望', '遗憾', '麻烦', '复杂', '卡住了',
        'not working', 'wrong', 'disappointed', 'regret', 'complicated', 'stuck',
    ]
    
    # Controversy indicators
    DISAGREEMENT_PATTERNS = [
        r'但是|不过|然而|可是',
        r'but|however|though|although',
        r'不同意|不赞成|反对|质疑',
        r'disagree|object|question|concern',
        r'我觉得不行|这样不好|有风险|有问题',
    ]
    
    EMOTION_PATTERNS = {
        'excited': ['兴奋', '激动', '期待', '太棒了', 'awesome', 'excited', 'looking forward'],
        'concerned': ['担心', '忧虑', '焦虑', '有风险', 'worried', 'concerned', 'anxious'],
        'frustrated': ['沮丧', '失望', '郁闷', 'frustrated', 'disappointed', 'upset'],
        'supportive': ['支持', '同意', '赞成', '没问题', 'support', 'agree', 'sounds good'],
        'confused': ['困惑', '不明白', '不清楚', 'confused', 'unclear', 'don\'t understand'],
        'urgent': ['紧急', '马上', '尽快', 'ASAP', 'urgent', 'immediately', 'as soon as'],
    }
    
    def analyze(self, messages: List[Dict]) -> SentimentResult:
        """Analyze sentiment of conversation."""
        if not messages:
            return self._empty_result()
        
        # Calculate base sentiment scores
        scores = [self._score_message(msg) for msg in messages]
        avg_score = sum(s[0] for s in scores) / len(scores)
        
        # Count reactions/emoji
        reaction_sentiment = self._analyze_reactions(messages)
        
        # Detect emotions
        emotions = self._detect_emotions(messages)
        
        # Find key moments
        key_moments = self._find_key_moments(messages, scores)
        
        # Extract concerns and positives
        concerns = self._extract_concerns(messages)
        positives = self._extract_positives(messages)
        
        # Calculate controversy
        controversy = self._calculate_controversy(messages)
        
        # Determine overall sentiment
        overall = self._determine_overall(avg_score, reaction_sentiment, controversy)
        
        # Calculate breakdown
        breakdown = self._calculate_breakdown(scores)
        
        return SentimentResult(
            overall_sentiment=overall,
            sentiment_score=round(avg_score, 2),
            breakdown=breakdown,
            emotions=emotions,
            key_moments=key_moments,
            concerns=concerns,
            positives=positives,
            controversy_score=round(controversy, 2)
        )
    
    def _score_message(self, msg: Dict) -> Tuple[float, Dict]:
        """Score a single message. Returns (score, details)."""
        content = msg.get('content', '')
        reactions = msg.get('reactions', [])
        
        score = 0.0
        details = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        # Check content
        content_lower = content.lower()
        
        # Positive indicators
        pos_count = sum(1 for w in self.POSITIVE_WORDS if w in content or w in content_lower)
        pos_emoji = sum(1 for e in self.POSITIVE_EMOJI if e in content)
        details['positive'] = pos_count + pos_emoji
        
        # Negative indicators
        neg_count = sum(1 for w in self.NEGATIVE_WORDS if w in content or w in content_lower)
        neg_emoji = sum(1 for e in self.NEGATIVE_EMOJI if e in content)
        details['negative'] = neg_count + neg_emoji
        
        # Reactions
        for reaction in reactions:
            reaction_str = str(reaction)
            if any(e in reaction_str for e in self.POSITIVE_EMOJI):
                details['positive'] += 1
            elif any(e in reaction_str for e in self.NEGATIVE_EMOJI):
                details['negative'] += 1
        
        # Calculate score
        total = details['positive'] + details['negative']
        if total > 0:
            score = (details['positive'] - details['negative']) / max(total, 1)
        
        # Adjust for intensity
        if '!' in content or '！' in content:
            score *= 1.2
        if '?' in content or '？' in content:
            score *= 0.8  # Questions are neutral
        
        return max(min(score, 1.0), -1.0), details
    
    def _analyze_reactions(self, messages: List[Dict]) -> float:
        """Analyze overall reaction sentiment."""
        all_reactions = []
        for msg in messages:
            all_reactions.extend(msg.get('reactions', []))
        
        if not all_reactions:
            return 0.0
        
        positive = sum(1 for r in all_reactions if any(e in str(r) for e in self.POSITIVE_EMOJI))
        negative = sum(1 for r in all_reactions if any(e in str(r) for e in self.NEGATIVE_EMOJI))
        
        total = positive + negative
        if total == 0:
            return 0.0
        
        return (positive - negative) / total
    
    def _detect_emotions(self, messages: List[Dict]) -> List[str]:
        """Detect dominant emotions in conversation."""
        emotion_scores = {emotion: 0 for emotion in self.EMOTION_PATTERNS}
        
        for msg in messages:
            content = msg.get('content', '').lower()
            for emotion, patterns in self.EMOTION_PATTERNS.items():
                for pattern in patterns:
                    if pattern in content:
                        emotion_scores[emotion] += 1
        
        # Return top emotions
        sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
        return [e[0] for e in sorted_emotions if e[1] > 0][:3]
    
    def _find_key_moments(self, messages: List[Dict], scores: List[Tuple[float, Dict]]) -> List[Dict]:
        """Find moments with significant sentiment shifts."""
        moments = []
        
        for i, (msg, (score, _)) in enumerate(zip(messages, scores)):
            # Significant positive or negative
            if abs(score) > 0.5:
                moments.append({
                    'time': msg.get('timestamp', ''),
                    'sender': msg.get('sender', 'Unknown'),
                    'description': msg.get('content', '')[:100],
                    'sentiment': 'positive' if score > 0 else 'negative',
                    'intensity': abs(score)
                })
            
            # Sentiment shift
            if i > 0:
                prev_score = scores[i-1][0]
                if abs(score - prev_score) > 0.7:
                    moments.append({
                        'time': msg.get('timestamp', ''),
                        'description': f"Sentiment shift from {'positive' if prev_score > 0 else 'negative'} to {'positive' if score > 0 else 'negative'}",
                        'sentiment_shift': f"{'positive' if prev_score > 0 else 'negative'}_to_{'positive' if score > 0 else 'negative'}"
                    })
        
        # Sort by intensity and return top 5
        moments.sort(key=lambda x: x.get('intensity', 0.5), reverse=True)
        return moments[:5]
    
    def _extract_concerns(self, messages: List[Dict]) -> List[str]:
        """Extract expressed concerns."""
        concerns = []
        concern_patterns = [
            r'担心\s*(.+?)[，。！；]',
            r'问题[是\s]*(.+?)[，。！；]',
            r'风险[是\s]*(.+?)[，。！；]',
            r'concern[ed]*\s*(?:about|that)?\s*(.+?)[.!;]',
            r'worried\s*(?:about)?\s*(.+?)[.!;]',
        ]
        
        for msg in messages:
            content = msg.get('content', '')
            for pattern in concern_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                concerns.extend(matches)
        
        # Deduplicate and limit
        unique_concerns = list(set(concerns))
        return [c[:100] for c in unique_concerns[:5]]
    
    def _extract_positives(self, messages: List[Dict]) -> List[str]:
        """Extract positive moments."""
        positives = []
        
        for msg in messages:
            content = msg.get('content', '')
            score, _ = self._score_message(msg)
            
            if score > 0.5 and len(content) > 10:
                positives.append(content[:100])
        
        return positives[:5]
    
    def _calculate_controversy(self, messages: List[Dict]) -> float:
        """Calculate controversy level (disagreement without resolution)."""
        disagreement_count = 0
        resolution_count = 0
        
        for msg in messages:
            content = msg.get('content', '')
            
            # Count disagreements
            for pattern in self.DISAGREEMENT_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    disagreement_count += 1
            
            # Count resolutions
            if any(w in content for w in ['同意', '确定', '决定', 'agree', 'decided', 'confirm']):
                resolution_count += 1
        
        if disagreement_count == 0:
            return 0.0
        
        # Higher controversy if more disagreements than resolutions
        return min(disagreement_count / max(resolution_count, 1) / 5, 1.0)
    
    def _determine_overall(self, avg_score: float, reaction_sentiment: float, controversy: float) -> str:
        """Determine overall sentiment label."""
        # Blend scores
        blended = (avg_score + reaction_sentiment) / 2
        
        # Adjust for controversy
        if controversy > 0.5:
            return 'mixed'
        
        if blended > 0.2:
            return 'positive'
        elif blended < -0.2:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_breakdown(self, scores: List[Tuple[float, Dict]]) -> Dict[str, float]:
        """Calculate sentiment breakdown percentages."""
        if not scores:
            return {'positive': 0, 'neutral': 1.0, 'negative': 0}
        
        positive = sum(1 for s, _ in scores if s > 0.2)
        negative = sum(1 for s, _ in scores if s < -0.2)
        neutral = len(scores) - positive - negative
        
        total = len(scores)
        return {
            'positive': round(positive / total, 2),
            'neutral': round(neutral / total, 2),
            'negative': round(negative / total, 2)
        }
    
    def _empty_result(self) -> SentimentResult:
        """Return empty result."""
        return SentimentResult(
            overall_sentiment='neutral',
            sentiment_score=0.0,
            breakdown={'positive': 0, 'neutral': 1.0, 'negative': 0},
            emotions=[],
            key_moments=[],
            concerns=[],
            positives=[],
            controversy_score=0.0
        )


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python analyze_sentiment.py <parsed_messages.json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    messages = data.get('messages', [])
    
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(messages)
    
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
