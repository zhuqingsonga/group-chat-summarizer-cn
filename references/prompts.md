# Prompts

LLM prompts for extraction and analysis tasks.

## Message Parsing

### Parse Raw Messages

```
You are a chat log parser. Extract structured data from the following chat messages.

Input format: [Platform name if known, or "Unknown"]
[Raw chat log]

Extract and output JSON:
{
  "platform": "detected platform name",
  "messages": [
    {
      "timestamp": "ISO 8601 format",
      "sender": "username",
      "content": "message text",
      "type": "text|image|file|system",
      "mentions": ["@user1", "@user2"],
      "reply_to": "username or null",
      "reactions": ["emoji1", "emoji2"]
    }
  ],
  "participants": ["user1", "user2"],
  "time_range": {
    "start": "ISO timestamp",
    "end": "ISO timestamp"
  }
}

Rules:
- Normalize all timestamps to ISO 8601
- Extract @mentions from content
- Identify message types (text/image/file/system)
- Detect reply/thread relationships
- Note any reactions/emoji
```

---

## Topic Analysis

### Identify Topics and Timeline

```
Analyze the following chat messages and identify discussion topics with timeline.

Messages:
[JSON array of parsed messages]

Output JSON:
{
  "topics": [
    {
      "id": "topic-1",
      "title": "Short topic name",
      "start_time": "ISO timestamp",
      "end_time": "ISO timestamp",
      "participants": ["user1", "user2"],
      "key_messages": [message_ids],
      "summary": "Brief description of discussion",
      "decision": "Decision made or null",
      "status": "resolved|ongoing|blocked"
    }
  ],
  "timeline": [
    {
      "time": "ISO timestamp",
      "event": "What happened",
      "topic_id": "topic-1"
    }
  ]
}

Guidelines:
- Group related messages into topics
- Identify natural breaks in conversation
- Note when topics shift
- Mark decisions and conclusions
- Identify unresolved or blocked items
```

---

## Action Item Extraction

### Extract Tasks and Assignments

```
Extract all action items, tasks, and assignments from the chat.

Messages:
[JSON array of messages]

Output JSON:
{
  "action_items": [
    {
      "id": "task-1",
      "description": "Clear task description",
      "owner": "@username or null",
      "deadline": "ISO date or relative time",
      "deadline_type": "explicit|inferred|none",
      "status": "pending|done|in_progress|blocked",
      "source_message": "message id",
      "context": "Surrounding conversation context"
    }
  ],
  "statistics": {
    "total": 10,
    "with_owner": 8,
    "with_deadline": 5,
    "completed": 2
  }
}

Extraction rules:
- Look for verbs: "完成", "准备", "检查", "review", "prepare", "check"
- Identify owners: @mentions, "由...负责", "XXX来做"
- Parse deadlines: "周四前", "next week", "by Friday", "ASAP"
- Detect status: "已完成", "done", "pending", "blocked"
- Include context for clarity
```

---

## Sentiment Analysis

### Analyze Conversation Tone

```
Analyze the sentiment and emotional tone of this conversation.

Messages:
[JSON array of messages]

Output JSON:
{
  "overall_sentiment": "positive|neutral|negative|mixed",
  "sentiment_score": 0.7,
  "breakdown": {
    "positive": 0.6,
    "neutral": 0.3,
    "negative": 0.1
  },
  "emotions": ["excited", "concerned", "supportive"],
  "key_moments": [
    {
      "time": "ISO timestamp",
      "description": "What happened",
      "sentiment_shift": "positive_to_negative"
    }
  ],
  "concerns": ["List of expressed concerns"],
  "positives": ["List of positive moments"]
}

Analysis guidelines:
- Consider emoji usage and reactions
- Note tone changes throughout conversation
- Identify conflicts or disagreements
- Recognize supportive or collaborative moments
- Flag escalations or de-escalations
```

---

## Risk Detection

### Identify Risks and Blockers

