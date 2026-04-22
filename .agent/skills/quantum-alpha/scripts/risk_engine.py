"""
QUANTUM ALPHA STRATEGIST — RISK ENGINE v1.0
ATR-Based Stop-Loss & Take-Profit Calculator
Mandate: Never Lose Money | Capital Preservation First

Usage:
    python risk_engine.py --demo                   # demo with sample data
    python risk_engine.py --ticker AAPL            # live data via yfinance
    python risk_engine.py --ticker BTC-USD --sl 2.0 --tp 4.0

Dependencies:
    pip install yfinance pandas numpy rich
"""

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ── Optional rich output ───────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None

# ── Optional live data ─────────────────────────────────────────────────────
try:
    import yfinance as yf
    DATA_AVAILABLE = True
except ImportError:
    DATA_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MarketData:
    """Raw OHLCV container."""
    ticker: str
    current_price: float
    highs: list
    lows: list
    closes: list
    period: int = 14
    source: str = "manual"


@dataclass
class RiskParameters:
    """Risk configuration."""
    atr_multiplier_sl: float = 1.5   # Stop-loss ATR multiplier
    atr_multiplier_tp: float = 3.0   # Take-profit ATR multiplier
    min_rr_ratio: float = 2.0        # Minimum R:R to accept a trade
    max_risk_pct: float = 2.0        # Max % of portfolio risked per trade
    portfolio_size: float = 100_000.0


