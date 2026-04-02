# Output Template

Standard output format for group chat summaries.

## Structure Overview

```
一、基本信息 (Basic Information)
二、脉络梳理 (Topic Timeline)  
三、核心要点 (Key Points)
四、待办事项 (Action Items)
五、后续跟进 (Follow-up Suggestions)
六、其他备注 (Additional Notes)
```

---

## 一、基本信息

| 项目 | 内容 |
|------|------|
| 群名称 | [Group Name] |
| 时间范围 | [YYYY-MM-DD HH:MM ~ HH:MM] |
| 参与人数 | [N]人 |
| 消息总数 | [N]条 |
| 总结类型 | [Basic/Standard/Detailed] |

---

## 二、脉络梳理

按时间段组织话题发展：

### 上午/下午/晚上 ([Time Range])

- [HH:MM] [Event/Topic started]
  - [Key discussion point]
  - [Decision or outcome]
- [HH:MM] [Next event/topic]
  - [Key discussion point]

### 示例

**上午（9:00-12:00）**
- 9:15 产品经理提出 Q2 版本需求评审
  - 核心功能：用户画像、智能推荐
  - 争议点：开发周期是否充足
- 10:30 技术负责人评估开发周期
  - 结论：资源不足，需要砍掉低优先级功能
- 11:45 讨论后决定
  - ✅ 核心功能保留
  - ❌ 低优先级功能延期到 Q3

**下午（14:00-18:00）**
- 14:00 设计师分享新版 UI 原型
  - 链接：[Figma/Design tool]
- 15:20 前端反馈技术难点
  - 问题：复杂动画性能问题
  - 待办：需要技术评估报告
- 16:00 后端确认接口文档
  - 负责人：后端组
  - 截止时间：周四前
- 17:30 确定评审会时间
  - 时间：下周三 14:00
  - 形式：线下会议室

---

## 三、核心要点

### ✅ 已确定事项 (Decisions Made)

1. [Decision 1 with context]
2. [Decision 2 with context]
3. [Decision 3 with context]

### ⚠️ 风险提示 (Risks & Concerns)

- [Risk 1] - [Impact/Context]
- [Risk 2] - [Impact/Context]

### 💡 重要信息 (Key Information)

- [Link/Resource 1]
- [Link/Resource 2]
- [Critical info mentioned]

### 🤔 未决事项 (Unresolved)

- [Issue 1] - [Current status/Next step needed]
- [Issue 2] - [Current status/Next step needed]

### 😊 情感氛围 (Sentiment)

- 整体氛围：[Positive/Neutral/Negative/Mixed]
- 关键情绪点：[Any significant mood shifts]

---

## 四、待办事项

| 事项 | 负责人 | 截止时间 | 状态 | 备注 |
|------|--------|----------|------|------|
| [Task 1] | [@Name] | [Date] | ⏳ 待办 | [Context] |
| [Task 2] | [@Name] | [Date] | ✅ 已完成 | [Context] |
| [Task 3] | [@Name] | [Date] | 🔄 进行中 | [Context] |
| [Task 4] | [@Name] | [Date] | ⏸️ 阻塞 | [Blocker] |

### 状态图标

- ⏳ 待办 (Pending)
- 🔄 进行中 (In Progress)
- ✅ 已完成 (Done)
- ⏸️ 阻塞 (Blocked)
- ❌ 取消 (Cancelled)

---

## 五、后续跟进建议

按时间顺序排列建议的检查点：

1. **[Date/Time]** - [Action to check/perform]
   - 目的：[Why this matters]
   - 负责人：[Who should follow up]

2. **[Date/Time]** - [Action to check/perform]
   - 目的：[Why this matters]
   - 负责人：[Who should follow up]

### 示例

1. **周四 17:00** - 检查接口文档完成情况
   - 目的：确保前端可以按时开始对接
   - 负责人：项目经理

2. **周五 12:00** - 同步前端技术难点评估结果
   - 目的：确定是否需要调整交互方案
   - 负责人：前端负责人

3. **下周三 13:00** - 评审会前提醒
   - 目的：确保所有参会人员准备充分
   - 负责人：技术负责人

---

## 六、其他备注

- **人员变动**: [@Name] 请假/离职/代理
- **假期提醒**: [Holiday dates] 注意时间安排
- **特殊说明**: [Any other important context]
- **资源链接**: [Documents, sheets, tools mentioned]

---

## Summary Level Variations

### Basic Level
Skip sections 2, 5, 6. Keep only:
- Basic Info (simplified)
- Key Points (decisions only)
- Action Items (top 3-5 only)

### Standard Level
Include all sections with moderate detail:
- Topic Timeline: Key milestones only
- Key Points: All subsections
- Action Items: All items with owners

### Detailed Level
Full detail in all sections:
- Topic Timeline: Complete chronological log
- Key Points: Include sentiment analysis, controversy detection
- Action Items: Include full context and dependencies
- Follow-up: Detailed check-in schedule
