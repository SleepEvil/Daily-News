#!/usr/bin/env python3
"""
加密日报播报机器人 - Python 版本
功能更强大，支持智能分析和信号聚合
"""

import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """新闻条目"""
    id: int
    title: str
    source: str
    link: str
    score: int
    grade: str
    signal: str
    summary_zh: str
    summary_en: str
    coins: List[str]
    published_at: str


@dataclass
class TweetItem:
    """推文条目"""
    author: str
    handle: str
    content: str
    url: str
    likes: int
    retweets: int
    replies: int
    posted_at: str
    relevance: str


class NewsAPIClient:
    """6551 新闻 API 客户端"""
    
    def __init__(self, base_url: str = "https://ai.6551.io"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    async def get_categories(self) -> List[Dict]:
        """获取新闻分类"""
        try:
            resp = await self.client.get(f"{self.base_url}/open/free_categories")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"获取分类失败: {e}")
            return []
    
    async def get_hot_news(self, category: str, subcategory: str = "") -> Dict:
        """获取热点新闻"""
        try:
            params = {"category": category}
            if subcategory:
                params["subcategory"] = subcategory
            
            resp = await self.client.get(
                f"{self.base_url}/open/free_hot",
                params=params
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"获取 {category} 新闻失败: {e}")
            return {"success": False, "error": str(e)}


class DailyReportGenerator:
    """日报生成器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.api = NewsAPIClient(config.get("api", {}).get("base_url"))
    
    def clean_html(self, text: str) -> str:
        """清理 HTML 标签"""
        if not text:
            return ""
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', ' ', text)
        # 清理多余空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def get_signal_emoji(self, signal: str) -> str:
        """信号表情"""
        signal = signal.lower() if signal else "neutral"
        return {
            "bullish": "🟢",
            "long": "🟢",
            "bearish": "🔴",
            "short": "🔴",
            "neutral": "⚪"
        }.get(signal, "⚪")
    
    def get_grade_emoji(self, grade: str) -> str:
        """等级表情"""
        return {
            "A": "🔥",
            "B": "📌",
            "C": "•"
        }.get(grade.upper(), "•")
    
    def format_news_item(self, item: Dict, index: int) -> str:
        """格式化单条新闻"""
        grade = self.get_grade_emoji(item.get("grade", ""))
        signal = self.get_signal_emoji(item.get("signal", ""))
        coins = item.get("coins", [])
        coin_str = f"相关: {', '.join(coins)}" if coins else ""
        
        # 清理 HTML 标签
        title = self.clean_html(item.get("title", ""))[:100]
        summary = self.clean_html(item.get("summary_zh", ""))[:80]
        
        lines = [
            f"{grade} {title}",
            f"   └ {signal} {item.get('signal', 'neutral')} | {coin_str}",
        ]
        if summary:
            lines.append(f"   💡 {summary}")
        
        return "\n".join(lines)
    
    def format_tweet(self, tweet: Dict) -> str:
        """格式化推文"""
        content = tweet.get("content", "")[:100]
        if len(tweet.get("content", "")) > 100:
            content += "..."
        
        metrics = tweet.get("metrics", {})
        likes = metrics.get("likes", 0)
        retweets = metrics.get("retweets", 0)
        
        return (
            f"💬 @{tweet.get('handle', '')}:\n"
            f"   \"{content}\"\n"
            f"   ❤️ {likes} 🔄 {retweets}"
        )
    
    def analyze_sentiment(self, items: List[Dict]) -> Dict:
        """分析情绪分布"""
        bullish_signals = ["bullish", "long"]
        bearish_signals = ["bearish", "short"]
        
        bullish = sum(1 for i in items if i.get("signal", "").lower() in bullish_signals)
        bearish = sum(1 for i in items if i.get("signal", "").lower() in bearish_signals)
        neutral = len(items) - bullish - bearish
        
        total = len(items) if items else 1
        return {
            "bullish_pct": (bullish / total) * 100,
            "bearish_pct": (bearish / total) * 100,
            "neutral_pct": (neutral / total) * 100,
            "dominant": "bullish" if bullish > bearish else "bearish" if bearish > bullish else "neutral"
        }
    
    async def generate_category_report(self, cat_config: Dict) -> str:
        """生成单个类别的报告"""
        key = cat_config["key"]
        name = cat_config["name"]
        icon = cat_config.get("icon", "📰")
        subcategory = cat_config.get("subcategory", "")
        
        logger.info(f"获取 {name} 类别新闻...")
        
        response = await self.api.get_hot_news(key, subcategory)
        
        if not response.get("success"):
            return f"⚠️ {icon} {name}: 暂时无法获取数据\n"
        
        news_data = response.get("news", {})
        tweets_data = response.get("tweets", {})
        
        news_items = news_data.get("items", [])[:self.config["report"]["max_news_per_category"]]
        tweet_items = tweets_data.get("items", [])[:self.config["report"]["max_tweets_per_category"]]
        
        # 情绪分析
        sentiment = self.analyze_sentiment(news_items)
        sentiment_emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}
        
        lines = [
            f"{icon} {name} | {news_data.get('count', 0)} 条",
            f"   情绪: {sentiment_emoji[sentiment['dominant']]} 看涨 {sentiment['bullish_pct']:.0f}% / 看跌 {sentiment['bearish_pct']:.0f}%",
            "─" * 30,
        ]
        
        # 添加新闻
        for i, item in enumerate(news_items, 1):
            lines.append(self.format_news_item(item, i))
            lines.append("")
        
        # 添加热门推文
        if tweet_items:
            lines.append(self.format_tweet(tweet_items[0]))
            lines.append("")
        
        return "\n".join(lines)
    
    async def generate_report(self) -> str:
        """生成完整日报"""
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")
        time_str = now.strftime("%H:%M")
        
        # 获取启用的类别
        categories = [
            c for c in self.config.get("categories", [])
            if c.get("enabled", True)
        ]
        categories.sort(key=lambda x: x.get("priority", 99))
        
        # 生成各类别报告
        category_reports = []
        for cat in categories:
            try:
                report = await self.generate_category_report(cat)
                category_reports.append(report)
            except Exception as e:
                logger.error(f"生成 {cat['name']} 报告失败: {e}")
                category_reports.append(f"⚠️ {cat['name']}: 数据获取失败\n")
        
        # 组合完整报告
        header = f"""📊 加密市场日报 | {date_str}