```
Identify risks, concerns, blockers, and potential issues from the conversation.

Messages:
[JSON array of messages]

Output JSON:
{
  "risks": [
    {
      "id": "risk-1",
      "type": "timeline|resource|technical|dependency|other",
      "description": "Clear risk description",
      "severity": "high|medium|low",
      "probability": "likely|possible|unlikely",
      "impact": "Description of potential impact",
      "owner": "Who raised it or is responsible",
      "mitigation": "Suggested mitigation or null",
      "source": "message id"
    }
  ],
  "blockers": [
    {
      "description": "What's blocked",
      "blocking": "What's causing the block",
      "impact": "Who/what is affected"
    }
  ],
  "missing_info": [
    "Information gaps identified"
  ],
  "dependencies": [
    {
      "task": "Dependent task",
      "depends_on": "Prerequisite task or info"
    }
  ]
}

Detection patterns:
- Timeline concerns: "来不及", "时间紧", "delay", "at risk"
- Resource issues: "人手不够", "资源不足", "short on resources"
- Technical risks: "技术难点", "不确定", "complexity"
- Dependencies: "等XXX完成", "blocked by", "depends on"
- Unknowns: "不清楚", "需要确认", "TBD"
```

---

## Summary Generation

### Generate Structured Summary

```
Generate a comprehensive group chat summary based on the analyzed data.

Input Data:
{
  "basic_info": {...},
  "topics": [...],
  "action_items": [...],
  "sentiment": {...},
  "risks": [...],
  "messages": [...]
}

Summary Level: [basic|standard|detailed]
Language: [zh-CN|en|...]

Generate output following this exact structure:

一、基本信息
[Table with group name, time range, participants, message count]

二、脉络梳理
[Chronological timeline of topics with key events]

三、核心要点
[Decisions, risks, important info, unresolved items, sentiment]

四、待办事项
[Table with tasks, owners, deadlines, status]

五、后续跟进
[Follow-up suggestions with dates]

六、其他备注
[Additional notes, absences, links]

Guidelines:
- Use clear, concise language
- Highlight critical information
- Include specific names and dates
- Note any uncertainties
- Suggest concrete next steps
```

---

## Follow-up Suggestions

### Generate Follow-up Recommendations

```
Based on the conversation summary, generate follow-up suggestions.

Summary Data:
[Full summary data]

Current Time: [ISO timestamp]

Output:
{
  "follow_ups": [
    {
      "date": "YYYY-MM-DD",
      "time": "HH:MM (optional)",
      "action": "What to check or do",
      "purpose": "Why this matters",
      "owner": "Who should follow up",
      "priority": "high|medium|low"
    }
  ],
  "reminders": [
    "Things to remember for next meeting"
  ],
  "preparation": [
    "What to prepare before next discussion"
  ]
}

Generate suggestions for:
- Deadline checkpoints (1 day before, day of)
- Progress check-ins
- Decision follow-ups
- Risk monitoring
- Information requests
```

---

## Format-Specific Parsing

### Feishu Format

```
Parse Feishu chat export format.

Input:
[Raw Feishu export text or JSON]

Handle:
- System messages: [系统消息]
- Reply threads: [回复 XXX]
- @mentions: @username
- Rich content: links, files, images
- Recalled messages: [已撤回]
- Pin notifications: [置顶消息]

Output standardized message format.
```

### Discord Format

```
Parse Discord chat export (JSON).

Handle:
- User mentions: <@user_id>
- Role mentions: <@&role_id>
- Channel mentions: <#channel_id>
- Emoji: :emoji_name: and Unicode
- Reactions: emoji + count
- Embeds: links, images, rich content
- Thread replies
- Edit history

Output standardized message format.
```

---

## Quality Checks

### Validate Summary Quality

```
Review the generated summary for quality and completeness.

Summary:
[Generated summary text]

Original Messages:
[Original chat messages]

Check:
1. Are all key decisions captured?
2. Are all action items with owners included?
3. Are deadlines accurate?
4. Is the timeline correct?
5. Are there any missing important details?
6. Is the sentiment analysis accurate?
7. Are risks and blockers identified?

Output:
{
  "quality_score": 0.95,
  "issues": [
    {
      "type": "missing|incorrect|unclear",
      "description": "What's wrong",
      "suggestion": "How to fix"
    }
  ],
  "confidence": "high|medium|low"
}
```
