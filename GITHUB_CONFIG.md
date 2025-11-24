# GitHub 提交配置

## 仓库信息
- **仓库地址**: https://github.com/yzh317179958/fiido-customer-service
- **SSH地址**: git@github.com:yzh317179958/fiido-customer-service.git

## SSH Key 信息
- **公钥指纹**: SHA256:VchqgOdfwrfBEzgjAKAHT500WGKk1KFPIAJgdugykK8
- **私钥位置**: 本地 ~/.ssh/ 目录

## 版本历史
| 版本 | 日期 | 主要更新 |
|------|------|----------|
| v2.2.1 | - | 上一版本 |
| v2.3.0 | 2025-11-23 | PRD文档重组 + 企业级部署需求 |
| v2.3.1 | 2025-11-23 | 更新Coze Workflow ID |

## GitHub 提交规范

### 版本管理要求 ⭐ **必须遵守**

**每次提交到 GitHub 必须完成以下步骤**：

#### 1. 更新 README.md 版本记录

**强制要求**：
- ✅ **必须**：在 README.md 中声明版本更新内容
- ✅ **必须**：版本号与 GitHub tag 保持一致
- ✅ **必须**：说明更新了哪些功能
- ✅ **必须**：列出当前系统拥有的所有功能

**README.md 版本记录格式**：
```markdown
## 📊 版本历史

### v2.X.X (YYYY-MM-DD) - 版本标题

**功能完成度**: XX%

**主要更新**:
- ✅ 功能1：具体描述
- ✅ 功能2：具体描述
- 📚 文档更新内容

**当前系统功能**:
- ✅ AI 智能对话
- ✅ 人工接管流程
- ✅ 坐席工作台
- ✅ 实时消息推送
- ... (列出所有已实现功能)

**GitHub**:
- Commit: `哈希值前7位`
- Tag: `v2.X.X`
```

#### 2. 提交到 GitHub

**提交流程**：
```bash
# 1. 添加所有更改
git add .

# 2. 创建提交（包含功能说明）
git commit -m "版本简短说明

详细更新内容:
- 更新内容1
- 更新内容2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 3. 创建版本标签（与 README.md 中的版本号一致）
git tag -a v2.X.X -m "版本说明"

# 4. 推送到远程仓库
git push origin main --tags
```

#### 3. 验证版本一致性

**提交后检查**：
- [ ] README.md 中的版本号 = Git tag 版本号
- [ ] README.md 列出了所有功能
- [ ] GitHub releases 显示正确的版本号

---

## 提交命令模板

```bash
# 标准提交流程
git add .
git commit -m "docs: 文档整理 - 移动过程文档和归档旧版本

主要更新:
- 移动 15 个过程文档到 docs/process/
- 归档 17 个 prd 旧版本到 docs/archive/prd_root_old/
- 创建 docs/README.md 文档导航
- 更新 prd/INDEX.md 反映新结构

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git tag -a v2.3.3 -m "文档整理版本"
git push origin main --tags
```
