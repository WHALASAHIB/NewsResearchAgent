# 🤖 Quantum Alpha Strategist — Agent Configuration
**File:** `.agent/skills/quantum-alpha/agent_config.md`  
**Purpose:** Browser tool routing, verification protocol, and Confidence Score pipeline

---

## Agent Identity

```yaml
name: Quantum Alpha Strategist
version: 1.0.0
mandate: Never Lose Money
skill_path: .agent/skills/quantum-alpha/
risk_engine: scripts/risk_engine.py
```

---

## 🌐 Browser Tool — Verification Protocol

The agent **must** use the built-in Browser tool to verify at least **2 of the 5 evidence points** before issuing a Confidence Score. Unverified claims are capped at 0.5⭐ each.

### Verification Sources & URLs

| Evidence Type | Primary Source | URL Pattern | Required Fields |
|---------------|---------------|-------------|-----------------|
| **News/Catalyst** | Perplexity AI | `https://www.perplexity.ai/search?q={ticker}+{catalyst}` | Date, headline, source |
| **SEC Filings** | SEC EDGAR | `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K` | Filing date, key figure |
| **Insider Trades** | OpenInsider | `http://openinsider.com/search?q={ticker}` | Trade date, insider role, $ amount |
| **Options Flow** | FINRA | `https://www.finra.org/investors/have-problem/filing-complaint` | Vol, OI, call/put ratio |
| **Earnings** | SEC EDGAR | `https://efts.sec.gov/LATEST/search-index?q={ticker}&dateRange=custom&startdt={date}` | EPS, revenue, guidance |

### Browser Call Sequence (per signal)

```
Step 1 → Browser.navigate(perplexity_url)
         Extract: headline, date, publication
         Tag: Evidence Point 5 (News/Catalyst)

Step 2 → Browser.navigate(sec_edgar_url)
         Extract: last 10-K/10-Q filing date, EPS, revenue YoY
         Tag: Evidence Point 2 (Fundamental)

Step 3 → Browser.navigate(openinsider_url)   [if applicable]
         Extract: insider buys/sells last 90d
         Tag: Evidence Point 4 (Sentiment/Flow)

Step 4 → Compile all verified data → run risk_engine.py
Step 5 → Calculate Confidence Score → generate WhatsApp output
```

---

## 🔒 Confidence Score Calculator

The Confidence Score is computed **after** browser verification completes.

### Scoring Formula

```
Confidence Score = Σ (point_score for each of 5 evidence points)

Where point_score:
  +1.0  → Verified via Browser (live source, dated within 30 days)
  +0.5  → Inferred or sourced from memory/training data
  -1.0  → Contradicted by verified browser data
```

### Score → Signal Status Mapping

| Score | Status | WhatsApp Label | Position Size |
|-------|--------|---------------|---------------|
| 4.5–5.0 | HIGH CONVICTION | 🟢 `[HC]` | 100% of calc size |
| 3.5–4.4 | MODERATE | 🟡 `[MOD]` | 50% of calc size |
| 2.5–3.4 | SPECULATIVE | 🟠 `[SPEC]` | 25% — watchlist |
| < 2.5   | REJECT | 🔴 `[REJ]` | 0% — do not trade |

### Confidence Score Block (WhatsApp)

```
🔒 *Confidence: [X]/5 ⭐*
   1️⃣ Technical:   [✅/⚠️] [source]
   2️⃣ Fundamental: [✅/⚠️] [SEC filing date]
   3️⃣ Macro:       [✅/⚠️] [source]
   4️⃣ Flow:        [✅/⚠️] [OpenInsider/FINRA]
   5️⃣ Catalyst:    [✅/⚠️] [Perplexity verified]
```

---

## ⚙️ Agent Behaviour Rules

1. **Never skip browser verification.** If the browser tool is unavailable, downgrade all Perplexity/SEC evidence points to 0.5⭐ and flag output with `⚠️ UNVERIFIED`.
2. **Always run `risk_engine.py` before output.** No SL/TP levels = no signal.
3. **Never hallucinate prices.** If live price cannot be fetched, state "Price unverified — using last known: $X".
4. **Reject conflicts.** If browser data contradicts stated thesis, re-score and potentially REJECT signal.
5. **Cite every source.** Every evidence point must have a URL or filing reference in the "Sources" block.

---

## 🔗 Source Block Template (end of every signal)

```
🔗 *Sources:*
• SEC: [filing URL]
• Perplexity: [search URL]
• Chart: TradingView — {TICKER}
• Flow: openinsider.com/{ticker}
• Macro: [Bloomberg/Fed URL]
```
