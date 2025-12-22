---
name: git-commit-helper
description: 生成符合 Fiido 规范的 Git commit 消息，自动计算版本号，检查提交规范。当用户说"帮我提交"、"生成 commit 消息"、"提交代码"时自动激活
---

# Git 提交规范助手

## 何时使用
- 用户说"帮我提交"
- 用户说"生成 commit 消息"
- 用户说"提交代码"
- 每个 Step 完成后

## 版本号规则

| 版本位 | 何时增加 | 示例 |
|--------|----------|------|
| 补丁版本 | Bug 修复、小功能 | v5.3.9 → v5.3.10 |
| 次版本 | 新功能、新模块 | v5.3.10 → v5.4.0 |
| 主版本 | 重大架构变更 | v5.4.0 → v6.0.0 |

## 提交前检查（必须全部通过）

- [ ] 修改文件数 < 10 个
- [ ] 新增代码行数 < 500 行
- [ ] 测试已通过
- [ ] 文档已更新（progress.md、architecture.md）
- [ ] 没有包含敏感信息（.env、credentials 等）

## commit 消息格式

```
类型: Step N - 描述 vX.X.X

详细说明（可选）

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## 类型前缀

| 类型 | 用途 | 示例 |
|------|------|------|
| feat | 新功能 | feat: Step 3 - 登录页面 v7.3.0 |
| fix | Bug 修复 | fix: 修复订单查询空指针 v7.2.1 |
| refactor | 重构 | refactor: 统一使用多站点服务 v7.2.0 |
| docs | 文档 | docs: 更新 memory-bank 文档 v7.1.1 |
| test | 测试 | test: 添加会话测试 v7.1.2 |
| chore | 杂项 | chore: 更新依赖版本 v7.1.3 |

## 完整提交流程

```bash
# 1. 查看改动
git status
git diff

# 2. 确认改动数量
# 文件数 < 10、代码行数 < 500

# 3. 添加文件
git add .

# 4. 提交（使用 HEREDOC 格式）
git commit -m "$(cat <<'EOF'
feat: Step N - 步骤描述 vX.X.X

详细说明（可选）

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 5. 打标签
git tag vX.X.X

# 6. 推送（等用户确认后）
git push origin main --tags
```

## 示例

### 新功能提交
```bash
git commit -m "$(cat <<'EOF'
feat: Step 5 - 登录页与鉴权守卫 v7.5.0

实现坐席登录、token 存储、401 自动跳转

- 创建登录页面组件
- 实现请求拦截器自动注入 Authorization header
- 实现 401 响应拦截器自动跳转登录
- 使用 React Context 管理认证状态

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Bug 修复提交
```bash
git commit -m "$(cat <<'EOF'
fix: 修复商品状态判断逻辑 v7.2.1

- 区分 fulfillment.status 和 shipment_status
- 优先级：退款状态 > shipment_status > fulfillment_status

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Git 安全协议（禁止事项）

- ❌ 禁止更新 git config
- ❌ 禁止运行破坏性命令（push --force、hard reset）
- ❌ 禁止跳过 hooks（--no-verify）
- ❌ 禁止 force push 到 main/master
- ❌ 禁止未经用户确认就 push

## 如果 pre-commit hook 修改了文件

1. 检查作者：`git log -1 --format='%an %ae'`
2. 检查未推送：`git status` 显示 "Your branch is ahead"
3. 如果都满足：可以 amend 提交
4. 否则：创建新的 commit
