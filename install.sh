#!/bin/bash
#
# 加密日报播报机器人 - 快速安装脚本
#

set -e

echo "📊 加密日报播报机器人 - 安装脚本"
echo "================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查依赖
echo "🔍 检查依赖..."

if ! command -v curl &> /dev/null; then
    echo "❌ 未安装 curl，请先安装"
    exit 1
fi

if command -v python3 &> /dev/null; then
    echo "✅ Python3 已安装"
    PYTHON_VERSION=$(python3 --version)
    echo "   版本: $PYTHON_VERSION"
    
    # 检查 httpx
    if python3 -c "import httpx" 2>/dev/null; then
        echo "✅ httpx 已安装"
    else
        echo "📦 正在安装 httpx..."
        pip3 install httpx
    fi
else
    echo "⚠️ Python3 未安装，将使用 Bash 版本"
fi

if command -v jq &> /dev/null; then
    echo "✅ jq 已安装"
else
    echo "⚠️ jq 未安装，Bash 版本功能受限"
fi

# 设置权限
echo ""
echo "🔧 设置权限..."
chmod +x daily-report.sh
echo "✅ daily-report.sh 已可执行"

# 创建缓存目录
mkdir -p .cache
echo "✅ 缓存目录已创建"

# 检查环境变量
echo ""
echo "🔐 检查环境变量..."

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
    echo "⚠️ 未设置 TELEGRAM_BOT_TOKEN"
    echo "   请在 ~/.bashrc 或 ~/.zshrc 中添加:"
    echo "   export TELEGRAM_BOT_TOKEN='your_bot_token'"
else
    echo "✅ TELEGRAM_BOT_TOKEN 已设置"
fi

if [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
    echo "⚠️ 未设置 TELEGRAM_CHAT_ID"
    echo "   请在 ~/.bashrc 或 ~/.zshrc 中添加:"
    echo "   export TELEGRAM_CHAT_ID='your_chat_id'"
else
    echo "✅ TELEGRAM_CHAT_ID 已设置"
fi

# 测试 API
echo ""
echo "🌐 测试 6551 API..."
if curl -s --max-time 5 "https://ai.6551.io/open/free_categories" >/dev/null 2>&1; then
    echo "✅ API 连接正常"
else
    echo "⚠️ API 连接失败，请检查网络"
fi

# 生成示例报告
echo ""
echo "📝 生成示例日报..."
if command -v python3 &> /dev/null && python3 -c "import httpx" 2>/dev/null; then
    timeout 30 python3 daily_bot.py > sample_report.txt 2>&1 || echo "⚠️ 示例生成超时或失败"
else
    timeout 30 ./daily-report.sh > sample_report.txt 2>&1 || echo "⚠️ 示例生成超时或失败"
fi

if [ -f sample_report.txt ]; then
    echo "✅ 示例日报已保存到 sample_report.txt"
    echo ""
    echo "预览:"
    head -20 sample_report.txt
fi

echo ""
echo "================================"
echo "✅ 安装完成!"
echo ""
echo "📖 使用方法:"
echo "   1. 手动运行: ./daily-report.sh"
echo "   2. Python版: python3 daily_bot.py"
echo ""
echo "⏰ 设置定时任务:"
echo "   crontab -e"
echo "   0 8 * * * cd $(pwd) && ./daily-report.sh"
echo ""
echo "📝 详细说明请查看 README.md"
echo "================================"
