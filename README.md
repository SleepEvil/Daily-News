# 📊 加密日报播报机器人

基于 6551 Daily News API 的加密货币市场日报机器人，支持智能分析和 Telegram 自动播报。

## ✨ 功能特点

| 功能 | 说明 |
|------|------|
| 📰 **多类别覆盖** | 宏观市场、加密货币、DeFi、AI 赛道 |
| 🔥 **智能评级** | A/B/C 等级新闻筛选，只推送高质量内容 |
| 📈 **情绪分析** | 自动分析看涨/看跌信号分布 |
| 💬 **热推聚合** | 同时展示相关热门推文 |
| 🤖 **定时播报** | 支持每日定时自动生成和发送 |
| 📱 **Telegram 推送** | 直接推送到指定频道/群组 |

## 🚀 快速开始

### 1. 安装依赖

```bash
# Python 版本需要
pip install httpx

# 或 Bash 版本需要
curl --version  # 确保已安装
```

### 2. 配置环境变量

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

获取方法：
- Bot Token: 通过 [@BotFather](https://t.me/botfather) 创建机器人
- Chat ID: 发送消息给 [@userinfobot](https://t.me/userinfobot) 获取

### 3. 运行

**Bash 版本（轻量级）:**
```bash
cd crypto-daily-bot
chmod +x daily-report.sh
./daily-report.sh
```

**Python 版本（功能完整）:**
```bash
python3 daily_bot.py
```

## ⚙️ 配置文件

编辑 `config.json` 自定义播报内容：

```json
{
  "categories": [
    {
      "key": "macro",
      "name": "宏观市场",
      "icon": "🌍",
      "priority": 1,
      "enabled": true
    },
    {
      "key": "defi",
      "name": "DeFi",
      "subcategory": "defi",
      "icon": "🦄",
      "enabled": true
    }
  ],
  "report": {
    "max_news_per_category": 3,
    "language": "zh"
  },
  "schedule": {
    "times": ["08:00", "20:00"]
  }
}
```

## 📋 可用类别

| 类别 Key | 子类别 | 说明 |
|----------|--------|------|
| macro | - | 宏观经济、全球市场 |
| crypto | - | 加密货币市场动态 |
| defi | defi | 去中心化金融 |
| nft | nft | NFT 市场 |
| ai | - | AI 与区块链结合 |

## ⏰ 定时任务设置

### 使用 OpenClaw Cron

```bash
# 每天早上 8 点播报
openclaw cron add \
  --name "crypto-daily-morning" \
  --schedule "0 8 * * *" \
  --command "cd ~/.openclaw/workspace/crypto-daily-bot && python3 daily_bot.py"

# 每天晚上 8 点播报
openclaw cron add \
  --name "crypto-daily-evening" \
  --schedule "0 20 * * *" \
  --command "cd ~/.openclaw/workspace/crypto-daily-bot && python3 daily_bot.py"
```

### 使用系统 Cron

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天早上8点）
0 8 * * * cd /root/.openclaw/workspace/crypto-daily-bot && python3 daily_bot.py >> cron.log 2>&1
```

## 📱 日报示例

```
📊 加密市场日报 | 2026年03月17日
⏰ 播报时间: 08:00
🤖 来源: 6551 Daily News
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌍 宏观市场 | 12 条
   情绪: 🟢 看涨 67% / 看跌 20%
──────────────────────────────
🔥 美联储暗示可能在下周降息
   └ 🟢 bullish | 相关: BTC, ETH
   💡 市场普遍预期美联储将在3月会议上维持利率不变，但...

💬 @CryptoWesley:
   "降息预期升温，风险资产迎来反弹窗口..."
   ❤️ 2341 🔄 567

...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 市场整体情绪: 看涨主导 (12🟢 vs 3🔴)
💡 提示: 投资有风险，以上信息仅供参考
🔍 情报工作，准确第一
```

## 🔧 高级用法

### 手动获取特定类别新闻

```bash
# 获取 DeFi 新闻
curl -s "https://ai.6551.io/open/free_hot?category=crypto&subcategory=defi" | jq
```

### 自定义播报格式

修改 `daily_bot.py` 中的 `format_news_item` 方法，自定义输出格式。

## 📝 日志查看

```bash
# 查看运行日志
tail -f bot.log

# 查看缓存的日报
cat .cache/report_20260317.txt
```

## ⚠️ 注意事项

1. **API 限制**: 6551 API 有请求频率限制，避免短时间内大量调用
2. **Telegram 限制**: 单条消息最长 4096 字符，超长内容会被截断
3. **数据延迟**: 新闻数据有缓存，非实时更新

## 🔗 相关链接

- [6551 Daily News GitHub](https://github.com/6551Team/daily-news)
- [6551 API 文档](https://ai.6551.io)
- [OpenClaw 文档](https://docs.openclaw.ai)

## 📄 License

MIT

---

**制作 by EvansKimi** 🔍
