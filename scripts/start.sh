#!/bin/bash

echo "=========================================="
echo "🚀 启动 Fiido 智能客服系统"
echo "=========================================="
echo ""

# 获取脚本所在目录的上级目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ 错误: .env 文件不存在"
    echo "   请先复制 .env.example 并配置相关信息"
    exit 1
fi

# 检查Python依赖
echo "📦 检查依赖..."
python3 -c "import fastapi; import uvicorn; import cozepy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 依赖未安装，正在安装..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败，请手动运行: pip3 install -r requirements.txt"
        exit 1
    fi
fi

echo "✅ 依赖检查完成"
echo ""
echo "=========================================="
echo "🚀 启动后端服务..."
echo "=========================================="
echo ""

# 启动后端（使用 products/ai_chatbot/backend.py）
cd products/ai_chatbot
python3 backend.py
