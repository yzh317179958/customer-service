#!/bin/bash

# Fiido 智能客服 - 快速测试脚本

echo "=========================================="
echo "🧪 Fiido 智能客服系统 - 配置检查"
echo "=========================================="
echo ""

# 检查必需文件
echo "📋 检查必需文件..."
FILES=("backend.py" "index2.html" "fiido2.png" ".env" "private_key.pem" "requirements.txt")
MISSING=0

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - 文件缺失"
        MISSING=1
    fi
done

echo ""

# 检查 Python 依赖
echo "📦 检查 Python 依赖..."
if python3 -c "import fastapi, cozepy, httpx, pydantic, dotenv" 2>/dev/null; then
    echo "✅ Python 依赖已安装"
else
    echo "⚠️  部分依赖未安装，请运行: pip install -r requirements.txt"
fi

echo ""

# 获取本机 IP
echo "🌐 网络信息..."
echo "本机 IP 地址："
hostname -I | awk '{print "   " $1}'

LOCAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "📝 使用说明"
echo "=========================================="
echo ""
echo "1. 启动服务："
echo "   python3 backend.py"
echo ""
echo "2. 本地访问："
echo "   http://localhost:8000/"
echo ""
echo "3. 局域网访问（告诉别人）："
echo "   http://$LOCAL_IP:8000/"
echo ""
echo "4. 查看 API 文档："
echo "   http://localhost:8000/docs"
echo ""
echo "=========================================="

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "⚠️  警告：存在缺失文件，请先完成配置"
    exit 1
fi

echo ""
echo "✅ 所有检查通过！可以启动服务了"
echo ""
