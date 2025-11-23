# 验收与记录文档

本目录包含验收标准、测试规范和实施记录。

## 文档说明

| 文档 | 说明 | 用途 |
|------|------|------|
| ACCEPTANCE_CRITERIA_v1.0.md | 详细验收标准 | 功能验收 |
| TESTING_GUIDE.md | 测试流程规范 | 测试参考 |
| implementation_notes.md | 实施过程笔记 | 开发参考 |
| PRD_REVIEW.md | PRD 评审记录 | 历史记录 |
| DOCUMENTATION_SUMMARY.md | 文档总结 | 索引参考 |

## 验收流程

### 1. 功能开发完成
```bash
# 运行回归测试
./tests/regression_test.sh
# 预期: 12/12 通过
```

### 2. 手动测试
参考 TESTING_GUIDE.md 的测试用例

### 3. 验收检查
对照 ACCEPTANCE_CRITERIA_v1.0.md 检查

## 测试命令速查

```bash
# 健康检查
curl http://localhost:8000/api/health

# 会话列表
curl "http://localhost:8000/api/sessions?status=pending_manual"

# 统计信息
curl http://localhost:8000/api/sessions/stats
```

## 核心测试场景

1. AI 对话测试
2. 人工升级测试
3. 坐席接入测试
4. 会话释放测试
5. 会话转接测试
6. 防抢单测试
7. 非工作时间测试
8. 会话隔离测试

## 使用建议

1. **测试人员**: 主要参考 TESTING_GUIDE.md 和 ACCEPTANCE_CRITERIA_v1.0.md
2. **开发人员**: 开发完成后参考测试规范自测
3. **新功能**: 添加对应的测试用例到 TESTING_GUIDE.md
