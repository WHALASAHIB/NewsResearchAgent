# ⚡ Quantum Alpha Strategist — Daily Alpha Report Workflow
**Location:** `.agent/customizations/workflow.md`  
**Trigger:** One-click / single prompt invocation  
**Output:** WhatsApp-ready Daily Alpha Report

---

## 🚀 ONE-CLICK TRIGGER

To run the full Daily Alpha Report, send this exact prompt to the agent:

```
/daily-alpha
```

Or the long form:

```
Run the Quantum Alpha Strategist Daily Alpha Report for today. 
Use the SKILL.md mandate, verify all data via Browser, 
run risk_engine.py for each setup, and output in WhatsApp format.
```

---

## 📋 WORKFLOW STEPS (Auto-Executed)

The agent executes these steps sequentially when triggered:

### PHASE 1 — Macro Briefing (Pre-Market)

```
1. Browser → Perplexity: "market moving news today {DATE}"
2. Browser → Fed Reserve: check for FOMC statements
3. Browser → SEC EDGAR: overnight 8-K filings (material events)
4. Summarise: Top 3 macro themes in 3 bullet points
5. Flag: Any earnings today that affect watchlist tickers
```

**Output block:**
```
🌍 *MACRO BRIEFING — {DATE}*
━━━━━━━━━━━━━━━━━━━━
📌 Theme 1: [summary]
📌 Theme 2: [summary]  
📌 Theme 3: [summary]
⚠️ Earnings Today: [tickers or NONE]
━━━━━━━━━━━━━━━━━━━━
```

---

### PHASE 2 — Top 3 Trade Setups

For each of the top 3 setups, execute:

```
1. Identify ticker from watchlist or screener
2. Run: python .agent/skills/quantum-alpha/scripts/risk_engine.py --ticker {TICKER}
3. Browser → verify 5 evidence points per SKILL.md protocol
4. Calculate Confidence Score (min 4.0/5 to include in report)
5. Format output per WhatsApp rules in SKILL.md
6. REJECT any setup below 4.0/5 confidence — replace with next candidate
```

**Output block (repeat × 3):**
```
━━━━━━━━━━━━━━━━━━━━
📊 SETUP #{N}: *{TICKER}*
🎯 Entry: ${PRICE}
🛑 Stop:  ${STOP} ({X}% risk)
🚀 Target: ${TARGET} ({X}R)
🔒 Confidence: {X}/5 ⭐

📋 Evidence:
1️⃣ [Technical — verified]
2️⃣ [Fundamental — SEC filing date]
3️⃣ [Macro — source]
4️⃣ [Flow — OpenInsider]
5️⃣ [Catalyst — Perplexity]

⚠️ Key Risk: [one line]
━━━━━━━━━━━━━━━━━━━━
```

---

### PHASE 3 — Watchlist Update

```
1. List tickers approaching key levels (no full signal yet)
2. State what catalyst would trigger a full signal
3. Max 5 watchlist items
```

**Output block:**
```
👁 *WATCHLIST*
━━━━━━━━━━━━━━━━━━━━
• {TICKER} — watching ${LEVEL}, trigger: [event]
• {TICKER} — watching ${LEVEL}, trigger: [event]
• {TICKER} — watching ${LEVEL}, trigger: [event]
━━━━━━━━━━━━━━━━━━━━
```

---

### PHASE 4 — Previous Day Recap (if applicable)

```
1. Review any open positions from yesterday's report
2. State current P&L vs target
3. Flag: hold / close / adjust stop
```

**Output block:**
```
📈 *OPEN POSITIONS RECAP*
━━━━━━━━━━━━━━━━━━━━
• {TICKER}: Entry ${X} → Now ${Y} | +{Z}% | {HOLD/CLOSE}
━━━━━━━━━━━━━━━━━━━━
```

---

### PHASE 5 — Risk Disclaimer

```
Always append the following disclaimer to every Daily Alpha Report:
```

```
⚠️ *DISCLAIMER*
This report is for educational purposes only. 
Not financial advice. All trades carry risk of loss. 
Verify all data independently before acting.
Position sizes are illustrative only.
Never risk more than you can afford to lose.
```

---

## ⏱ SCHEDULE (Optional Automation)

| Report | Trigger Time | Content |
|--------|-------------|---------|
| Pre-Market Brief | 06:30 UTC | Macro only (Phase 1) |
| Full Daily Report | 09:35 UTC | All 5 phases |
| End-of-Day Recap | 20:45 UTC | Phase 4 only |

To run a specific phase only:
```
/daily-alpha --phase 1     # Macro briefing only
/daily-alpha --phase 2     # Setups only
/daily-alpha --phase 4     # Recap only
```

---

## 🔧 CONFIGURATION OVERRIDES

Customise per session by appending flags to the trigger:

```
/daily-alpha --watchlist AAPL,NVDA,BTC-USD,ETH-USD
/daily-alpha --portfolio 50000 --risk 1.5
/daily-alpha --min-confidence 4.5
/daily-alpha --atr-period 21
```

---

## 📁 FILE REFERENCES

| File | Purpose |
|------|---------|
| `SKILL.md` | Full mandate, formatting rules, evidence requirements |
| `agent_config.md` | Browser routing, verification protocol, Confidence Score |
| `scripts/risk_engine.py` | ATR-based SL/TP calculator |
| `customizations/workflow.md` | This file — one-click trigger |

---

*Last updated: 2026-04-22 | Quantum Alpha Strategist v1.0.0*
