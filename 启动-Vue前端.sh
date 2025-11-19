#!/bin/bash

echo "======================================"
echo "  Fiido 智能客服 - Vue 3 前端启动"
echo "======================================"
echo ""

# 检查后端是否运行
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "❌ 后端未运行！"
    echo "请先启动后端："
    echo "  cd /home/yzh/AI客服/鉴权"
    echo "  python3 backend.py"
    echo ""
    exit 1
fi

echo "✅ 后端运行正常"
echo ""

# 进入前端目录
cd /home/yzh/AI客服/鉴权/frontend

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，正在安装依赖..."
    npm install
    echo ""
fi

echo "🚀 启动 Vue 开发服务器..."
echo ""
echo "访问地址："
echo "  http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止服务"
echo "======================================"
echo ""

npm run dev
