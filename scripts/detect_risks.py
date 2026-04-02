#!/usr/bin/env python3
"""
Detect risks, blockers, and controversies in chat conversations.
"""

import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class Risk:
    id: str
    type: str  # timeline, resource, technical, dependency, communication, other
    description: str
    severity: str  # high, medium, low
    probability: str  # likely, possible, unlikely
    impact: str
    owner: Optional[str]
    mitigation: Optional[str]
    source: str


@dataclass
class Blocker:
    description: str
    blocking: str
    impact: str
    affected: List[str]


@dataclass
class Controversy:
    topic: str
    positions: List[str]
    participants: List[str]
    intensity: float  # 0.0-1.0
    resolved: bool


class RiskDetector:
    """Detect risks and issues in conversations."""
    
    # Risk type patterns
    RISK_PATTERNS = {
        'timeline': [
            r'来不及|时间[不够紧]|delay|延期|推迟|at risk',
            r'赶不及|来不及|时间紧|周期[不够]|schedule',
        ],
        'resource': [
            r'人手[不够不足]|资源[不够不足]|short on|lack of',
            r'预算[不够不足]|经费|cost|budget',
            r'忙不过来|overload|overloaded',
        ],
        'technical': [
            r'技术难点|技术挑战|technical challenge|complex',
            r'不确定|uncertain|not sure|unknown',
            r'性能问题|performance|瓶颈|bottleneck',
            r'兼容性|compatibility|冲突|conflict',
        ],
        'dependency': [
            r'依赖|depends? on|rely on|blocked by',
            r'等.+完成|waiting for|pending',
            r'前置|prerequisite|先决条件',
        ],
        'communication': [
            r'沟通|communication|协调|coordinate',
            r'信息不|信息不对称|unclear|ambiguous',
            r'理解不|misunderstand|误解',
        ],
    }
    
    # Severity indicators
    SEVERITY_HIGH = ['严重', 'critical', 'blocker', 'blocking', '必须', 'must', '严重', '高风险']
    SEVERITY_MEDIUM = ['重要', 'important', '有风险', '需要注意', 'medium']
    
    # Blocker patterns
    BLOCKER_PATTERNS = [
        r'被?阻塞|blocked|卡住|stuck',
        r'无法继续|cannot proceed|不能进行',
        r'等.+才能|waiting.*to',
    ]
    
    # Controversy patterns
    DISAGREEMENT_PATTERNS = [
        r'但是|不过|然而|可是|but|however|though',
        r'不同意|不赞成|反对|质疑|disagree|object',
        r'我觉得不行|这样不好|有问题|concern',
        r'另一种看法|different view|alternative',
    ]
    
    def __init__(self):
        self.risk_counter = 0
    
    def detect(self, messages: List[Dict], topics: List[Dict] = None) -> Dict:
        """Detect all risks and issues."""
        risks = self._detect_risks(messages)
        blockers = self._detect_blockers(messages)
        missing_info = self._detect_missing_info(messages)
        dependencies = self._detect_dependencies(messages)
        controversies = self._detect_controversies(messages, topics)
        
        return {
            'risks': [asdict(r) for r in risks],
            'blockers': [asdict(b) for b in blockers],
            'missing_info': missing_info,
            'dependencies': dependencies,
            'controversies': [asdict(c) for c in controversies],
            'summary': {
                'total_risks': len(risks),
                'high_severity': sum(1 for r in risks if r.severity == 'high'),
                'blockers': len(blockers),
                'unresolved_controversies': sum(1 for c in controversies if not c.resolved),
            }
        }
    
    def _detect_risks(self, messages: List[Dict]) -> List[Risk]:
        """Detect risks from messages."""
        risks = []
        
        for msg in messages:
            content = msg.get('content', '')
            sender = msg.get('sender', 'Unknown')
            
            for risk_type, patterns in self.RISK_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        risk = self._create_risk(msg, risk_type, pattern)
                        if risk:
                            risks.append(risk)
        
        # Deduplicate
        return self._deduplicate_risks(risks)
    
    def _create_risk(self, msg: Dict, risk_type: str, pattern: str) -> Optional[Risk]:
        """Create a risk object from message."""
        content = msg.get('content', '')
        
        # Extract risk description
        description = self._extract_risk_description(content, pattern)
        if not description:
            return None
        
        # Determine severity
        severity = self._determine_severity(content)
        
        # Determine probability
        probability = self._determine_probability(content)
        
        # Extract impact
        impact = self._extract_impact(content)
        
        # Find owner
        owner = self._extract_owner(content, msg.get('sender'))
        
        # Suggest mitigation
        mitigation = self._suggest_mitigation(risk_type, description)
        
        self.risk_counter += 1
        
        return Risk(
            id=f"risk-{self.risk_counter:03d}",
            type=risk_type,
            description=description,
            severity=severity,
            probability=probability,
            impact=impact,
            owner=owner,
            mitigation=mitigation,
            source=msg.get('id', '')
        )
    
    def _extract_risk_description(self, content: str, matched_pattern: str) -> Optional[str]:
        """Extract clean risk description."""
        # Get sentence containing the risk
        sentences = re.split(r'[。！；.!?;]', content)
        
        for sentence in sentences:
            if re.search(matched_pattern, sentence, re.IGNORECASE):
                # Clean up
                desc = sentence.strip()
                desc = re.sub(r'^[但是|不过|然而|可是|but|however]\s*', '', desc)
                if len(desc) > 10 and len(desc) < 200:
                    return desc
        
        return None
    
    def _determine_severity(self, content: str) -> str:
        """Determine risk severity."""
        content_lower = content.lower()
        
        for indicator in self.SEVERITY_HIGH:
            if indicator in content or indicator in content_lower:
                return 'high'
        
        for indicator in self.SEVERITY_MEDIUM:
            if indicator in content or indicator in content_lower:
                return 'medium'
        
        return 'low'
    
    def _determine_probability(self, content: str) -> str:
        """Determine risk probability."""
        # Check for certainty indicators
        likely_indicators = ['肯定', '一定', 'will', 'definitely', 'certainly']
        unlikely_indicators = ['可能不', 'unlikely', 'probably not', '也许不']
        
        content_lower = content.lower()
        
        if any(i in content or i in content_lower for i in likely_indicators):
            return 'likely'
        elif any(i in content or i in content_lower for i in unlikely_indicators):
            return 'unlikely'
        
        return 'possible'
    
    def _extract_impact(self, content: str) -> str:
        """Extract impact description."""
        # Look for impact patterns
        impact_patterns = [
            r'影响\s*(.+?)[，。；]',
            r'导致\s*(.+?)[，。；]',
            r'会\s*(.+?)[，。；]',
            r'impact\s*(.+?)[.!;]',
            r'result in\s*(.+?)[.!;]',
        ]
        
        for pattern in impact_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:100]
        
        return '需要进一步评估'
    
    def _extract_owner(self, content: str, default_sender: str) -> Optional[str]:
        """Extract risk owner."""
        # Look for @mentions
        mentions = re.findall(r'@(\S+)', content)
        if mentions:
            return mentions[0]
        
        return default_sender
    
    def _suggest_mitigation(self, risk_type: str, description: str) -> Optional[str]:
        """Suggest mitigation strategy."""
        mitigations = {
            'timeline': '评估是否可以调整范围或增加资源',
            'resource': '考虑资源调配或外部支持',
            'technical': '安排技术评审或寻求专家支持',
            'dependency': '建立依赖跟踪机制，提前沟通',
            'communication': '安排同步会议，明确沟通渠道',
            'other': '持续监控，准备应急预案',
        }
        
        return mitigations.get(risk_type, '持续监控')
    
    def _detect_blockers(self, messages: List[Dict]) -> List[Blocker]:
        """Detect blockers from messages."""
        blockers = []
        
        for msg in messages:
            content = msg.get('content', '')
            
            for pattern in self.BLOCKER_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    blocker = self._create_blocker(msg)
                    if blocker:
                        blockers.append(blocker)
        
        return blockers
    
    def _create_blocker(self, msg: Dict) -> Optional[Blocker]:
        """Create a blocker object."""
        content = msg.get('content', '')
        
        # Extract what's blocked
        blocked_match = re.search(r'(\S+?)(被?阻塞|blocked|卡住)', content, re.IGNORECASE)
        blocked = blocked_match.group(1) if blocked_match else '某项工作'
        
        # Extract blocking factor
        blocking_match = re.search(r'(?:因为|由于|等|waiting for|blocked by)\s*(.+?)[，。；]', content, re.IGNORECASE)
        blocking = blocking_match.group(1) if blocking_match else '未知因素'
        
        return Blocker(
            description=f"{blocked} 被阻塞",
            blocking=blocking,
            impact='影响后续工作进展',
            affected=[msg.get('sender', 'Unknown')]
        )
    
    def _detect_missing_info(self, messages: List[Dict]) -> List[str]:
        """Detect missing information."""
        missing = []
        
        patterns = [
            r'不清楚|不知道|unknown|unclear|不确定',
            r'需要确认|待确认|to be confirmed|TBD',
            r'缺少|缺乏|missing|lack of',
        ]
        
        for msg in messages:
            content = msg.get('content', '')
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # Extract what's missing
                    match = re.search(r'(?:不清楚|不知道|缺少|缺乏)\s*(.+?)[，。；]', content)
                    if match:
                        info = match.group(1).strip()
                        if len(info) > 3 and len(info) < 100:
                            missing.append(info)
        
        return list(set(missing))[:5]  # Deduplicate and limit
    
    def _detect_dependencies(self, messages: List[Dict]) -> List[Dict]:
        """Detect dependencies between tasks."""
        dependencies = []
        
        for msg in messages:
            content = msg.get('content', '')
            
            # Look for dependency patterns
            dep_match = re.search(r'等\s*@?(\S+?)\s*完成', content)
            if dep_match:
                dependencies.append({
                    'task': '当前工作',
                    'depends_on': dep_match.group(1),
                    'type': 'completion'
                })
            
            dep_match2 = re.search(r'依赖\s*@?(\S+?)[，。；]', content)
            if dep_match2:
                dependencies.append({
                    'task': '当前工作',
                    'depends_on': dep_match2.group(1),
                    'type': 'dependency'
                })
        
        return dependencies
    
    def _detect_controversies(self, messages: List[Dict], topics: List[Dict] = None) -> List[Controversy]:
        """Detect controversies and disagreements."""
        controversies = []
        
        # Group messages by topic
        if topics:
            for topic in topics:
                topic_msgs = topic.get('messages', [])
                controversy = self._analyze_topic_controversy(topic, topic_msgs)
                if controversy and controversy.intensity > 0.3:
                    controversies.append(controversy)
        else:
            # Analyze all messages
            controversy = self._analyze_message_thread(messages)
            if controversy and controversy.intensity > 0.3:
                controversies.append(controversy)
        
        return controversies
    
    def _analyze_topic_controversy(self, topic: Dict, messages: List[Dict]) -> Optional[Controversy]:
        """Analyze controversy within a topic."""
        if not messages:
            return None
        
        # Count disagreement indicators
        disagreement_count = 0
        participants = set()
        positions = []
        
        for msg in messages:
            content = msg.get('content', '')
            sender = msg.get('sender', 'Unknown')
            participants.add(sender)
            
            for pattern in self.DISAGREEMENT_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    disagreement_count += 1
                    # Extract position
                    position = self._extract_position(content)
                    if position:
                        positions.append(f"{sender}: {position}")
        
        # Calculate intensity
        intensity = min(disagreement_count / max(len(messages) / 3, 1), 1.0)
        
        # Check if resolved
        resolved = self._check_resolved(messages)
        
        if intensity > 0.2:
            return Controversy(
                topic=topic.get('title', 'Unknown topic'),
                positions=positions[:3],
                participants=list(participants),
                intensity=intensity,
                resolved=resolved
            )
        
        return None
    
    def _analyze_message_thread(self, messages: List[Dict]) -> Optional[Controversy]:
        """Analyze controversy in message thread."""
        return self._analyze_topic_controversy({'title': 'General discussion'}, messages)
    
    def _extract_position(self, content: str) -> Optional[str]:
        """Extract position statement from message."""
        # Look for opinion patterns
        patterns = [
            r'我觉得\s*(.+?)[，。；]',
            r'我认为\s*(.+?)[，。；]',
            r'我的看法是\s*(.+?)[，。；]',
            r'I think\s*(.+?)[.!;]',
            r'In my opinion\s*(.+?)[.!;]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:50]
        
        return None
    
    def _check_resolved(self, messages: List[Dict]) -> bool:
        """Check if controversy was resolved."""
        resolution_indicators = ['同意', '确定', '决定', 'agree', 'decided', 'confirmed', 'resolved']
        
        # Check last few messages for resolution
        for msg in messages[-3:]:
            content = msg.get('content', '').lower()
            if any(indicator in content for indicator in resolution_indicators):
                return True
        
        return False
    
    def _deduplicate_risks(self, risks: List[Risk]) -> List[Risk]:
        """Deduplicate similar risks."""
        seen = set()
        unique = []
        
        for risk in risks:
            # Create signature
            sig = (risk.type, risk.description[:30])
            if sig not in seen:
                seen.add(sig)
                unique.append(risk)
        
        return unique


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python detect_risks.py <parsed_messages.json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    messages = data.get('messages', [])
    topics = data.get('topics', [])
    
    detector = RiskDetector()
    result = detector.detect(messages, topics)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
