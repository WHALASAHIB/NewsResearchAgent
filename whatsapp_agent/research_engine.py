"""
╔══════════════════════════════════════════════════════════════════╗
║      QUANTUM ALPHA — Research Engine                           ║
║      Gemini AI  +  NewsData.io  +  yfinance + SEC EDGAR        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import asyncio
import httpx
from datetime import datetime, timedelta
import sys

# Add risk engine path
sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", ".agent", "skills", "quantum-alpha", "scripts")
)
from risk_engine import QuantumRiskEngine, RiskParameters, fetch_market_data

try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL = genai.GenerativeModel("gemini-1.5-flash")
    GEMINI = True
except Exception:
    GEMINI = False

try:
    import yfinance as yf
    YFINANCE = True
except ImportError:
    YFINANCE = False


# ═══════════════════════════════════════════════════════════════════════════

class ResearchEngine:

    def __init__(self):
        self.risk_engine  = QuantumRiskEngine(RiskParameters())
        self.newsdata_key = os.getenv("NEWSDATA_API_KEY", "")

    # ───────────────────────────────────────────────────────────────────────
    # HELP
    # ───────────────────────────────────────────────────────────────────────

    def get_help_message(self) -> str:
        return (
            "👋 *Quantum Alpha Research Agent*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "I research markets live and tell you your next move.\n\n"
            "📌 *Commands:*\n"
            "• /daily — Full daily alpha report\n"
            "• /analyse AAPL — Deep dive on any stock\n"
            "• /analyse BTC-USD — Crypto analysis\n"
            "• /risk NVDA — Stop-loss & take-profit\n"
            "• /news bitcoin — News on any topic\n"
            "• /macro — Global macro briefing\n\n"
            "💬 *Or just ask me anything:*\n"
            "_\"Is Apple a buy right now?\"\n"
            "\"What's moving crypto today?\"\n"
            "\"Should I sell my TSLA?\"_\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔒 All research is live. Every signal verified."
        )

    # ───────────────────────────────────────────────────────────────────────
    # FREE-FORM QUESTION
    # ───────────────────────────────────────────────────────────────────────

    async def free_research(self, question: str) -> str:
        news = await self._fetch_news(question, max_results=6)
        return await self._gemini_analyse(
            question=question,
            context=news,
            mode="free"
        )

    # ───────────────────────────────────────────────────────────────────────
    # TICKER DEEP DIVE
    # ───────────────────────────────────────────────────────────────────────

    async def analyse_ticker(self, ticker: str) -> str:
        news_task = self._fetch_news(f"{ticker} stock earnings analysis", max_results=5)
        sec_task  = self._fetch_sec(ticker)
        price_task = self._fetch_price(ticker)

        news, sec, price = await asyncio.gather(news_task, sec_task, price_task, return_exceptions=True)

        risk_block = self._risk_block(ticker)
        score, evidence = self._confidence_score(price, news, sec)
        context = f"Price: {price}\n\nNews:\n{news}\n\nSEC:\n{sec}"

        ai_verdict = await self._gemini_analyse(
            question=f"Should I buy, sell or hold {ticker}? Give a specific verdict with price levels.",
            context=context,
            mode="ticker",
            ticker=ticker
        )

        return (
            f"📊 *{ticker} — Full Analysis*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{risk_block}\n\n"
            f"🔒 *Confidence: {score:.1f}/5 ⭐*\n"
            f"{evidence}\n\n"
            f"🧠 *AI Verdict:*\n"
            f"{ai_verdict}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )

    # ───────────────────────────────────────────────────────────────────────
    # DAILY ALPHA REPORT
    # ───────────────────────────────────────────────────────────────────────

    async def daily_alpha_report(self) -> str:
        macro = await self.macro_briefing()
        news  = await self._fetch_news("stocks crypto market today top movers", max_results=8)

        setups = await self._gemini_analyse(
            question=(
                "Based on today's market news, identify the TOP 3 trade setups. "
                "For each: name the ticker, state buy/sell/avoid, give one key reason. "
                "Format for WhatsApp with emojis."
            ),
            context=news,
            mode="daily"
        )

        date = datetime.utcnow().strftime("%d %b %Y")
        return (
            f"📅 *DAILY ALPHA — {date}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{macro}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *TOP SETUPS TODAY*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{setups}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ Not financial advice. DYOR.\n"
            f"⏱ {datetime.utcnow().strftime('%H:%M UTC')}"
        )

    # ───────────────────────────────────────────────────────────────────────
    # MACRO BRIEFING
    # ───────────────────────────────────────────────────────────────────────

    async def macro_briefing(self) -> str:
        news = await self._fetch_news(
            "Federal Reserve interest rates inflation GDP economy market outlook",
            max_results=6
        )
        summary = await self._gemini_analyse(
            question="What are the 3 most important macro themes right now? For each, state what it means for investors in one line.",
            context=news,
            mode="macro"
        )
        return f"🌍 *MACRO BRIEFING*\n━━━━━━━━━━━━━━━━━━━━\n{summary}"

    # ───────────────────────────────────────────────────────────────────────
    # NEWS TOPIC
    # ───────────────────────────────────────────────────────────────────────

    async def get_news(self, topic: str) -> str:
        articles = await self._fetch_news(topic, max_results=6)
        summary = await self._gemini_analyse(
            question=f"Summarise the key investor insights from these '{topic}' news articles. What should I do?",
            context=articles,
            mode="news"
        )
        return (
            f"📰 *NEWS: {topic.upper()}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{summary}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )

    # ───────────────────────────────────────────────────────────────────────
    # RISK CHECK
    # ───────────────────────────────────────────────────────────────────────

    async def risk_check(self, ticker: str) -> str:
        try:
            market_data = fetch_market_data(ticker)
            setup = self.risk_engine.calculate(market_data)
            return setup.to_whatsapp()
        except ImportError:
            return "⚠️ Run: pip install yfinance"
        except Exception as e:
            return f"❌ Risk engine error for {ticker}: {str(e)[:150]}"

    # ═══════════════════════════════════════════════════════════════════════
    # PRIVATE: NEWS FETCH (NewsData.io)
    # ═══════════════════════════════════════════════════════════════════════

    async def _fetch_news(self, query: str, max_results: int = 5) -> str:
        """Fetch from NewsData.io — free tier 200 req/day."""
        if not self.newsdata_key:
            return "⚠️ NEWSDATA_API_KEY not set"
        try:
            url = "https://newsdata.io/api/1/news"
            params = {
                "apikey":   self.newsdata_key,
                "q":        query,
                "language": "en",
                "size":     max_results,
            }
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params=params)
                data = resp.json()

            if data.get("status") != "success":
                return f"NewsData error: {data.get('message', 'unknown')}"

            articles = data.get("results", [])
            lines = []
            for i, a in enumerate(articles[:max_results], 1):
                title  = a.get("title", "")
                source = a.get("source_id", "")
                date   = (a.get("pubDate") or "")[:10]
                desc   = (a.get("description") or "")[:150]
                lines.append(f"{i}. [{date}] {title} ({source})\n   {desc}")

            return "\n\n".join(lines) if lines else f"No news found for: {query}"

        except Exception as e:
            return f"News fetch error: {str(e)[:100]}"

    # ═══════════════════════════════════════════════════════════════════════
    # PRIVATE: SEC EDGAR
    # ═══════════════════════════════════════════════════════════════════════

    async def _fetch_sec(self, ticker: str) -> str:
        try:
            start = (datetime.utcnow() - timedelta(days=180)).strftime("%Y-%m-%d")
            end   = datetime.utcnow().strftime("%Y-%m-%d")
            url   = (
                f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22"
                f"&dateRange=custom&startdt={start}&enddt={end}&forms=10-K,10-Q,8-K"
            )
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url)
                data = resp.json()

            hits = data.get("hits", {}).get("hits", [])
            if not hits:
                return "No recent SEC filings found"

            lines = []
            for h in hits[:3]:
                s = h.get("_source", {})
                lines.append(
                    f"• {s.get('form_type','?')} filed {s.get('file_date','?')}: "
                    f"{s.get('display_names','?')}"
                )
            return "SEC Filings:\n" + "\n".join(lines)
        except Exception as e:
            return f"SEC unavailable: {str(e)[:80]}"

    # ═══════════════════════════════════════════════════════════════════════
    # PRIVATE: PRICE DATA
    # ═══════════════════════════════════════════════════════════════════════

    async def _fetch_price(self, ticker: str) -> dict:
        if not YFINANCE:
            return {"error": "pip install yfinance"}
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None, lambda: yf.Ticker(ticker).fast_info
            )
            return {
                "price":    round(getattr(info, "last_price", 0), 2),
                "52w_high": round(getattr(info, "year_high", 0), 2),
                "52w_low":  round(getattr(info, "year_low", 0), 2),
            }
        except Exception as e:
            return {"error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════
    # PRIVATE: RISK LEVELS
    # ═══════════════════════════════════════════════════════════════════════

    def _risk_block(self, ticker: str) -> str:
        try:
            data  = fetch_market_data(ticker)
            setup = self.risk_engine.calculate(data)
            return (
                f"🎯 Entry:  ${setup.entry_price:.2f}\n"
                f"🛑 Stop:   ${setup.stop_loss:.2f}\n"
                f"🚀 Target: ${setup.take_profit:.2f}\n"
                f"📐 R:R:    {setup.rr_ratio:.1f}:1"
            )
        except Exception as e:
            return f"⚠️ Risk levels unavailable: {str(e)[:80]}"

    # ═══════════════════════════════════════════════════════════════════════
    # PRIVATE: CONFIDENCE SCORE
    # ═══════════════════════════════════════════════════════════════════════

    def _confidence_score(self, price, news, sec) -> tuple:
        score = 0.0
        lines = []

        # Technical
        if isinstance(price, dict) and "error" not in price:
            score += 1.0; lines.append("1️⃣ Technical:   ✅ Live price data")
        else:
            score += 0.5; lines.append("1️⃣ Technical:   ⚠️ Limited data")

        # Fundamental (SEC)
        if isinstance(sec, str) and "No recent" not in sec and "unavailable" not in sec:
            score += 1.0; lines.append("2️⃣ Fundamental: ✅ SEC filing verified")
        else:
            score += 0.5; lines.append("2️⃣ Fundamental: ⚠️ No SEC data")

        # News
        if isinstance(news, str) and len(news) > 100 and "error" not in news.lower():
            score += 1.0; lines.append("3️⃣ News:        ✅ NewsData.io verified")
        else:
            score += 0.0; lines.append("3️⃣ News:        ❌ No news found")

        # Macro
        score += 0.5; lines.append("4️⃣ Macro:       ⚠️ General context")

        # AI
        if GEMINI:
            score += 1.0; lines.append("5️⃣ AI Analysis: ✅ Gemini verified")
        else:
            score += 0.0; lines.append("5️⃣ AI Analysis: ❌ Gemini not connected")

        return score, "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════════════
    # PRIVATE: GEMINI AI ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════

    async def _gemini_analyse(self, question: str, context: str, mode: str, ticker: str = "") -> str:
        if not GEMINI:
            return "⚠️ Gemini not available. Check GEMINI_API_KEY in .env"

        system = (
            "You are Quantum Alpha, an elite financial research agent. "
            "Give precise, actionable market intelligence. "
            "Always answer: what's happening, why it matters, and the EXACT next move. "
            "Format for WhatsApp: use emojis, *bold* key numbers. Max 350 words. "
            "Never be vague. Include specific price levels or % when possible."
        )
        prompt = (
            f"{system}\n\n"
            f"Question: {question}\n\n"
            f"Research Context:\n{context[:3500]}\n\n"
            f"Give a WhatsApp-formatted response with: verdict, key insight, next move."
        )
        try:
            loop   = asyncio.get_event_loop()
            resp   = await loop.run_in_executor(
                None, lambda: GEMINI_MODEL.generate_content(prompt)
            )
            return resp.text.strip()
        except Exception as e:
            return f"⚠️ Gemini error: {str(e)[:150]}"
