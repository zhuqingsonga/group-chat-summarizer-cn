#!/usr/bin/env python3
"""
Extract action items, tasks, and assignments from parsed chat messages.
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class ActionItem:
    id: str
    description: str
    owner: Optional[str]
    deadline: Optional[str]
    deadline_type: str  # explicit, inferred, none
    status: str  # pending, done, in_progress, blocked
    source_message: str
    context: str
    confidence: float  # 0.0-1.0


class ActionItemExtractor:
    """Extract action items from chat messages."""
    
    # Task indicator keywords
    TASK_KEYWORDS = [
        # Chinese
        '完成', '准备', '检查', '确认', '提交', '更新', '修改', '审核',
        'review', 'prepare', 'check', 'confirm', 'submit', 'update', 'modify',
        '需要', '要', '必须', '得', '负责', '来做', '处理', '解决',
        'need to', 'have to', 'must', 'should', 'responsible for', 'handle',
    ]
    
    # Status indicators
    STATUS_DONE = ['已完成', '搞定', 'done', 'finished', 'completed', '✅', '☑️']
    STATUS_IN_PROGRESS = ['进行中', '正在', 'in progress', 'working on', '🔄']
    STATUS_BLOCKED = ['阻塞', '卡住', 'blocked', 'stuck', 'waiting for', '⏸️', '❌']
    STATUS_PENDING = ['待办', 'pending', 'todo', '待处理', '⏳']
    
    # Deadline patterns
    DEADLINE_PATTERNS = [
        # Chinese patterns
        (r'(本周|下周|下下周)([一二三四五六日])', 'relative_weekday'),
        (r'(今天|明天|后天|大后天)', 'relative_day'),
        (r'(\d+)月(\d+)日', 'month_day'),
        (r'(\d{4})年(\d+)月(\d+)日', 'full_date'),
        (r'(周一|周二|周三|周四|周五|周六|周日|星期[一二三四五六日])', 'weekday'),
        (r'(\d+)号', 'day_only'),
        (r'(\d+)天后', 'days_later'),
        (r'(\d+)周后', 'weeks_later'),
        # English patterns
        (r'by\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)', 'weekday_en'),
        (r'by\s+(tomorrow|today|next week)', 'relative_en'),
        (r'by\s+(\d{1,2})\s*(st|nd|rd|th)?', 'date_en'),
        (r'(\d+)\s*days?\s*(from now)?', 'days_later_en'),
        (r'ASAP|asap|尽快', 'asap'),
    ]
    
    def __init__(self, reference_date: Optional[datetime] = None):
        self.reference_date = reference_date or datetime.now()
        self.item_counter = 0
    
    def extract(self, messages: List[Dict]) -> List[ActionItem]:
        """Extract action items from messages."""
        items = []
        
        for i, msg in enumerate(messages):
            content = msg.get('content', '')
            sender = msg.get('sender', 'Unknown')
            timestamp = msg.get('timestamp', '')
            
            # Skip system messages and very short messages
            if not content or len(content) < 5:
                continue
            
            # Check if message contains task indicators
            if self._contains_task_indicator(content):
                item = self._extract_action_item(msg, messages[max(0, i-2):i+3])
                if item:
                    items.append(item)
        
        # Deduplicate similar items
        items = self._deduplicate(items)
        
        return items
    
    def _contains_task_indicator(self, content: str) -> bool:
        """Check if content contains task indicators."""
        content_lower = content.lower()
        return any(kw in content or kw in content_lower for kw in self.TASK_KEYWORDS)
    
    def _extract_action_item(self, msg: Dict, context_messages: List[Dict]) -> Optional[ActionItem]:
        """Extract a single action item from message."""
        content = msg.get('content', '')
        sender = msg.get('sender', 'Unknown')
        
        # Extract task description
        description = self._extract_description(content)
        if not description:
            return None
        
        # Extract owner
        owner = self._extract_owner(content, context_messages)
        
        # Extract deadline
        deadline, deadline_type = self._extract_deadline(content, msg.get('timestamp', ''))
        
        # Determine status
        status = self._determine_status(content)
        
        # Build context
        context = self._build_context(context_messages)
        
        # Calculate confidence
        confidence = self._calculate_confidence(content, owner, deadline)
        
        self.item_counter += 1
        
        return ActionItem(
            id=f"task-{self.item_counter:03d}",
            description=description,
            owner=owner,
            deadline=deadline,
            deadline_type=deadline_type,
            status=status,
            source_message=msg.get('id', ''),
            context=context,
            confidence=confidence
        )
    
    def _extract_description(self, content: str) -> Optional[str]:
        """Extract clean task description."""
        # Remove @mentions for cleaner description
        clean = re.sub(r'@\S+', '', content)
        
        # Remove status markers
        for marker in self.STATUS_DONE + self.STATUS_IN_PROGRESS + self.STATUS_BLOCKED + self.STATUS_PENDING:
            clean = clean.replace(marker, '')
        
        # Remove deadline phrases
        clean = re.sub(r'(by|before|在|之前).*?(?=[，。！；]|$)', '', clean, flags=re.IGNORECASE)
        
        clean = clean.strip(' ，。！；:')
        
        # Return if meaningful length
        if len(clean) > 5:
            return clean[:200]  # Limit length
        
        return None
    
    def _extract_owner(self, content: str, context_messages: List[Dict]) -> Optional[str]:
        """Extract task owner from @mentions or context."""
        # Look for @mentions
        mentions = re.findall(r'@(\S+)', content)
        if mentions:
            return mentions[0]
        
        # Look for assignment patterns
        patterns = [
            r'由\s*@?(\S+?)\s*(负责|来做|处理)',
            r'@?(\S+?)\s*(负责|来做|处理|跟进)',
            r'(\S+?)\s*来\s*(做|负责|跟进)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        # Check context for "好的，我来..."
        for ctx_msg in context_messages:
            ctx_content = ctx_msg.get('content', '')
            ctx_sender = ctx_msg.get('sender', '')
            
            if re.search(r'(好的|ok|我来|我负责)', ctx_content, re.IGNORECASE):
                return ctx_sender
        
        return None
    
    def _extract_deadline(self, content: str, msg_timestamp: str) -> Tuple[Optional[str], str]:
        """Extract deadline from content."""
        for pattern, pattern_type in self.DEADLINE_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                deadline = self._parse_deadline(match, pattern_type, msg_timestamp)
                if deadline:
                    return deadline, 'explicit'
        
        # Check for relative time references in context
        if '尽快' in content or 'ASAP' in content.upper():
            # Default to 2 days
            ref_date = self._parse_timestamp(msg_timestamp) or self.reference_date
            deadline = (ref_date + timedelta(days=2)).strftime('%Y-%m-%d')
            return deadline, 'inferred'
        
        return None, 'none'
    
    def _parse_deadline(self, match, pattern_type: str, msg_timestamp: str) -> Optional[str]:
        """Parse matched deadline pattern."""
        ref_date = self._parse_timestamp(msg_timestamp) or self.reference_date
        groups = match.groups()
        
        try:
            if pattern_type == 'relative_day':
                day_map = {'今天': 0, '明天': 1, '后天': 2, '大后天': 3}
                days = day_map.get(groups[0], 0)
                return (ref_date + timedelta(days=days)).strftime('%Y-%m-%d')
            
            elif pattern_type == 'month_day':
                month, day = int(groups[0]), int(groups[1])
                year = ref_date.year
                # Handle year boundary
                if month < ref_date.month:
                    year += 1
                return f"{year:04d}-{month:02d}-{day:02d}"
            
            elif pattern_type == 'full_date':
                return f"{groups[0]}-{int(groups[1]):02d}-{int(groups[2]):02d}"
            
            elif pattern_type == 'weekday':
                weekday_map = {
                    '周一': 0, '周二': 1, '周三': 2, '周四': 3, '周五': 4, '周六': 5, '周日': 6,
                    '星期一': 0, '星期二': 1, '星期三': 2, '星期四': 3, '星期五': 4, '星期六': 5, '星期日': 6,
                }
                target_weekday = weekday_map.get(groups[0], 0)
                current_weekday = ref_date.weekday()
                days_ahead = (target_weekday - current_weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week if today
                return (ref_date + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            
            elif pattern_type == 'days_later':
                days = int(groups[0])
                return (ref_date + timedelta(days=days)).strftime('%Y-%m-%d')
            
            elif pattern_type == 'weeks_later':
                weeks = int(groups[0])
                return (ref_date + timedelta(weeks=weeks)).strftime('%Y-%m-%d')
            
            elif pattern_type == 'relative_en':
                day_map = {'today': 0, 'tomorrow': 1, 'next week': 7}
                days = day_map.get(groups[0].lower(), 0)
                return (ref_date + timedelta(days=days)).strftime('%Y-%m-%d')
            
            elif pattern_type == 'days_later_en':
                days = int(groups[0])
                return (ref_date + timedelta(days=days)).strftime('%Y-%m-%d')
        
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _parse_timestamp(self, timestamp: str) -> Optional[datetime]:
        """Parse ISO timestamp."""
        if not timestamp:
            return None
        try:
            # Handle ISO format
            if 'T' in timestamp:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00').replace('+00:00', ''))
            # Handle simple date
            return datetime.strptime(timestamp[:10], '%Y-%m-%d')
        except ValueError:
            return None
    
    def _determine_status(self, content: str) -> str:
        """Determine task status from content."""
        content_lower = content.lower()
        
        for marker in self.STATUS_DONE:
            if marker in content or marker in content_lower:
                return 'done'
        
        for marker in self.STATUS_BLOCKED:
            if marker in content or marker in content_lower:
                return 'blocked'
        
        for marker in self.STATUS_IN_PROGRESS:
            if marker in content or marker in content_lower:
                return 'in_progress'
        
        return 'pending'
    
    def _build_context(self, context_messages: List[Dict]) -> str:
        """Build context from surrounding messages."""
        contexts = []
        for msg in context_messages:
            sender = msg.get('sender', 'Unknown')
            content = msg.get('content', '')[:100]  # Limit length
            if content:
                contexts.append(f"{sender}: {content}")
        
        return '\n'.join(contexts)
    
    def _calculate_confidence(self, content: str, owner: Optional[str], deadline: Optional[str]) -> float:
        """Calculate confidence score for extraction."""
        score = 0.5  # Base score
        
        # Boost for clear task keywords
        if any(kw in content for kw in ['完成', '准备', 'review', 'prepare', '负责']):
            score += 0.2
        
        # Boost for having owner
        if owner:
            score += 0.15
        
        # Boost for having deadline
        if deadline:
            score += 0.15
        
        return min(score, 1.0)
    
    def _deduplicate(self, items: List[ActionItem]) -> List[ActionItem]:
        """Remove duplicate action items."""
        seen = set()
        unique = []
        
        for item in items:
            # Create signature
            sig = (item.description[:50], item.owner)
            if sig not in seen:
                seen.add(sig)
                unique.append(item)
        
        return unique
    
    def get_statistics(self, items: List[ActionItem]) -> Dict:
        """Get statistics about extracted items."""
        return {
            'total': len(items),
            'with_owner': sum(1 for i in items if i.owner),
            'with_deadline': sum(1 for i in items if i.deadline),
            'by_status': {
                'pending': sum(1 for i in items if i.status == 'pending'),
                'in_progress': sum(1 for i in items if i.status == 'in_progress'),
                'done': sum(1 for i in items if i.status == 'done'),
                'blocked': sum(1 for i in items if i.status == 'blocked'),
            }
        }


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_action_items.py <parsed_messages.json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    messages = data.get('messages', [])
    
    extractor = ActionItemExtractor()
    items = extractor.extract(messages)
    stats = extractor.get_statistics(items)
    
    output = {
        'action_items': [asdict(item) for item in items],
        'statistics': stats
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
