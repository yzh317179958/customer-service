#!/bin/bash
# Fiido 智能服务平台 - 启动脚本
# 支持全家桶模式和独立模式

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# 默认配置
MODE="all"
PORT_BACKEND=8000
PORT_AI_CHATBOT=8001
PORT_AGENT_WORKBENCH=8002

# 帮助信息
show_help() {
    echo "Fiido 智能服务平台启动脚本"
    echo ""
    echo "用法: $0 [选项] [模式]"
    echo ""
    echo "模式:"
    echo "  all               启动所有服务（全家桶模式，默认）"
    echo "  ai-chatbot        仅启动 AI 客服"
    echo "  agent-workbench   仅启动坐席工作台"
    echo ""
    echo "选项:"
    echo "  -h, --help        显示帮助信息"
    echo "  -d, --debug       启用调试模式"
    echo "  -r, --reload      启用热重载（开发模式）"
    echo ""
    echo "示例:"
    echo "  $0                    # 启动全家桶"
    echo "  $0 ai-chatbot         # 仅启动 AI 客服"
    echo "  $0 -r ai-chatbot      # 热重载模式启动 AI 客服"
}

# 解析参数
DEBUG=false
RELOAD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        -r|--reload)
            RELOAD=true
            shift
            ;;
        all|ai-chatbot|agent-workbench)
            MODE=$1
            shift
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 切换到项目目录
cd "$PROJECT_ROOT"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${RED}错误: .env 文件不存在${NC}"
    echo "   请先配置 .env 文件"
    exit 1
fi

# 加载环境变量
set -a
source .env
set +a
echo -e "${GREEN}已加载 .env 配置${NC}"

# 检查Python依赖
echo -e "${BLUE}检查依赖...${NC}"
if ! python3 -c "import fastapi; import uvicorn; import cozepy" 2>/dev/null; then
    echo -e "${YELLOW}依赖未安装，正在安装...${NC}"
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}依赖安装失败${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}依赖检查完成${NC}"

# 构建 uvicorn 参数
UVICORN_ARGS=""
if [ "$RELOAD" = true ]; then
    UVICORN_ARGS="$UVICORN_ARGS --reload"
fi
if [ "$DEBUG" = true ]; then
    UVICORN_ARGS="$UVICORN_ARGS --log-level debug"
fi

echo ""

# 启动服务
case $MODE in
    all)
        echo -e "${BLUE}=========================================="
        echo -e "  启动全家桶模式"
        echo -e "==========================================${NC}"
        echo -e "   端口: $PORT_BACKEND"
        echo ""
        uvicorn backend:app --host 0.0.0.0 --port $PORT_BACKEND $UVICORN_ARGS
        ;;
    ai-chatbot)
        echo -e "${BLUE}=========================================="
        echo -e "  启动 AI 客服（独立模式）"
        echo -e "==========================================${NC}"
        echo -e "   端口: $PORT_AI_CHATBOT"
        echo ""
        export AI_CHATBOT_PORT=$PORT_AI_CHATBOT
        uvicorn products.ai_chatbot.main:app --host 0.0.0.0 --port $PORT_AI_CHATBOT $UVICORN_ARGS
        ;;
    agent-workbench)
        echo -e "${BLUE}=========================================="
        echo -e "  启动坐席工作台（独立模式）"
        echo -e "==========================================${NC}"
        echo -e "   端口: $PORT_AGENT_WORKBENCH"
        echo ""
        export AGENT_WORKBENCH_PORT=$PORT_AGENT_WORKBENCH
        uvicorn products.agent_workbench.main:app --host 0.0.0.0 --port $PORT_AGENT_WORKBENCH $UVICORN_ARGS
        ;;
esac
