#!/usr/bin/env python3
"""
Generate structured summary report from analyzed chat data.
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SummaryConfig:
    level: str  # basic, standard, detailed
    language: str  # zh-CN, en
    include_sentiment: bool = True
    include_risks: bool = True


class SummaryGenerator:
    """Generate formatted summary reports."""
    
    STATUS_ICONS = {
        'pending': '⏳',
        'in_progress': '🔄',
        'done': '✅',
        'blocked': '⏸️',
        'cancelled': '❌'
    }
    
    SEVERITY_ICONS = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    }
    
    def __init__(self, config: SummaryConfig):
        self.config = config
    
    def generate(self, data: Dict) -> str:
        """Generate complete summary."""
        sections = []
        
        # Always include basic info
        sections.append(self._generate_basic_info(data))
        
        # Topic timeline (standard and detailed)
        if self.config.level in ['standard', 'detailed']:
            sections.append(self._generate_timeline(data))
        
        # Key points (always included)
        sections.append(self._generate_key_points(data))
        
        # Action items (always included)
        sections.append(self._generate_action_items(data))
        
        # Follow-up suggestions (standard and detailed)
        if self.config.level in ['standard', 'detailed']:
            sections.append(self._generate_follow_up(data))
        
        # Additional notes (detailed only)
        if self.config.level == 'detailed':
            sections.append(self._generate_notes(data))
        
        return '\n\n'.join(sections)
    
    def _generate_basic_info(self, data: Dict) -> str:
        """Generate basic information section."""
        info = data.get('basic_info', {})
        
        lines = [
            '## 一、基本信息',
            '',
            '| 项目 | 内容 |',
            '|------|------|',
            f"| 群名称 | {info.get('group_name', 'Unknown')} |",
            f"| 时间范围 | {self._format_time_range(info.get('time_range', {}))} |",
            f"| 参与人数 | {info.get('participant_count', 0)}人 |",
            f"| 消息总数 | {info.get('message_count', 0)}条 |",
        ]
        
        if self.config.level != 'basic':
            lines.append(f"| 总结类型 | {self._level_name(self.config.level)} |")
        
        return '\n'.join(lines)
    
    def _generate_timeline(self, data: Dict) -> str:
        """Generate topic timeline section."""
        topics = data.get('topics', [])
        
        if not topics:
            return '## 二、脉络梳理\n\n无明确话题脉络'
        
        lines = ['## 二、脉络梳理', '']
        
        # Group by time period
        periods = self._group_by_period(topics)
        
        for period_name, period_topics in periods.items():
            lines.append(f"### {period_name}")
            lines.append('')
            
            for topic in period_topics:
                start_time = self._format_time(topic.get('start_time', ''))
                lines.append(f"- **{start_time}** {topic.get('title', 'Unknown topic')}")
                
                # Add key events
                if self.config.level == 'detailed':
                    for event in topic.get('events', []):
                        event_time = self._format_time(event.get('time', ''))
                        lines.append(f"  - {event_time} {event.get('description', '')}")
                
                # Add decision if any
                if topic.get('decision'):
                    lines.append(f"  - ✅ **决定**: {topic['decision']}")
                
                lines.append('')
        
        return '\n'.join(lines)
    
    def _generate_key_points(self, data: Dict) -> str:
        """Generate key points section."""
        lines = ['## 三、核心要点', '']
        
        # Decisions
        decisions = data.get('decisions', [])
        if decisions:
            lines.append('### ✅ 已确定事项')
            lines.append('')
            for i, decision in enumerate(decisions, 1):
                lines.append(f"{i}. {decision}")
            lines.append('')
        
        # Risks
        if self.config.include_risks:
            risks = data.get('risks', [])
            if risks:
                lines.append('### ⚠️ 风险提示')
                lines.append('')
                for risk in risks:
                    icon = self.SEVERITY_ICONS.get(risk.get('severity', 'medium'), '🟡')
                    lines.append(f"{icon} **{risk.get('description', '')}**")
                    if risk.get('impact'):
                        lines.append(f"   - 影响: {risk['impact']}")
                    lines.append('')
        
        # Important information
        important = data.get('important_info', [])
        if important:
            lines.append('### 💡 重要信息')
            lines.append('')
            for info in important:
                lines.append(f"- {info}")
            lines.append('')
        
        # Unresolved items
        unresolved = data.get('unresolved', [])
        if unresolved and self.config.level != 'basic':
            lines.append('### 🤔 未决事项')
            lines.append('')
            for item in unresolved:
                lines.append(f"- {item.get('description', '')}")
                if item.get('next_step'):
                    lines.append(f"  - 下一步: {item['next_step']}")
            lines.append('')
        
        # Sentiment
        if self.config.include_sentiment and self.config.level != 'basic':
            sentiment = data.get('sentiment', {})
            if sentiment:
                lines.append('### 😊 情感氛围')
                lines.append('')
                overall = sentiment.get('overall_sentiment', 'neutral')
                emoji = {'positive': '😊', 'neutral': '😐', 'negative': '😟', 'mixed': '🤔'}
                lines.append(f"- 整体氛围: {emoji.get(overall, '😐')} {overall}")
                
                if sentiment.get('emotions'):
                    lines.append(f"- 主要情绪: {', '.join(sentiment['emotions'])}")
                
                if sentiment.get('controversy_score', 0) > 0.3:
                    lines.append(f"- 争议程度: 存在不同意见，需要进一步沟通")
                
                lines.append('')
        
        return '\n'.join(lines)
    
    def _generate_action_items(self, data: Dict) -> str:
        """Generate action items section."""
        items = data.get('action_items', [])
        
        lines = ['## 四、待办事项', '']
        
        if not items:
            lines.append('无明确待办事项')
            return '\n'.join(lines)
        
        # Table header
        lines.append('| 事项 | 负责人 | 截止时间 | 状态 | 备注 |')
        lines.append('|------|--------|----------|------|------|')
        
        # Table rows
        for item in items:
            status_icon = self.STATUS_ICONS.get(item.get('status', 'pending'), '⏳')
            owner = item.get('owner') or '待定'
            deadline = item.get('deadline') or '未设定'
            note = item.get('context', '')[:30] + '...' if item.get('context') else ''
            
            lines.append(f"| {item.get('description', '')[:40]} | {owner} | {deadline} | {status_icon} | {note} |")
        
        lines.append('')
        
        # Statistics
        if self.config.level != 'basic':
            stats = data.get('action_item_stats', {})
            lines.append(f"**统计**: 共 {stats.get('total', 0)} 项，"
                        f"已分配 {stats.get('with_owner', 0)} 项，"
                        f"已设截止 {stats.get('with_deadline', 0)} 项")
            lines.append('')
        
        return '\n'.join(lines)
    
    def _generate_follow_up(self, data: Dict) -> str:
        """Generate follow-up suggestions section."""
        lines = ['## 五、后续跟进建议', '']
        
        # Generate suggestions based on action items
        action_items = data.get('action_items', [])
        suggestions = []
        
        for item in action_items:
            if item.get('deadline'):
                suggestions.append({
                    'date': item['deadline'],
                    'action': f"检查: {item.get('description', '任务')[:30]}...",
                    'owner': item.get('owner', '相关负责人'),
                    'priority': 'high' if item.get('status') == 'blocked' else 'medium'
                })
        
        # Sort by date
        suggestions.sort(key=lambda x: x['date'])
        
        # Output
        for i, suggestion in enumerate(suggestions[:10], 1):  # Limit to 10
            lines.append(f"{i}. **{suggestion['date']}** - {suggestion['action']}")
            lines.append(f"   - 负责人: {suggestion['owner']}")
            if suggestion['priority'] == 'high':
                lines.append(f"   - ⚠️ 高优先级")
            lines.append('')
        
        if not suggestions:
            lines.append('根据待办事项自动生成的跟进建议')
        
        return '\n'.join(lines)
    
    def _generate_notes(self, data: Dict) -> str:
        """Generate additional notes section."""
        lines = ['## 六、其他备注', '']
        
        # Absences
        absences = data.get('absences', [])
        if absences:
            lines.append('- **人员变动**: ' + ', '.join(absences))
        
        # Holidays
        holidays = data.get('holidays', [])
        if holidays:
            lines.append(f"- **假期提醒**: {', '.join(holidays)}")
        
        # Resources
        resources = data.get('resources', [])
        if resources:
            lines.append('- **资源链接**:')
            for resource in resources:
                lines.append(f"  - {resource}")
        
        # Key moments from sentiment analysis
        sentiment = data.get('sentiment', {})
        if sentiment and sentiment.get('key_moments'):
            lines.append('- **关键情绪时刻**:')
            for moment in sentiment['key_moments'][:3]:
                time = self._format_time(moment.get('time', ''))
                lines.append(f"  - {time}: {moment.get('description', '')[:50]}")
        
        if len(lines) == 2:  # Only header
            lines.append('无其他备注')
        
        return '\n'.join(lines)
    
    def _format_time_range(self, time_range: Dict) -> str:
        """Format time range for display."""
        start = time_range.get('start', '')
        end = time_range.get('end', '')
        
        if not start or not end:
            return 'Unknown'
        
        # Extract date and time
        start_dt = self._parse_iso_time(start)
        end_dt = self._parse_iso_time(end)
        
        if start_dt and end_dt:
            if start_dt.date() == end_dt.date():
                return f"{start_dt.strftime('%Y-%m-%d')} {start_dt.strftime('%H:%M')} ~ {end_dt.strftime('%H:%M')}"
            else:
                return f"{start_dt.strftime('%Y-%m-%d %H:%M')} ~ {end_dt.strftime('%Y-%m-%d %H:%M')}"
        
        return f"{start[:16]} ~ {end[:16]}"
    
    def _format_time(self, timestamp: str) -> str:
        """Format timestamp for display."""
        dt = self._parse_iso_time(timestamp)
        if dt:
            return dt.strftime('%H:%M')
        return timestamp[:5] if len(timestamp) >= 5 else timestamp
    
    def _parse_iso_time(self, timestamp: str) -> Optional[datetime]:
        """Parse ISO timestamp."""
        if not timestamp:
            return None
        try:
            # Handle various ISO formats
            ts = timestamp.replace('Z', '+00:00')
            if '+' in ts:
                ts = ts.split('+')[0]
            return datetime.fromisoformat(ts)
        except ValueError:
            return None
    
    def _group_by_period(self, topics: List[Dict]) -> Dict[str, List[Dict]]:
        """Group topics by time period."""
        periods = {}
        
        for topic in topics:
            start_time = topic.get('start_time', '')
            dt = self._parse_iso_time(start_time)
            
            if dt:
                hour = dt.hour
                if 5 <= hour < 12:
                    period = '上午'
                elif 12 <= hour < 14:
                    period = '中午'
                elif 14 <= hour < 18:
                    period = '下午'
                elif 18 <= hour < 22:
                    period = '晚上'
                else:
                    period = '深夜'
                
                period_key = f"{dt.strftime('%m月%d日')}{period}"
            else:
                period_key = '其他时间'
            
            if period_key not in periods:
                periods[period_key] = []
            periods[period_key].append(topic)
        
        return periods
    
    def _level_name(self, level: str) -> str:
        """Get display name for summary level."""
        names = {
            'basic': '简要版',
            'standard': '标准版',
            'detailed': '详细版'
        }
        return names.get(level, level)


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python generate_summary.py <analyzed_data.json> [level] [language]")
        print("Levels: basic, standard, detailed (default: standard)")
        print("Languages: zh-CN, en (default: zh-CN)")
        sys.exit(1)
    
    file_path = sys.argv[1]
    level = sys.argv[2] if len(sys.argv) > 2 else 'standard'
    language = sys.argv[3] if len(sys.argv) > 3 else 'zh-CN'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    config = SummaryConfig(level=level, language=language)
    generator = SummaryGenerator(config)
    summary = generator.generate(data)
    
    print(summary)


if __name__ == '__main__':
    main()
