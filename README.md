# 📊 Quantum Alpha — WhatsApp Market Research Agent

> **Personal AI research agent that texts you live market intelligence on WhatsApp.**  
> You ask. It researches the internet, SEC filings, and price data. It texts back your next move.

---

## 🧠 What It Does

```
You type on WhatsApp → Agent researches live internet → Texts you insights back
```

- 🔍 **Live news research** via NewsData.io (real-time headlines)
- 📈 **Price & technicals** via yfinance (live stock/crypto data)
- 📄 **SEC filing checks** via EDGAR (10-K, 10-Q, 8-K)
- 🤖 **AI synthesis** via Google Gemini (actionable verdicts)
- 📐 **ATR risk engine** — calculates Stop-Loss & Take-Profit from market volatility
- 🔒 **Owner-only** — only your WhatsApp number can use the bot

---

## 💬 How to Message the Agent

### Step 1 — Start the bot on your Mac
```bash
cd whatsapp_agent
python main.py
```
You'll see:
```
⚡ Quantum Alpha WhatsApp Agent — ONLINE
   Instance : XXXXXXXXXX
   Polling  : every 2 seconds
```

### Step 2 — Open WhatsApp and message your own number

The bot runs on **your own WhatsApp number** via Green API.  
Just open WhatsApp and send a message to yourself, or use WhatsApp Web.

---

## 📱 Commands — What to Type

| What You Type | What the Agent Does |
|---------------|-------------------|
| `hi` | Shows the full command menu |
| `/daily` | Full Daily Alpha Report — macro + top 3 setups |
| `/analyse AAPL` | Deep dive: price, SEC filings, news, AI verdict, SL/TP |
| `/analyse BTC-USD` | Same for any crypto |
| `/risk NVDA` | ATR-based Stop-Loss and Take-Profit levels only |
| `/news Fed interest rates` | Live news on any topic, investor-summarised |
| `/macro` | Global macro briefing — Fed, inflation, GDP themes |
| `Is Apple a buy right now?` | Free-form question — full AI research response |
| `What's moving crypto today?` | Any natural language question |
| `Should I sell my TSLA?` | Specific hold/sell analysis |

### Example Conversation

```
You:   /analyse NVDA

Bot:   🔍 Researching... give me 20–30 seconds.

Bot:   📊 NVDA — Full Analysis
       ━━━━━━━━━━━━━━━━━━━━
       🎯 Entry:  $875.40
       🛑 Stop:   $843.20
       🚀 Target: $971.60
       📐 R:R:    3.0:1

       🔒 Confidence: 4.5/5 ⭐
       1️⃣ Technical:   ✅ Live price data
       2️⃣ Fundamental: ✅ SEC 10-K verified
       3️⃣ News:        ✅ NewsData.io verified
       4️⃣ Macro:       ⚠️ General context
       5️⃣ AI Analysis: ✅ Gemini verified

       🧠 AI Verdict:
       *NVDA — BUY* on pullback to $860–870...
```

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────┐
│                  YOUR WHATSAPP                       │
│   "Is NVDA a buy?" ──────────────────────────────►  │
└──────────────────────┬───────────────────────────────┘
                       │  Green API (your own number)
                       ▼
┌──────────────────────────────────────────────────────┐
│              main.py  (polling bot)                  │
│  ┌──────────────────────────────────────────────┐   │
│  │           security.py (4 gates)              │   │
│  │  1. Owner whitelist (your number only)       │   │
│  │  2. Rate limiter (20 req/hr)                 │   │
│  │  3. Input sanitizer (injection blocker)      │   │
│  │  4. Masking logger (keys never logged)       │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│          research_engine.py                          │
│  ┌────────────┐ ┌───────────┐ ┌──────────────────┐  │
│  │ NewsData   │ │ SEC EDGAR │ │    yfinance       │  │
│  │ (live news)│ │ (filings) │ │ (prices/ATR)      │  │
│  └────────────┘ └───────────┘ └──────────────────┘  │
│              ↓ Gemini AI synthesises ↓               │
│          risk_engine.py (ATR SL/TP)                  │
└──────────────────────┬───────────────────────────────┘
                       │  Reply via Green API
                       ▼
