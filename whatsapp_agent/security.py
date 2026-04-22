"""
╔══════════════════════════════════════════════════════════════════╗
║      QUANTUM ALPHA — Security Module                           ║
║      Whitelist · Rate Limiting · Input Sanitization · Logging  ║
╚══════════════════════════════════════════════════════════════════╝

This is a PERSONAL bot. Unauthorised access is blocked at every layer:
  1. Phone number whitelist  — only OWNER_PHONE_NUMBER can interact
  2. Rate limiter            — max N requests/hour even for owner
  3. Input sanitizer         — strip injections, limit length
  4. Secure logger           — masks all API keys in logs
  5. Intrusion logger        — records every blocked attempt
"""

import os
import re
import time
import hashlib
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# SECURE LOGGING — masks any value that looks like an API key
# ═══════════════════════════════════════════════════════════════════════════

class MaskingFormatter(logging.Formatter):
    """Redacts API keys and tokens from all log output."""

    # Patterns that look like secrets
    PATTERNS = [
        (re.compile(r'(AIza[A-Za-z0-9_\-]{35})'), '[GEMINI_KEY_REDACTED]'),
        (re.compile(r'(pub_[a-f0-9]{32})'),        '[NEWSDATA_KEY_REDACTED]'),
        (re.compile(r'([a-f0-9]{50})'),             '[TOKEN_REDACTED]'),
        (re.compile(r'(sk-[A-Za-z0-9]{48})'),      '[OPENAI_KEY_REDACTED]'),
        (re.compile(r'(pplx-[A-Za-z0-9]{48})'),    '[PERPLEXITY_KEY_REDACTED]'),
    ]

    def format(self, record):
        msg = super().format(record)
        for pattern, replacement in self.PATTERNS:
            msg = pattern.sub(replacement, msg)
        return msg


def setup_logger() -> logging.Logger:
    """Configure the application logger with masking and file output."""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("quantum_alpha")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger  # Already configured

    fmt = MaskingFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S UTC",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler — rotates daily
    log_file = log_dir / f"agent_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


logger = setup_logger()


# ═══════════════════════════════════════════════════════════════════════════
# WHITELIST — only the owner's number may use the bot
# ═══════════════════════════════════════════════════════════════════════════

def _load_authorized_numbers() -> set[str]:
    """
    Build the set of authorized chat IDs from environment.
    Green API chat IDs look like: '85254861285@c.us'
    """
    raw = os.getenv("OWNER_PHONE_NUMBER", "")
    authorized = set()
    for num in raw.split(","):
        num = num.strip().lstrip("+")
        if num:
            authorized.add(f"{num}@c.us")
    return authorized


AUTHORIZED_CHAT_IDS: set[str] = _load_authorized_numbers()
LOG_UNAUTHORIZED: bool = os.getenv("LOG_UNAUTHORIZED", "true").lower() == "true"


def is_authorized(chat_id: str) -> bool:
    """Return True only if chat_id belongs to the owner."""
    return chat_id in AUTHORIZED_CHAT_IDS


def handle_unauthorized(chat_id: str, message: str) -> str:
    """Log the intrusion attempt and return a non-informative rejection."""
    if LOG_UNAUTHORIZED:
        # Hash the chat_id so real number is not stored in plain text
        hashed = hashlib.sha256(chat_id.encode()).hexdigest()[:12]
        logger.warning(
            f"UNAUTHORIZED ACCESS BLOCKED | caller_hash={hashed} | "
            f"msg_len={len(message)} | ts={datetime.now(timezone.utc).isoformat()}"
        )
    # Return a generic message — don't reveal that a bot exists
    return None   # Caller should send nothing (silent drop)


# ═══════════════════════════════════════════════════════════════════════════
# RATE LIMITER — sliding window, per chat_id
# ═══════════════════════════════════════════════════════════════════════════

RATE_LIMIT: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "20"))
_request_log: dict[str, list[float]] = defaultdict(list)