@dataclass
class TradeSetup:
    """Computed trade levels and risk metrics."""
    ticker: str
    entry_price: float
    atr: float
    stop_loss: float
    take_profit: float
    risk_per_share: float
    reward_per_share: float
    rr_ratio: float
    position_size_shares: int
    position_size_usd: float
    max_loss_usd: float
    max_gain_usd: float
    signal_valid: bool
    rejection_reason: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    )

    def to_whatsapp(self) -> str:
        """WhatsApp-optimised output (see SKILL.md formatting rules)."""
        risk_pct = (self.risk_per_share / self.entry_price) * 100
        status = "🟢 VALID SETUP" if self.signal_valid else f"🔴 REJECTED — {self.rejection_reason}"
        return (
            f"📊 *{self.ticker} — Risk Engine*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 Entry:  ${self.entry_price:.2f}\n"
            f"🛑 Stop:   ${self.stop_loss:.2f}  ({risk_pct:.1f}% risk)\n"
            f"🚀 Target: ${self.take_profit:.2f}  ({self.rr_ratio:.1f}R)\n"
            f"📐 ATR(14): ${self.atr:.2f}\n\n"
            f"💼 *Position:*\n"
            f"   Shares: {self.position_size_shares:,}\n"
            f"   Value:  ${self.position_size_usd:,.0f}\n"
            f"   Max Loss: ${self.max_loss_usd:,.0f}\n"
            f"   Max Gain: ${self.max_gain_usd:,.0f}\n\n"
            f"🔒 Status: {status}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ {self.timestamp}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# ATR CALCULATION (Wilder's Smoothing)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_true_range(high: float, low: float, prev_close: float) -> float:
    """True Range = max(H-L, |H-Cprev|, |L-Cprev|)."""
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def calculate_atr(highs: list, lows: list, closes: list, period: int = 14) -> float:
    """
    Wilder's Average True Range.
    Requires period + 1 data points minimum.
    """
    if len(closes) < period + 1:
        raise ValueError(
            f"Need at least {period + 1} data points for ATR({period}). Got {len(closes)}."
        )
    trs = [
        calculate_true_range(highs[i], lows[i], closes[i - 1])
        for i in range(1, len(closes))
    ]
    # Seed with simple average
    atr = sum(trs[:period]) / period
    # Wilder smoothing
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return round(atr, 4)


# ═══════════════════════════════════════════════════════════════════════════
# RISK ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class QuantumRiskEngine:
    """
    Core risk engine for the Quantum Alpha Strategist.
    Enforces the Never Lose Money mandate via ATR-gated SL/TP and R:R checks.
    """

    def __init__(self, params: Optional[RiskParameters] = None):
        self.params = params or RiskParameters()

    def calculate(self, data: MarketData) -> TradeSetup:
        """Run the full risk calculation pipeline."""
        atr = calculate_atr(data.highs, data.lows, data.closes, data.period)

        entry = data.current_price
        stop_loss   = round(entry - (atr * self.params.atr_multiplier_sl), 4)
        take_profit = round(entry + (atr * self.params.atr_multiplier_tp), 4)

        risk   = round(entry - stop_loss, 4)
        reward = round(take_profit - entry, 4)

        if risk <= 0:
            return self._reject(data.ticker, entry, atr, stop_loss, take_profit,
                                risk, reward, "Stop-loss above entry price")

        rr = round(reward / risk, 2)

        # Never Lose Money gate — minimum R:R
        if rr < self.params.min_rr_ratio:
            return self._reject(data.ticker, entry, atr, stop_loss, take_profit,
                                risk, reward,
                                f"R:R {rr:.1f} below minimum {self.params.min_rr_ratio:.1f}")

        # Position sizing (fixed-fractional)
        max_risk_usd   = self.params.portfolio_size * (self.params.max_risk_pct / 100)
        shares         = max(1, int(max_risk_usd / risk))
        position_usd   = round(shares * entry, 2)
        max_loss       = round(shares * risk, 2)
        max_gain       = round(shares * reward, 2)

        return TradeSetup(
            ticker=data.ticker,
            entry_price=entry, atr=atr,
            stop_loss=stop_loss, take_profit=take_profit,
            risk_per_share=risk, reward_per_share=reward, rr_ratio=rr,
            position_size_shares=shares, position_size_usd=position_usd,
            max_loss_usd=max_loss, max_gain_usd=max_gain,
            signal_valid=True,
        )

    def _reject(self, ticker, entry, atr, sl, tp, risk, reward, reason) -> TradeSetup:
        rr = round(reward / risk, 2) if risk > 0 else 0.0
        return TradeSetup(
            ticker=ticker, entry_price=entry, atr=atr,
            stop_loss=sl, take_profit=tp,
            risk_per_share=risk, reward_per_share=reward, rr_ratio=rr,
            position_size_shares=0, position_size_usd=0.0,
            max_loss_usd=0.0, max_gain_usd=0.0,
            signal_valid=False, rejection_reason=reason,
        )


# ═══════════════════════════════════════════════════════════════════════════
# LIVE DATA FETCHER
# ═══════════════════════════════════════════════════════════════════════════

def fetch_market_data(ticker: str, period_days: int = 14) -> MarketData:
    """Fetch OHLCV from Yahoo Finance via yfinance."""
    if not DATA_AVAILABLE:
        raise ImportError("Run: pip install yfinance")
    df = yf.download(ticker, period=f"{period_days + 10}d", progress=False)
    if df.empty:
        raise ValueError(f"No data for '{ticker}'")
    return MarketData(
        ticker=ticker.upper(),
        current_price=round(float(df["Close"].iloc[-1]), 4),
        highs=df["High"].tolist(),
        lows=df["Low"].tolist(),
        closes=df["Close"].tolist(),
        period=period_days,
        source="Yahoo Finance (live)",
    )


# ═══════════════════════════════════════════════════════════════════════════
# DEMO DATA
# ═══════════════════════════════════════════════════════════════════════════

DEMO_DATA = {
    "AAPL": MarketData(
        ticker="AAPL", current_price=189.50,
        highs=[185,187,190,192,191,193,195,194,196,198,197,199,200,191,193],
        lows= [180,182,185,187,186,188,190,189,191,193,192,194,195,186,188],
        closes=[183,185,188,190,189,191,193,192,194,196,195,197,198,189,189.50],
    ),
    "BTC-USD": MarketData(
        ticker="BTC-USD", current_price=67_250.0,
        highs=[64000,65200,66100,67000,66800,68000,69000,68500,70000,71000,70500,72000,73000,68000,69000],
        lows= [62000,63000,64500,65000,65200,66000,67000,66800,68000,69000,68500,70000,71000,66000,67000],
        closes=[63500,64500,65500,66000,66200,67000,68000,67500,69000,70000,69500,71000,72000,67000,67250],
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════════════════════════

def print_result(setup: TradeSetup, data: MarketData) -> None:
    if RICH:
        tbl = Table(title=f"⚡ Quantum Risk Engine — {setup.ticker}", show_lines=True)
        tbl.add_column("Metric", style="cyan", min_width=22)
        tbl.add_column("Value",  style="bold white", min_width=20)
        tbl.add_row("Entry Price",     f"${setup.entry_price:,.4f}")
        tbl.add_row(f"ATR({data.period})", f"${setup.atr:,.4f}")
        tbl.add_row("🛑 Stop-Loss",    f"[red]${setup.stop_loss:,.4f}[/red]")
        tbl.add_row("🚀 Take-Profit",  f"[green]${setup.take_profit:,.4f}[/green]")
        tbl.add_row("R:R Ratio",       f"{setup.rr_ratio:.2f}:1")
        tbl.add_row("Position Shares", f"{setup.position_size_shares:,}")
        tbl.add_row("Position Value",  f"${setup.position_size_usd:,.2f}")
        tbl.add_row("Max Loss",        f"[red]${setup.max_loss_usd:,.2f}[/red]")
        tbl.add_row("Max Gain",        f"[green]${setup.max_gain_usd:,.2f}[/green]")
        status = "✅ VALID" if setup.signal_valid else f"❌ REJECTED: {setup.rejection_reason}"
        tbl.add_row("Signal Status",   status)
        console.print(tbl)
        console.print(Panel(setup.to_whatsapp(), title="📱 WhatsApp Output", border_style="blue"))
    else:
        print("\n" + "═" * 50)
        print(f"  {setup.ticker} — Quantum Risk Engine")
        print("═" * 50)
        print(f"  Entry:       ${setup.entry_price:,.4f}")
        print(f"  ATR({data.period}):     ${setup.atr:,.4f}")
        print(f"  Stop-Loss:   ${setup.stop_loss:,.4f}")
        print(f"  Take-Profit: ${setup.take_profit:,.4f}")
        print(f"  R:R:         {setup.rr_ratio:.2f}:1")
        print(f"  Shares:      {setup.position_size_shares:,}")
        print(f"  Max Loss:    ${setup.max_loss_usd:,.2f}")
        print(f"  Max Gain:    ${setup.max_gain_usd:,.2f}")
        valid = "YES" if setup.signal_valid else f"NO — {setup.rejection_reason}"
        print(f"  Valid:       {valid}")
        print("═" * 50)
        print("\n📱 WhatsApp Output:\n" + "-" * 40)
        print(setup.to_whatsapp())


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Quantum Alpha — ATR Risk Engine")
    parser.add_argument("--ticker",    type=str)
    parser.add_argument("--demo",      action="store_true")
    parser.add_argument("--sl",        type=float, default=1.5)
    parser.add_argument("--tp",        type=float, default=3.0)
    parser.add_argument("--min-rr",    type=float, default=2.0)
    parser.add_argument("--portfolio", type=float, default=100_000)
    parser.add_argument("--risk",      type=float, default=2.0)
    parser.add_argument("--period",    type=int,   default=14)
    args = parser.parse_args()

    params = RiskParameters(
        atr_multiplier_sl=args.sl,
        atr_multiplier_tp=args.tp,
        min_rr_ratio=args.min_rr,
        max_risk_pct=args.risk,
        portfolio_size=args.portfolio,
    )
    engine = QuantumRiskEngine(params)

    if args.demo:
        for ticker, data in DEMO_DATA.items():
            data.period = args.period
            print_result(engine.calculate(data), data)
            print()
    elif args.ticker:
        try:
            data = fetch_market_data(args.ticker, args.period)
            print_result(engine.calculate(data), data)
        except Exception as e:
            print(f"❌ {e}"); sys.exit(1)
    else:
        ticker = input("Ticker (or 'demo'): ").strip().upper()
        if ticker == "DEMO":
            for t, data in DEMO_DATA.items():
                print_result(engine.calculate(data), data)
        else:
            try:
                data = fetch_market_data(ticker, args.period)
                print_result(engine.calculate(data), data)
            except Exception as e:
                print(f"❌ {e}"); sys.exit(1)


if __name__ == "__main__":
    main()