⏰ 播报时间: {time_str}
🤖 来源: 6551 Daily News
{'━' * 35}
"""
        
        body = "\n\n".join(category_reports)
        
        # 添加市场摘要
        summary = self.generate_summary(category_reports)
        
        footer = f"""
{'━' * 35}
{summary}
💡 提示: 投资有风险，以上信息仅供参考
🔍 情报工作，准确第一
"""
        
        await self.api.close()
        return header + "\n\n" + body + footer
    
    def generate_summary(self, reports: List[str]) -> str:
        """生成市场摘要"""
        # 简单统计看涨/看跌信号数量
        bullish_count = sum(r.count("🟢") for r in reports)
        bearish_count = sum(r.count("🔴") for r in reports)
        
        if bullish_count > bearish_count * 1.5:
            return f"📈 市场整体情绪: 看涨主导 ({bullish_count}🟢 vs {bearish_count}🔴)"
        elif bearish_count > bullish_count * 1.5:
            return f"📉 市场整体情绪: 看跌主导 ({bullish_count}🟢 vs {bearish_count}🔴)"
        else:
            return f"📊 市场整体情绪: 分歧较大 ({bullish_count}🟢 vs {bearish_count}🔴)"


class TelegramSender:
    """Telegram 消息发送器"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(self, text: str) -> bool:
        """发送消息"""
        try:
            # 将 Markdown 格式转换为 HTML
            html_text = self.convert_to_html(text)
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": html_text[:4000],  # Telegram 限制
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True
                    }
                )
                resp.raise_for_status()
                result = resp.json()
                return result.get("ok", False)
        except Exception as e:
            logger.error(f"发送 Telegram 消息失败: {e}")
            return False
    
    def convert_to_html(self, text: str) -> str:
        """将文本转换为 HTML 格式"""
        # 转义 HTML 特殊字符
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        
        # 简单格式化
        lines = text.split("\n")
        html_lines = []
        
        for line in lines:
            if line.startswith("📊") or line.startswith("📈") or line.startswith("📉"):
                html_lines.append(f"<b>{line}</b>")
            elif line.startswith("━") or line.startswith("─"):
                html_lines.append("<code>" + line + "</code>")
            else:
                html_lines.append(line)
        
        return "\n".join(html_lines)


async def main():
    """主函数"""
    # 加载配置
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {
            "api": {"base_url": "https://ai.6551.io"},
            "report": {"max_news_per_category": 3, "max_tweets_per_category": 1},
            "categories": [
                {"key": "macro", "name": "宏观市场", "icon": "🌍", "priority": 1, "enabled": True},
                {"key": "crypto", "name": "加密货币", "icon": "₿", "priority": 2, "enabled": True},
                {"key": "defi", "name": "DeFi", "subcategory": "defi", "icon": "🦄", "priority": 3, "enabled": True},
                {"key": "ai", "name": "AI 赛道", "icon": "🤖", "priority": 4, "enabled": True},
            ]
        }
    
    # 生成日报
    generator = DailyReportGenerator(config)
    logger.info("开始生成加密日报...")
    
    report = await generator.generate_report()
    
    # 保存到文件
    cache_dir = Path(".cache")
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"日报已保存: {cache_file}")
    
    # 发送到 Telegram
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if bot_token and chat_id:
        sender = TelegramSender(bot_token, chat_id)
        logger.info("正在发送到 Telegram...")
        if await sender.send_message(report):
            logger.info("✅ Telegram 发送成功")
        else:
            logger.error("❌ Telegram 发送失败")
    else:
        logger.info("未配置 Telegram，仅保存到本地")
        print(report)
    
    logger.info("日报播报完成")


if __name__ == "__main__":
    asyncio.run(main())
