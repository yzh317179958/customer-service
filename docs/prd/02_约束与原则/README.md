# 约束与原则文档

本目录包含开发过程中必须遵守的技术限制、约束条件和设计原则。

## 文档说明

| 文档 | 说明 | 重要性 |
|------|------|--------|
| CONSTRAINTS_AND_PRINCIPLES.md | 核心约束与开发原则 | 必读 |
| TECHNICAL_CONSTRAINTS.md | 技术约束详细说明 | 必读 |
| coze.md | Coze API 使用规范 | 重要 |

## 关键约束速查

### Coze API 约束
- `conversation_id` 由 Coze 自动生成，**禁止手动创建**
- 必须使用 `session_name` 实现会话隔离
- JWT Token 中传入 session_name

### 状态机约束
```
bot_active → pending_manual → manual_live → bot_active
```
- 状态转换必须按顺序
- 人工接管期间**必须阻止 AI 对话**

### 开发原则
- 增量式开发，每次只改动必要部分
- 遵循现有代码风格
- 保持向后兼容

## 使用建议

1. **开发前**: 必须完整阅读 CONSTRAINTS_AND_PRINCIPLES.md
2. **接口开发**: 参考 coze.md 了解 API 限制
3. **遇到问题**: 先检查是否违反约束
