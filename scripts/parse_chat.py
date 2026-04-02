#!/usr/bin/env python3
"""
Parse chat logs from various platforms into standardized format.
Supports: Feishu, DingTalk, WeChat Work, Discord, Slack, Teams, Telegram
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Message:
    timestamp: str
    sender: str
    content: str
    type: str = "text"
    mentions: List[str] = None
    reply_to: Optional[str] = None
    reactions: List[str] = None
    
    def __post_init__(self):
        if self.mentions is None:
            self.mentions = []
        if self.reactions is None:
            self.reactions = []


@dataclass
class ParseResult:
    platform: str
    messages: List[Message]
    participants: List[str]
    time_range: Dict[str, str]
    group_name: Optional[str] = None


class ChatParser:
    """Main parser class that auto-detects platform and parses messages."""
    
    def __init__(self):
        self.parsers = {
            'feishu': self._parse_feishu,
            'dingtalk': self._parse_dingtalk,
            'wechat_work': self._parse_wechat_work,
            'discord': self._parse_discord,
            'slack': self._parse_slack,
            'teams': self._parse_teams,
            'telegram': self._parse_telegram,
            'generic': self._parse_generic,
        }
    
    def parse(self, content: str, platform: Optional[str] = None) -> ParseResult:
        """Parse chat content, auto-detecting platform if not specified."""
        if platform is None:
            platform = self._detect_platform(content)
        
        parser = self.parsers.get(platform, self._parse_generic)
        return parser(content)
    
    def _detect_platform(self, content: str) -> str:
        """Auto-detect platform based on content patterns."""
        # Check for JSON structure
        if content.strip().startswith('{'):
            try:
                data = json.loads(content)
                if 'guild' in data:
                    return 'discord'
                elif 'conversation' in data and 'id' in data.get('conversation', {}):
                    return 'teams'
                elif 'message_list' in data or 'room_name' in data:
                    return 'wechat_work'
                elif 'messages' in data and isinstance(data['messages'], list):
                    if 'name' in data and 'type' in data:
                        return 'telegram'
                    return 'feishu'
            except json.JSONDecodeError:
                pass
        
        # Check text patterns
        if '[系统消息]' in content or '飞书' in content[:100]:
            return 'feishu'
        elif '钉钉' in content[:100] or 'DingTalk' in content[:100]:
            return 'dingtalk'
        elif '企业微信' in content[:100]:
            return 'wechat_work'
        
        return 'generic'
    
    def _parse_feishu(self, content: str) -> ParseResult:
        """Parse Feishu chat export."""
        messages = []
        
        # Try JSON first
        try:
            data = json.loads(content)
            if 'messages' in data:
                for msg in data['messages']:
                    messages.append(Message(
                        timestamp=self._normalize_timestamp(msg.get('timestamp', '')),
                        sender=msg.get('sender', 'Unknown'),
                        content=msg.get('content', ''),
                        type=msg.get('type', 'text'),
                        mentions=msg.get('mentions', []),
                        reply_to=msg.get('reply_to')
                    ))
                return ParseResult(
                    platform='feishu',
                    messages=messages,
                    participants=list(set(m.sender for m in messages)),
                    time_range=self._get_time_range(messages),
                    group_name=data.get('group_name')
                )
        except json.JSONDecodeError:
            pass
        
        # Parse text format
        lines = content.split('\n')
        current_msg = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Pattern: 2024-04-01 09:15:30 Username
            match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)(?:\s+\[回复\s+(\S+)\])?', line)
            if match:
                if current_msg:
                    messages.append(current_msg)
                timestamp, sender, reply_to = match.groups()
                current_msg = Message(
                    timestamp=self._normalize_timestamp(timestamp),
                    sender=sender,
                    content='',
                    reply_to=reply_to
                )
            elif current_msg:
                current_msg.content += line + '\n'
        
        if current_msg:
            messages.append(current_msg)
        
        # Clean up content
        for msg in messages:
            msg.content = msg.content.strip()
            msg.mentions = re.findall(r'@(\S+)', msg.content)
        
        return ParseResult(
            platform='feishu',
            messages=messages,
            participants=list(set(m.sender for m in messages)),
            time_range=self._get_time_range(messages)
        )
    
    def _parse_dingtalk(self, content: str) -> ParseResult:
        """Parse DingTalk chat export."""
        messages = []
        
        # Try JSON
        try:
            data = json.loads(content)
            if 'conversation' in data and 'messages' in data['conversation']:
                for msg in data['conversation']['messages']:
                    messages.append(Message(
                        timestamp=self._normalize_timestamp(msg.get('createdAt', '')),
                        sender=msg.get('senderNick', 'Unknown'),
                        content=msg.get('content', {}).get('text', ''),
                        type=msg.get('msgType', 'text')
                    ))
                return ParseResult(
                    platform='dingtalk',
                    messages=messages,
                    participants=list(set(m.sender for m in messages)),
                    time_range=self._get_time_range(messages),
                    group_name=data['conversation'].get('title')
                )
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Parse text format: [2024-04-01 09:15] Username
        lines = content.split('\n')
        current_msg = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = re.match(r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\]\s+(\S+)', line)
            if match:
                if current_msg:
                    messages.append(current_msg)
                timestamp, sender = match.groups()
                current_msg = Message(
                    timestamp=self._normalize_timestamp(timestamp + ':00'),
                    sender=sender,
                    content=''
                )
            elif current_msg:
                current_msg.content += line + '\n'
        
        if current_msg:
            messages.append(current_msg)
        
        for msg in messages:
            msg.content = msg.content.strip()
            msg.mentions = re.findall(r'@(\S+)', msg.content)
        
        return ParseResult(
            platform='dingtalk',
            messages=messages,
            participants=list(set(m.sender for m in messages)),
            time_range=self._get_time_range(messages)
        )
    
    def _parse_wechat_work(self, content: str) -> ParseResult:
        """Parse WeChat Work chat export."""
        messages = []
        
        # Try JSON
        try:
            data = json.loads(content)
            if 'message_list' in data:
                for msg in data['message_list']:
                    messages.append(Message(
                        timestamp=self._normalize_timestamp(msg.get('send_time', '')),
                        sender=msg.get('sender', 'Unknown'),
                        content=msg.get('content', ''),
                        type=msg.get('msg_type', 'text')
                    ))
                return ParseResult(
                    platform='wechat_work',
                    messages=messages,
                    participants=list(set(m.sender for m in messages)),
                    time_range=self._get_time_range(messages),
                    group_name=data.get('room_name')
                )
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Parse text format: Username 2024-04-01 09:15:30
        lines = content.split('\n')
        current_msg = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = re.match(r'(\S+)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
            if match:
                if current_msg:
                    messages.append(current_msg)
                sender, timestamp = match.groups()
                current_msg = Message(
                    timestamp=self._normalize_timestamp(timestamp),
                    sender=sender,
                    content=''
                )
            elif current_msg:
                current_msg.content += line + '\n'
        
        if current_msg:
            messages.append(current_msg)
        
        for msg in messages:
            msg.content = msg.content.strip()
            msg.mentions = re.findall(r'@(\S+)', msg.content)
        
        return ParseResult(
            platform='wechat_work',
            messages=messages,
            participants=list(set(m.sender for m in messages)),
            time_range=self._get_time_range(messages)
        )
    
    def _parse_discord(self, content: str) -> ParseResult:
        """Parse Discord JSON export."""
        data = json.loads(content)
        messages = []
        
        def extract_messages(channel_data):
            for msg in channel_data.get('messages', []):
                author = msg.get('author', {})
                messages.append(Message(
                    timestamp=self._normalize_timestamp(msg.get('timestamp', '')),
                    sender=author.get('username', 'Unknown'),
                    content=msg.get('content', ''),
                    mentions=[m.get('username') for m in msg.get('mentions', [])],
                    reactions=[r.get('emoji', {}).get('name', '') for r in msg.get('reactions', [])]
                ))
                # Handle thread messages
                if 'thread' in msg and 'messages' in msg['thread']:
                    extract_messages(msg['thread'])
        
        if 'guild' in data:
            for channel in data['guild'].get('channels', []):
                extract_messages(channel)
            group_name = data['guild'].get('name')
        else:
            extract_messages(data)
            group_name = None
        
        return ParseResult(
            platform='discord',
            messages=messages,
            participants=list(set(m.sender for m in messages)),
            time_range=self._get_time_range(messages),
            group_name=group_name
        )
    
    def _parse_slack(self, content: str) -> ParseResult:
        """Parse Slack JSON export."""
        data = json.loads(content)
        messages = []
        
        # Handle array of messages
        if isinstance(data, list):
            msg_list = data
        elif 'messages' in data:
            msg_list = data['messages']
        else:
            msg_list = [data]
        
        for msg in msg_list:
            ts = msg.get('ts', '')
            timestamp = datetime.fromtimestamp(float(ts)).isoformat() if ts else ''
            
            messages.append(Message(
                timestamp=timestamp,
                sender=msg.get('user', 'Unknown'),
                content=msg.get('text', ''),
                reactions=[r.get('name', '') for r in msg.get('reactions', [])]
            ))
        
        return ParseResult(
            platform='slack',
            messages=messages,
            participants=list(set(m.sender for m in messages)),
            time_range=self._get_time_range(messages)
        )
    
    def _parse_teams(self, content: str) -> ParseResult:
        """Parse Microsoft Teams JSON export."""
        data = json.loads(content)
        messages = []
        
        for msg in data.get('conversation', {}).get('messages', []):
            sender = msg.get('from', {}).get('user', {}).get('displayName', 'Unknown')
            messages.append(Message(
                timestamp=self._normalize_timestamp(msg.get('createdDateTime', '')),
                sender=sender,
                content=msg.get('body', {}).get('content', ''),
                type=msg.get('body', {}).get('contentType', 'text')
            ))
        
        return ParseResult(
            platform='teams',
            messages=messages,
            participants=list(set(m.sender for m in messages)),
            time_range=self._get_time_range(messages)
        )
    
    def _parse_telegram(self, content: str) -> ParseResult:
        """Parse Telegram JSON export."""
        data = json.loads(content)
        messages = []
        
        for msg in data.get('messages', []):
            if msg.get('type') == 'message':
                text = msg.get('text', '')
                if isinstance(text, list):
                    text = ' '.join(str(t) for t in text)
                
                messages.append(Message(
                    timestamp=self._normalize_timestamp(msg.get('date', '')),
                    sender=msg.get('from', 'Unknown'),
                    content=text
                ))
        
        return ParseResult(
            platform='telegram',
            messages=messages,
            participants=list(set(m.sender for m in messages)),
            time_range=self._get_time_range(messages),
            group_name=data.get('name')
        )
    
    def _parse_generic(self, content: str) -> ParseResult:
        """Parse generic text format."""
        messages = []
        lines = content.split('\n')
        
        # Try various patterns
        patterns = [
            # [2024-04-01 09:15:30] Username: Message
            r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+(\S+):\s*(.*)',
            # Username [09:15:30]: Message
            r'(\S+)\s+\[(\d{2}:\d{2}:\d{2})\]:\s*(.*)',
            # Username 2024-04-01 09:15:30: Message
            r'(\S+)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}):\s*(.*)',
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    if len(groups[0]) > 10:  # Has date
                        timestamp = groups[0]
                        sender = groups[1]
                        content_text = groups[2] if len(groups) > 2 else ''
                    else:  # Only time
                        sender = groups[0]
                        timestamp = groups[1]
                        content_text = groups[2] if len(groups) > 2 else ''
                    
                    messages.append(Message(
                        timestamp=self._normalize_timestamp(timestamp),
                        sender=sender,
                        content=content_text
                    ))
                    break
        
        return ParseResult(
            platform='generic',
            messages=messages,
            participants=list(set(m.sender for m in messages)),
            time_range=self._get_time_range(messages)
        )
    
    def _normalize_timestamp(self, ts: str) -> str:
        """Normalize various timestamp formats to ISO 8601."""
        if not ts:
            return ''
        
        # Already ISO format
        if 'T' in ts:
            return ts.replace('Z', '+00:00')
        
        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y/%m/%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%m/%d/%Y %I:%M %p',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(ts.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        return ts
    
    def _get_time_range(self, messages: List[Message]) -> Dict[str, str]:
        """Get time range from messages."""
        if not messages:
            return {'start': '', 'end': ''}
        
        timestamps = [m.timestamp for m in messages if m.timestamp]
        if not timestamps:
            return {'start': '', 'end': ''}
        
        return {
            'start': min(timestamps),
            'end': max(timestamps)
        }


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parse_chat.py <chat_file> [platform]")
        print("Platforms: feishu, dingtalk, wechat_work, discord, slack, teams, telegram")
        sys.exit(1)
    
    file_path = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = ChatParser()
    result = parser.parse(content, platform)
    
    # Output as JSON
    output = {
        'platform': result.platform,
        'group_name': result.group_name,
        'participants': result.participants,
        'time_range': result.time_range,
        'message_count': len(result.messages),
        'messages': [asdict(m) for m in result.messages]
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
