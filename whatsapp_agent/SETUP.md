# 📱 Quantum Alpha WhatsApp Agent — Setup Guide

## What This Is

You text a WhatsApp number. It researches the internet in real-time — news, SEC filings, price data — and texts you back with market insights and your next move. All conversation happens on WhatsApp.

```
You (WhatsApp) → Bot receives → Researches live internet → Texts you back insights
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    YOUR PHONE                       │
│   You: "Is NVDA a buy right now?"  (WhatsApp)      │
└──────────────────────┬──────────────────────────────┘
                       │  Twilio routes message
                       ▼
┌─────────────────────────────────────────────────────┐
│              BACKEND SERVER (main.py)               │
│   FastAPI webhook — receives your WhatsApp texts    │
└──────────────────────┬──────────────────────────────┘
                       │  Routes to research engine
                       ▼
┌─────────────────────────────────────────────────────┐
│           RESEARCH ENGINE (research_engine.py)      │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  NewsAPI /   │  │  SEC EDGAR   │  │ yfinance │ │
│  │  Perplexity  │  │  (filings)   │  │ (prices) │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                          ↓                          │
│              GPT-4o synthesises insights            │
│              ATR risk engine calculates SL/TP       │
└──────────────────────┬──────────────────────────────┘
                       │  Sends reply via Twilio
                       ▼
┌─────────────────────────────────────────────────────┐
│                    YOUR PHONE                       │
│   Bot: "NVDA — 🟢 BUY Setup..."    (WhatsApp)      │
└─────────────────────────────────────────────────────┘
```

---

## ⚡ Setup in 4 Steps

### Step 1 — Get Your API Keys (15 min)

| Key | Where to Get | Cost | Required? |
|-----|-------------|------|-----------|
| **Twilio** Account SID + Auth Token | [console.twilio.com](https://console.twilio.com) | Free sandbox | ✅ Yes |
| **OpenAI** API Key | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | ~$5/month | Recommended |
| **NewsAPI** Key | [newsapi.org](https://newsapi.org) | Free (100/day) | Pick one |
| **Perplexity** API Key | [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api) | ~$5/month | Pick one |

### Step 2 — Configure Environment

```bash
cd whatsapp_agent
cp .env.example .env
# Open .env and paste your keys
```

### Step 3 — Install & Run

```bash
pip install -r requirements.txt
python main.py
```

You should see:
```
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Step 4 — Connect Twilio to WhatsApp

**a)** Install ngrok to expose your local server:
```bash
brew install ngrok
ngrok http 8000
```
Copy the `https://xxxx.ngrok.io` URL.

**b)** Go to [Twilio Sandbox for WhatsApp](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn):
- Paste your ngrok URL + `/webhook` as the "When a message comes in" URL
- Set method to `POST`

**c)** Connect your phone:
- WhatsApp the Twilio sandbox number: `+1 415 523 8886`
- Send: `join <your-sandbox-code>` (shown in Twilio console)

**Done!** Text the number and your agent is live.

---

## 💬 Commands You Can Text

| Message | What Happens |
|---------|-------------|
| `hi` or `help` | Shows command menu |
| `/daily` | Full daily alpha report |
| `/analyse AAPL` | Deep dive on Apple stock |
| `/analyse BTC-USD` | Bitcoin analysis |
| `/risk NVDA` | Stop-loss + take-profit levels |
| `/news Fed interest rates` | Latest news on any topic |
| `/macro` | Global macro briefing |
| `Is Apple a buy right now?` | Free-form question |
| `What's moving crypto today?` | Free-form question |
| `Should I hold or sell TSLA?` | Free-form question |

---

## 📅 Scheduled Daily Reports (Optional)

To get an automatic daily report at 09:35 UTC, add to your crontab:

```bash
crontab -e
```

Add this line:
```
35 9 * * 1-5 curl -X POST http://localhost:8000/scheduled-report
```

Or use the macOS LaunchAgent (ask me to set this up).

---

## 🔒 Security Notes

- Never commit your `.env` file (it's in `.gitignore`)
- Use Twilio request validation in production
- Your conversations are private — no data stored on disk

---

## 🛠 File Structure

```
whatsapp_agent/
├── main.py             ← FastAPI webhook server
├── research_engine.py  ← Internet research + AI synthesis
├── requirements.txt    ← Python dependencies
├── .env.example        ← API key template
└── SETUP.md            ← This file
```
