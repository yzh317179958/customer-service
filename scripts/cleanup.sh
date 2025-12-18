#!/bin/bash
# 项目文档清理脚本

cd /home/yzh/AI客服/鉴权

echo "开始清理冗余文档..."

# 删除 prd/04_任务拆解/ 下所有文件
rm -rf prd/04_任务拆解/*
echo "✅ 已删除 prd/04_任务拆解/ 下的文件"

# 删除 prd/05_验收与记录/
rm -rf prd/05_验收与记录/
echo "✅ 已删除 prd/05_验收与记录/"

# 删除 prd/06_企业部署/
rm -rf prd/06_企业部署/
echo "✅ 已删除 prd/06_企业部署/"

# 删除 prd/01_全局指导/ 下除 README.md 外的文件
rm -f prd/01_全局指导/GUIDE.md
rm -f prd/01_全局指导/prd.md
rm -f prd/01_全局指导/PRD_COMPLETE_v3.0.md
echo "✅ 已精简 prd/01_全局指导/"

# 删除 prd/INDEX.md
rm -f prd/INDEX.md
echo "✅ 已删除 prd/INDEX.md"

# 删除空的 docs 目录（如果存在）
rmdir docs 2>/dev/null && echo "✅ 已删除空的 docs 目录"

# 删除空的 04_任务拆解 目录
rmdir prd/04_任务拆解 2>/dev/null && echo "✅ 已删除空的 prd/04_任务拆解 目录"

echo ""
echo "清理完成！当前 prd/ 目录结构："
find prd/ -type f 2>/dev/null

echo ""
echo "准备提交到 Git..."
git add -A
git status
