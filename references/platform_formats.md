# Platform Formats

Supported chat log formats and parsing guidelines.

## Format Detection

The system auto-detects format based on:
1. File extension (.json, .csv, .txt)
2. Content patterns (timestamps, username formats)
3. Metadata fields present

---

## Feishu (飞书)

### Export Format

**Text Export:**
```
2024-04-01 09:15:30 张三
产品经理提出 Q2 版本需求评审，大家看看这个文档

2024-04-01 09:16:45 李四
好的，我看看

2024-04-01 09:20:12 王五 [回复 张三]
核心功能是什么？
```

**JSON Export:**
```json
{
  "messages": [
    {
      "sender": "张三",
      "timestamp": "2024-04-01T09:15:30+08:00",
      "content": "产品经理提出 Q2 版本需求评审...",
      "type": "text",
      "mentions": ["@所有人"]
    }
  ]
}
```

### Parsing Notes
- Timestamp format: `YYYY-MM-DD HH:MM:SS`
- Username separator: Space after timestamp
- Reply indicator: `[回复 XXX]`
- System messages: Marked with `[系统消息]`

---

## DingTalk (钉钉)

### Export Format

**Text Export:**
```
[2024-04-01 09:15] 张三
产品经理提出 Q2 版本需求评审

[2024-04-01 09:16] 李四
好的，我看看
```

**JSON Export:**
```json
{
  "conversation": {
    "title": "产品技术沟通群",
    "messages": [
      {
        "senderNick": "张三",
        "createdAt": "2024-04-01T09:15:30.000+0800",
        "content": {"text": "产品经理提出 Q2 版本需求评审"},
        "msgType": "text"
      }
    ]
  }
}
```

### Parsing Notes
- Timestamp in brackets: `[YYYY-MM-DD HH:MM]`
- Rich content types: text, image, file, link
- @mentions: `@张三` format

---

## WeChat Work (企业微信)

### Export Format

**Text Export:**
```
张三 2024-04-01 09:15:30
产品经理提出 Q2 版本需求评审

李四 2024-04-01 09:16:45
好的，我看看
```

**JSON Export:**
```json
{
  "room_name": "产品技术沟通群",
  "message_list": [
    {
      "sender": "张三",
      "send_time": "2024-04-01 09:15:30",
      "content": "产品经理提出 Q2 版本需求评审",
      "msg_type": "text"
    }
  ]
}
```

### Parsing Notes
- Username first, then timestamp
- Simple text format
- Limited metadata in exports

---

## Discord

### Export Format (JSON)

```json
{
  "guild": {
    "name": "Dev Team",
    "channels": [
      {
        "name": "general",
        "messages": [
          {
            "author": {
              "username": "alice",
              "discriminator": "1234"
            },
            "timestamp": "2024-04-01T09:15:30.123Z",
            "content": "Let's discuss the Q2 roadmap",
            "mentions": [],
            "reactions": [
              {"emoji": "👍", "count": 3}
            ],
            "thread": {
              "name": "Q2 Planning",
              "messages": [...]
            }
          }
        ]
      }
    ]
  }
}
```

### Parsing Notes
- ISO 8601 timestamps (UTC)
- Reactions indicate sentiment
- Threaded conversations supported
- Rich embeds for links/files

---

## Slack
n### Export Format (JSON)

```json
{
  "type": "message",
  "user": "U12345678",
  "text": "Let's discuss the Q2 roadmap",
  "ts": "1711962930.123456",
  "thread_ts": "1711962930.123456",
  "reply_count": 5,
  "reactions": [
    {
      "name": "thumbsup",
      "count": 3,
      "users": ["U123", "U456", "U789"]
    }
  ]
}
```

### Parsing Notes
- Unix timestamp with microseconds
- User IDs need mapping to names
- Thread support via `thread_ts`
- Reactions for sentiment analysis

---

## Microsoft Teams

### Export Format

**JSON:**
```json
{
  "conversation": {
    "id": "19:xxx@thread.tacv2",
    "messages": [
      {
        "from": {
          "user": {
            "displayName": "Alice"
          }
        },
        "createdDateTime": "2024-04-01T09:15:30Z",
        "body": {
          "content": "Let's discuss the Q2 roadmap",
          "contentType": "text"
        },
        "replies": [...]
      }
    ]
  }
}
```

### Parsing Notes
- ISO 8601 timestamps
- HTML content possible
- Reply threading supported

---

## Telegram

### Export Format (JSON)

```json
{
  "name": "Dev Team",
  "type": "supergroup",
  "messages": [
    {
      "id": 12345,
      "type": "message",
      "date": "2024-04-01T09:15:30",
      "from": "Alice",
      "text": "Let's discuss the Q2 roadmap"
    }
  ]
}
```

### Parsing Notes
- Simple format
- Text can be array (for entities)
- Forwarded messages marked

---

## Generic Plain Text

### Supported Patterns

**Pattern 1: Timestamp at start**
```
[2024-04-01 09:15:30] Alice: Message text
[2024-04-01 09:16:45] Bob: Reply text
```

**Pattern 2: Username first**
```
Alice [09:15:30]: Message text
Bob [09:16:45]: Reply text
```

**Pattern 3: Simple lines**
```
Alice: Message text
Bob: Reply text
```

### Auto-Detection Rules

1. Look for timestamp patterns
2. Identify username separators (:, -, space)
3. Detect reply/thread indicators
4. Recognize @mentions and URLs

---

## Date/Time Format Handling

### Supported Formats

- `YYYY-MM-DD HH:MM:SS` (China platforms)
- `YYYY-MM-DD HH:MM` (Short form)
- `MM/DD/YYYY HH:MM AM/PM` (US format)
- `DD/MM/YYYY HH:MM` (EU format)
- ISO 8601: `2024-04-01T09:15:30Z`
- Unix timestamp: `1711962930`

### Timezone Handling

- Assume local timezone if not specified
- Convert all to consistent timezone for summary
- Note timezone in basic info section

---

## Special Content Types

### @Mentions
- Feishu/DingTalk/WeChat: `@username`
- Discord: `<@user_id>` or `@username`
- Slack: `<@U12345678>`

### Media Messages
- Images: `[图片]` / `[Image]` / URL
- Files: `[文件: filename]` / attachment object
- Links: URL with optional preview

### System Messages
- Join/leave notifications
- Name changes
- Topic changes
- Pinned messages
