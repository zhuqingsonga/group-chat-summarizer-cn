#!/usr/bin/env python3
"""
Main entry point for group chat summarization.
Orchestrates parsing, analysis, and summary generation.
"""

import json
import sys
import argparse
from pathlib import Path

# Import our modules
from parse_chat import ChatParser
from extract_action_items import ActionItemExtractor
from analyze_sentiment import SentimentAnalyzer
from detect_risks import RiskDetector
from generate_summary import SummaryGenerator, SummaryConfig


def process_chat(chat_content: str, platform: str = None, level: str = 'standard') -> dict:
    """
    Process chat content and generate summary.
    
    Args:
        chat_content: Raw chat log content
        platform: Platform name (auto-detected if None)
        level: Summary level (basic, standard, detailed)
    
    Returns:
        Dictionary containing all analysis results
    """
    # Step 1: Parse chat
    parser = ChatParser()
    parse_result = parser.parse(chat_content, platform)
    
    messages = [{
        'id': f"msg-{i}",
        'timestamp': m.timestamp,
        'sender': m.sender,
        'content': m.content,
        'type': m.type,
        'mentions': m.mentions,
        'reply_to': m.reply_to,
        'reactions': m.reactions
    } for i, m in enumerate(parse_result.messages)]
    
    # Step 2: Extract action items
    extractor = ActionItemExtractor()
    action_items = extractor.extract(messages)
    action_stats = extractor.get_statistics(action_items)
    
    # Step 3: Analyze sentiment
    analyzer = SentimentAnalyzer()
    sentiment = analyzer.analyze(messages)
    
    # Step 4: Detect risks
    detector = RiskDetector()
    risk_data = detector.detect(messages)
    
    # Step 5: Build topic timeline (simplified)
    topics = build_topics(messages)
    
    # Step 6: Extract decisions
    decisions = extract_decisions(messages)
    
    # Step 7: Extract important info
    important_info = extract_important_info(messages)
    
    # Step 8: Generate summary
    config = SummaryConfig(
        level=level,
        language='zh-CN',
        include_sentiment=True,
        include_risks=True
    )
    
    summary_data = {
        'basic_info': {
            'group_name': parse_result.group_name or 'Unknown Group',
            'time_range': parse_result.time_range,
            'participant_count': len(parse_result.participants),
            'message_count': len(messages)
        },
        'topics': topics,
        'decisions': decisions,
        'risks': risk_data['risks'],
        'important_info': important_info,
        'unresolved': [c for c in risk_data['controversies'] if not c.get('resolved')],
        'sentiment': {
            'overall_sentiment': sentiment.overall_sentiment,
            'sentiment_score': sentiment.sentiment_score,
            'emotions': sentiment.emotions,
            'controversy_score': sentiment.controversy_score,
            'key_moments': sentiment.key_moments
        },
        'action_items': [{
            'id': item.id,
            'description': item.description,
            'owner': item.owner,
            'deadline': item.deadline,
            'status': item.status,
            'context': item.context,
            'confidence': item.confidence
        } for item in action_items],
        'action_item_stats': action_stats,
        'messages': messages
    }
    
    generator = SummaryGenerator(config)
    summary_text = generator.generate(summary_data)
    
    return {
        'summary': summary_text,
        'data': summary_data,
        'metadata': {
            'platform': parse_result.platform,
            'level': level,
            'generated_at': datetime.now().isoformat()
        }
    }


def build_topics(messages: list) -> list:
    """Build topic timeline from messages."""
    if not messages:
        return []
    
    # Simple topic grouping by time windows
    topics = []
    current_topic = None
    window_minutes = 30
    
    for msg in messages:
        msg_time = parse_timestamp(msg.get('timestamp', ''))
        
        if current_topic is None:
            current_topic = {
                'id': f"topic-{len(topics)}",
                'title': msg.get('content', '')[:30] + '...',
                'start_time': msg.get('timestamp'),
                'end_time': msg.get('timestamp'),
                'participants': [msg.get('sender')],
                'events': [{'time': msg.get('timestamp'), 'description': msg.get('content', '')[:50]}],
                'decision': None
            }
        else:
            last_time = parse_timestamp(current_topic['end_time'])
            if msg_time and last_time:
                gap = (msg_time - last_time).total_seconds() / 60
                
                if gap > window_minutes:
                    # Start new topic
                    topics.append(current_topic)
                    current_topic = {
                        'id': f"topic-{len(topics)}",
                        'title': msg.get('content', '')[:30] + '...',
                        'start_time': msg.get('timestamp'),
                        'end_time': msg.get('timestamp'),
                        'participants': [msg.get('sender')],
                        'events': [{'time': msg.get('timestamp'), 'description': msg.get('content', '')[:50]}],
                        'decision': None
                    }
                else:
                    # Continue current topic
                    current_topic['end_time'] = msg.get('timestamp')
                    current_topic['participants'].append(msg.get('sender'))
                    current_topic['participants'] = list(set(current_topic['participants']))
                    current_topic['events'].append({'time': msg.get('timestamp'), 'description': msg.get('content', '')[:50]})
    
    if current_topic:
        topics.append(current_topic)
    
    return topics


def extract_decisions(messages: list) -> list:
    """Extract decisions from messages."""
    decisions = []
    decision_patterns = [
        r'决定[是\s]*(.+?)[，。；]',
        r'确定[是\s]*(.+?)[，。；]',
        r'同意[是\s]*(.+?)[，。；]',
        r'结论[是\s]*(.+?)[，。；]',
        r'decided\s*(?:to|that)?\s*(.+?)[.!;]',
        r'agreed\s*(?:to|that)?\s*(.+?)[.!;]',
    ]
    
    for msg in messages:
        content = msg.get('content', '')
        for pattern in decision_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            decisions.extend(matches)
    
    return list(set(decisions))[:10]  # Deduplicate and limit


def extract_important_info(messages: list) -> list:
    """Extract important information (links, docs, etc.)."""
    info = []
    
    # Link patterns
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    # Document patterns
    doc_patterns = [
        r'文档[：:]\s*(\S+)',
        r'链接[：:]\s*(\S+)',
        r'([\w\-]+\.(?:doc|docx|pdf|xlsx|pptx))',
    ]
    
    for msg in messages:
        content = msg.get('content', '')
        
        # Find URLs
        urls = re.findall(url_pattern, content)
        info.extend(urls)
        
        # Find documents
        for pattern in doc_patterns:
            matches = re.findall(pattern, content)
            info.extend(matches)
    
    return list(set(info))[:10]  # Deduplicate and limit


def parse_timestamp(ts: str):
    """Parse timestamp string."""
    from datetime import datetime
    
    if not ts:
        return None
    
    try:
        if 'T' in ts:
            return datetime.fromisoformat(ts.replace('Z', '+00:00').replace('+00:00', ''))
    except ValueError:
        pass
    
    return None


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Summarize group chat conversations')
    parser.add_argument('input_file', help='Path to chat log file')
    parser.add_argument('--platform', '-p', help='Platform type (auto-detect if not specified)')
    parser.add_argument('--level', '-l', default='standard', choices=['basic', 'standard', 'detailed'],
                        help='Summary detail level')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--json', '-j', action='store_true', help='Output full JSON data')
    
    args = parser.parse_args()
    
    # Read input file
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Process
    try:
        result = process_chat(content, args.platform, args.level)
    except Exception as e:
        print(f"Error processing chat: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Output
    if args.json:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = result['summary']
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Summary saved to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    from datetime import datetime
    import re
    main()