┌──────────────────────────────────────────────────────┐
│                  YOUR WHATSAPP                       │
│   "NVDA — 🟢 BUY Setup. Entry $875..."  ◄────────   │
└──────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
NewsResearchAgent/
│
├── whatsapp_agent/
│   ├── main.py              ← Bot server (Green API polling)
│   ├── research_engine.py   ← News + SEC + AI + price research
│   ├── security.py          ← Whitelist, rate limiter, sanitizer
│   ├── requirements.txt     ← Python dependencies
│   ├── .env.example         ← API key template (copy → .env)
│   └── SETUP.md             ← Full setup guide
│
├── .agent/
│   ├── skills/quantum-alpha/
│   │   ├── SKILL.md         ← Never Lose Money mandate + rules
│   │   ├── agent_config.md  ← Browser verification protocol
│   │   └── scripts/
│   │       └── risk_engine.py  ← ATR Stop-Loss/Take-Profit engine
│   └── customizations/
│       └── workflow.md      ← One-click Daily Alpha Report trigger
│
├── .gitignore               ← Keeps .env and secrets off GitHub
└── README.md                ← This file
```

---

## ⚙️ Setup (15 minutes)

### 1. Clone & install
```bash
git clone https://github.com/WHALASAHIB/NewsResearchAgent.git
cd NewsResearchAgent/whatsapp_agent
pip install -r requirements.txt
```

### 2. Configure API keys
```bash
cp .env.example .env
# Open .env and fill in your keys
```

Required keys:

| Key | Where to Get | Cost |
|-----|-------------|------|
| `GREEN_API_INSTANCE_ID` | [console.greenapi.com](https://console.greenapi.com) — scan QR | Free |
| `GREEN_API_TOKEN` | Same dashboard | Free |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | Free tier |
| `NEWSDATA_API_KEY` | [newsdata.io](https://newsdata.io) | Free (200/day) |

### 3. Run
```bash
python main.py
```

### 4. Message yourself on WhatsApp
Type `hi` → bot responds with the command menu.

---

## 🔒 Security

- **Owner-only whitelist** — only your phone number can interact with the bot
- **Silent drop** on unauthorized access — strangers get no response and no hint a bot exists
- **Rate limiting** — 20 requests/hour maximum
- **Prompt injection blocking** — detects and drops jailbreak attempts
- **API key masking** — keys are never written to logs in plain text
- **`.env` never on GitHub** — all secrets stay local

---

## 🛠 Never Lose Money — Risk Engine

Every trade setup is gated by the ATR-based risk engine:

```
Stop-Loss  = Entry − (ATR × 1.5)
Take-Profit = Entry + (ATR × 3.0)
Minimum R:R = 2:1  →  signals below this are REJECTED
```

Run it standalone:
```bash
python .agent/skills/quantum-alpha/scripts/risk_engine.py --demo
python .agent/skills/quantum-alpha/scripts/risk_engine.py --ticker AAPL
```

---

## 📅 Daily Alpha Report

Trigger any time by typing `/daily` on WhatsApp, or run manually:
```bash
# From the agent prompt:
/daily
```

Report includes:
1. 🌍 Macro briefing (Fed, inflation, key themes)
2. 🎯 Top 3 trade setups with SL/TP and Confidence Score
3. 👁 Watchlist tickers approaching key levels

---

## ⚠️ Disclaimer

This is a **personal research tool**, not financial advice.  
All signals are for educational purposes only.  
Always do your own research before making any investment decision.  
Past performance does not guarantee future results.

---

*Built with Python · Gemini AI · Green API · NewsData.io · yfinance · SEC EDGAR*