def is_rate_limited(chat_id: str) -> bool:
    """
    Return True if chat_id has exceeded RATE_LIMIT requests in the last hour.
    Uses a sliding 3600-second window.
    """
    now = time.monotonic()
    window = now - 3600.0

    # Remove timestamps older than 1 hour
    _request_log[chat_id] = [t for t in _request_log[chat_id] if t > window]

    if len(_request_log[chat_id]) >= RATE_LIMIT:
        logger.warning(f"RATE LIMIT HIT | chat={_hash(chat_id)} | count={len(_request_log[chat_id])}")
        return True

    _request_log[chat_id].append(now)
    return False


def _hash(chat_id: str) -> str:
    return hashlib.sha256(chat_id.encode()).hexdigest()[:10]


# ═══════════════════════════════════════════════════════════════════════════
# INPUT SANITIZER — prevent injection / abuse
# ═══════════════════════════════════════════════════════════════════════════

MAX_MESSAGE_LENGTH = 500   # Characters
MAX_TICKER_LENGTH  = 10    # Ticker symbols

# Characters allowed in ticker symbols
TICKER_PATTERN = re.compile(r'^[A-Z0-9\-\.]{1,10}$')


def sanitize_message(text: str) -> tuple[bool, str]:
    """
    Validate and clean an incoming message.

    Returns:
        (is_safe: bool, cleaned_text: str)
    """
    if not text or not isinstance(text, str):
        return False, ""

    # Strip leading/trailing whitespace
    text = text.strip()

    # Enforce maximum length
    if len(text) > MAX_MESSAGE_LENGTH:
        logger.info(f"Message truncated from {len(text)} to {MAX_MESSAGE_LENGTH} chars")
        text = text[:MAX_MESSAGE_LENGTH]

    # Remove null bytes and control characters (except newline/tab)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

    # Block prompt injection patterns targeting the AI
    injection_patterns = [
        r'ignore (previous|all|above) instructions',
        r'you are now',
        r'disregard your',
        r'system prompt',
        r'act as (a |an )?(different|new|unrestricted)',
        r'jailbreak',
        r'DAN mode',
    ]
    for pattern in injection_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"INJECTION ATTEMPT BLOCKED | pattern='{pattern[:30]}'")
            return False, ""

    return True, text


def sanitize_ticker(ticker: str) -> tuple[bool, str]:
    """
    Validate a ticker symbol.

    Returns:
        (is_valid: bool, clean_ticker: str)
    """
    ticker = ticker.strip().upper()[:MAX_TICKER_LENGTH]
    if TICKER_PATTERN.match(ticker):
        return True, ticker
    logger.warning(f"Invalid ticker rejected: '{ticker[:20]}'")
    return False, ""


# ═══════════════════════════════════════════════════════════════════════════
# ENV VALIDATOR — check all required secrets are present at startup
# ═══════════════════════════════════════════════════════════════════════════

def validate_environment() -> bool:
    """
    Check required environment variables at startup.
    Returns False and prints errors if critical vars are missing.
    """
    required = {
        "GREEN_API_INSTANCE_ID": "Green API instance ID",
        "GREEN_API_TOKEN":       "Green API token",
        "OWNER_PHONE_NUMBER":    "Your WhatsApp number (owner whitelist)",
    }
    recommended = {
        "GEMINI_API_KEY":    "Gemini AI (needed for analysis)",
        "NEWSDATA_API_KEY":  "NewsData.io (needed for news)",
    }

    ok = True
    for key, desc in required.items():
        val = os.getenv(key, "")
        if not val or "your_" in val:
            logger.error(f"MISSING REQUIRED: {key} — {desc}")
            ok = False

    for key, desc in recommended.items():
        val = os.getenv(key, "")
        if not val:
            logger.warning(f"MISSING RECOMMENDED: {key} — {desc}")

    if ok:
        logger.info("✅ Environment validated — all required secrets present")
    return ok


# ═══════════════════════════════════════════════════════════════════════════
# RATE LIMIT REPLY
# ═══════════════════════════════════════════════════════════════════════════

RATE_LIMIT_MESSAGE = (
    f"⏳ *Slow down!*\n"
    f"You've hit the request limit ({RATE_LIMIT}/hour).\n"
    f"Wait a few minutes and try again."
)

SANITIZE_FAIL_MESSAGE = (
    "⚠️ *Invalid input detected.*\n"
    "Please send a normal market question or command.\n"
    "Type /help for available commands."
)
