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

## 提交命令
```bash
# 添加远程仓库
git remote add origin git@github.com:yzh317179958/fiido-customer-service.git

# 提交并打标签
git add .
git commit -m "版本说明"
git tag -a v2.3.0 -m "版本说明"
git push origin main --tags
```
