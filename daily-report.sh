#!/bin/bash
#
# 加密日报播报机器人 - 主脚本
# 使用 6551 Daily News API 获取热点新闻
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.json"
CACHE_DIR="${SCRIPT_DIR}/.cache"
LOG_FILE="${SCRIPT_DIR}/bot.log"

# 确保缓存目录存在
mkdir -p "$CACHE_DIR"

# API 基础配置
API_BASE="${DAILY_NEWS_API_BASE:-https://ai.6551.io}"
MAX_ROWS="${DAILY_NEWS_MAX_ROWS:-10}"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 获取新闻分类
get_categories() {
    curl -s -X GET "${API_BASE}/open/free_categories" 2>/dev/null || echo '[]'
}

# 获取热点新闻
get_hot_news() {
    local category="$1"
    local subcategory="${2:-}"
    
    local url="${API_BASE}/open/free_hot?category=${category}"
    if [ -n "$subcategory" ]; then
        url="${url}&subcategory=${subcategory}"
    fi
    
    curl -s -X GET "$url" 2>/dev/null || echo '{"success":false}'
}

# 格式化日报
format_daily_report() {
    local date_str=$(date '+%Y年%m月%d日')
    local time_str=$(date '+%H:%M')
    
    cat << EOF
📊 加密市场日报 | ${date_str}
⏰ 播报时间: ${time_str}
━━━━━━━━━━━━━━━━━━━━━━

EOF
    
    # 依次获取各类别新闻
    local categories=("macro" "crypto" "defi" "ai")
    local names=("宏观市场" "加密货币" "DeFi" "AI 赛道")
    
    for i in "${!categories[@]}"; do
        local cat="${categories[$i]}"
        local name="${names[$i]}"
        
        log "获取 ${name} 类别新闻..."
        
        local response=$(get_hot_news "$cat")
        
        if echo "$response" | jq -e '.success == true' >/dev/null 2>&1; then
            format_category_section "$name" "$response"
        else
            echo "⚠️ ${name}: 暂时无法获取数据"
            echo ""
        fi
        
        # 避免请求过快
        sleep 0.5
    done
    
    cat << EOF
━━━━━━━━━━━━━━━━━━━━━━
💡 数据由 6551 Daily News 提供
🤖 生成 by EvansKimi
EOF
}

# 格式化单个类别
format_category_section() {
    local category_name="$1"
    local response="$2"
    
    # 提取新闻数量
    local news_count=$(echo "$response" | jq '.news.count // 0')
    local tweet_count=$(echo "$response" | jq '.tweets.count // 0')
    
    echo "📰 ${category_name} | ${news_count} 条新闻 · ${tweet_count} 条热推"
    echo "─────────────────────"
    
    # 格式化前3条重要新闻
    echo "$response" | jq -r '.news.items[:3] | 
        .[] | 
        if .grade == "A" then "🔥"
        elif .grade == "B" then "📌"
        else "•" end + " " +
        .title + "\n" +
        "  └ " +
        (if .signal == "bullish" then "🟢 看涨"
         elif .signal == "bearish" then "🔴 看跌"
         else "⚪ 中性" end) +
        " | " +
        (if .coins | length > 0 then "相关: " + (.coins | join(", ")) else "" end) +
        "\n"
    '
    
    # 添加热门推文（如果有）
    local top_tweet=$(echo "$response" | jq -r '.tweets.items[0] | 
        select(. != null) |
        "💬 热推: " + .author + "\n" +
        "   " + .content[:100] + 
        (if (.content | length) > 100 then "..." else "" end) + "\n"
    ')
    
    if [ -n "$top_tweet" ] && [ "$top_tweet" != "null" ]; then
        echo "$top_tweet"
    fi
    
    echo ""
}

# 发送 Telegram 消息
send_to_telegram() {
    local message="$1"
    local bot_token="${TELEGRAM_BOT_TOKEN:-}"
    local chat_id="${TELEGRAM_CHAT_ID:-}"
    
    if [ -z "$bot_token" ] || [ -z "$chat_id" ]; then
        log "错误: 未配置 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID"
        return 1
    fi
    
    # 转义特殊字符
    local escaped_msg=$(echo "$message" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g')
    
    curl -s -X POST "https://api.telegram.org/bot${bot_token}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": \"${chat_id}\",
            \"text\": \"${escaped_msg}\",
            \"parse_mode\": \"HTML\",
            \"disable_web_page_preview\": true
        }" 2>/dev/null | jq -r '.ok // false'
}

# 主函数
main() {
    log "开始生成加密日报..."
    
    # 生成日报内容
    local report=$(format_daily_report)
    
    # 保存到缓存文件
    local cache_file="${CACHE_DIR}/report_$(date +%Y%m%d).txt"
    echo "$report" > "$cache_file"
    
    log "日报已生成: $cache_file"
    
    # 如果配置了 Telegram，则发送
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
        log "正在发送到 Telegram..."
        if send_to_telegram "$report"; then
            log "✅ 发送成功"
        else
            log "❌ 发送失败"
        fi
    else
        log "未配置 Telegram，仅保存到本地"
        echo "$report"
    fi
    
    log "日报播报完成"
}

# 运行
main "$@"
