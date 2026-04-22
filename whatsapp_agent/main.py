"""
╔══════════════════════════════════════════════════════════════════╗
║      QUANTUM ALPHA — WhatsApp Bot (Green API)                  ║
║      Personal · Secured · Owner-only                           ║
╚══════════════════════════════════════════════════════════════════╝

Security layers applied on every incoming message:
  1. Owner whitelist    — only OWNER_PHONE_NUMBER can interact
  2. Rate limiter       — max RATE_LIMIT_PER_HOUR requests/hour
  3. Input sanitizer    — blocks injections, limits length
  4. Secure logger      — masks all API keys in logs
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

from security import (
    logger,
    validate_environment,
    is_authorized,
    handle_unauthorized,
    is_rate_limited,
    sanitize_message,
    sanitize_ticker,
    RATE_LIMIT_MESSAGE,
    SANITIZE_FAIL_MESSAGE,
)
from research_engine import ResearchEngine

load_dotenv()

INSTANCE_ID = os.getenv("GREEN_API_INSTANCE_ID", "")
API_TOKEN   = os.getenv("GREEN_API_TOKEN", "")
BASE_URL    = f"https://api.greenapi.com/waInstance{INSTANCE_ID}"

engine    = ResearchEngine()
processed = set()          # Already-handled receipt IDs


# ═══════════════════════════════════════════════════════════════════════════
# GREEN API HELPERS
# ═══════════════════════════════════════════════════════════════════════════

async def send_message(chat_id: str, text: str):
    """Send a WhatsApp message. Splits long replies into chunks."""
    chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
    async with httpx.AsyncClient(timeout=15) as client:
        for chunk in chunks:
            try:
                await client.post(
                    f"{BASE_URL}/sendMessage/{API_TOKEN}",
                    json={"chatId": chat_id, "message": chunk},
                )
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"send_message error: {e}")


async def receive_notification() -> dict | None:
    """Poll Green API for the next queued notification."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE_URL}/receiveNotification/{API_TOKEN}")
        if resp.status_code == 200 and resp.text.strip() not in ["null", ""]:
            return resp.json()
    return None


async def delete_notification(receipt_id: int):
    """Acknowledge a processed notification so it leaves the queue."""
    async with httpx.AsyncClient(timeout=10) as client:
        await client.delete(
            f"{BASE_URL}/deleteNotification/{API_TOKEN}/{receipt_id}"
        )


def extract_message(notification: dict) -> tuple[str, str] | tuple[None, None]:
    """Extract (chat_id, message_text) from a Green API notification body."""
    body  = notification.get("body", {})
    type_ = body.get("typeWebhook", "")

    if type_ != "incomingMessageReceived":
        return None, None

    msg_data = body.get("messageData", {})
    if msg_data.get("typeMessage") != "textMessage":
        return None, None

    chat_id = body.get("senderData", {}).get("chatId", "")
    text    = msg_data.get("textMessageData", {}).get("textMessage", "").strip()
    return chat_id, text


# ═══════════════════════════════════════════════════════════════════════════
# SECURE MESSAGE ROUTER
# ═══════════════════════════════════════════════════════════════════════════

async def handle_message(chat_id: str, raw_text: str):
    """
    Process a single incoming WhatsApp message through all security gates
    before routing to the research engine.
    """

    # ── Gate 1: Owner whitelist ────────────────────────────────────────────
    if not is_authorized(chat_id):
        handle_unauthorized(chat_id, raw_text)
        # Silent drop — don't acknowledge the bot exists to strangers
        return

    # ── Gate 2: Rate limiter ───────────────────────────────────────────────
    if is_rate_limited(chat_id):
        await send_message(chat_id, RATE_LIMIT_MESSAGE)
        return

    # ── Gate 3: Input sanitizer ────────────────────────────────────────────
    is_safe, text = sanitize_message(raw_text)
    if not is_safe:
        await send_message(chat_id, SANITIZE_FAIL_MESSAGE)
        return

    logger.info(f"MSG | len={len(text)} | preview='{text[:60]}'")

    # ── Typing indicator ───────────────────────────────────────────────────
    await send_message(chat_id, "🔍 *Researching...* give me 20–30 seconds.")

    # ── Route to research functions ────────────────────────────────────────
    try:
        msg = text.lower().strip()

        if msg in ["hi", "hello", "help", "/help", "start", "/start"]:
            reply = engine.get_help_message()

        elif msg.startswith("/daily") or "daily report" in msg:
            reply = await engine.daily_alpha_report()

        elif msg.startswith("/analyse ") or msg.startswith("/analyze "):
            raw_ticker = text.split(" ", 1)[1].strip()
            valid, ticker = sanitize_ticker(raw_ticker)
            if not valid:
                reply = f"⚠️ Invalid ticker `{raw_ticker[:10]}`. Example: /analyse AAPL"
            else:
                reply = await engine.analyse_ticker(ticker)

        elif msg.startswith("/risk "):
            raw_ticker = text.split(" ", 1)[1].strip()
            valid, ticker = sanitize_ticker(raw_ticker)
            if not valid:
                reply = f"⚠️ Invalid ticker. Example: /risk NVDA"
            else:
                reply = await engine.risk_check(ticker)

        elif msg.startswith("/news "):
            topic = text.split(" ", 1)[1].strip()
            reply = await engine.get_news(topic)

        elif msg.startswith("/macro"):
            reply = await engine.macro_briefing()

        else:
            reply = await engine.free_research(text)

    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        reply = (
            "⚠️ *Something went wrong on my end.*\n"
            "I've logged the error. Try again or type /help."
        )

    await send_message(chat_id, reply)
    logger.info(f"REPLIED | len={len(reply)}")


# ═══════════════════════════════════════════════════════════════════════════
# POLLING LOOP
# ═══════════════════════════════════════════════════════════════════════════

async def poll_loop():
    """Poll Green API every 2 seconds for new messages."""
    logger.info("=" * 55)
    logger.info("  Quantum Alpha WhatsApp Agent — ONLINE")
    logger.info(f"  Instance : {INSTANCE_ID}")
    logger.info(f"  Security : whitelist={len(os.getenv('OWNER_PHONE_NUMBER','').split(','))} number(s)")
    logger.info("  Polling  : every 2 seconds")
    logger.info("=" * 55)

    while True:
        try:
            notif = await receive_notification()

            if notif:
                receipt_id = notif.get("receiptId")
                chat_id, text = extract_message(notif)

                # Always delete first to prevent re-delivery
                if receipt_id:
                    await delete_notification(receipt_id)

                if chat_id and text and receipt_id not in processed:
                    processed.add(receipt_id)
                    # Trim processed set to avoid unbounded memory growth
                    if len(processed) > 10_000:
                        oldest = list(processed)[:5_000]
                        for r in oldest:
                            processed.discard(r)

                    asyncio.create_task(handle_message(chat_id, text))

        except httpx.TimeoutException:
            logger.debug("Poll timeout — retrying")
        except Exception as e:
            logger.error(f"Poll loop error: {e}")

        await asyncio.sleep(2)


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if validate_environment():
        asyncio.run(poll_loop())
    else:
        logger.error("Startup aborted — fix missing environment variables in .env")
