"""
╔══════════════════════════════════════════════════════════════════╗
║      QUANTUM ALPHA — WhatsApp Bot (Green API)                  ║
║      No Twilio. No ngrok. Just scan a QR code.                 ║
╚══════════════════════════════════════════════════════════════════╝

This uses Green API — connects via YOUR existing WhatsApp number.
You scan a QR code once → bot runs on your own number.

Setup: See SETUP.md
Run:   python main.py
"""

import os
import asyncio
import httpx
import json
import time
from dotenv import load_dotenv
from research_engine import ResearchEngine

load_dotenv()

INSTANCE_ID = os.getenv("GREEN_API_INSTANCE_ID", "")
API_TOKEN   = os.getenv("GREEN_API_TOKEN", "")
BASE_URL    = f"https://api.greenapi.com/waInstance{INSTANCE_ID}"

engine = ResearchEngine()

# Tracks messages already processed (prevents duplicates)
processed = set()


# ═══════════════════════════════════════════════════════════════════════════
# GREEN API HELPERS
# ═══════════════════════════════════════════════════════════════════════════

async def send_message(chat_id: str, text: str):
    """Send a WhatsApp message via Green API."""
    # Split into chunks if > 1500 chars (keeps WhatsApp readable)
    chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
    async with httpx.AsyncClient(timeout=15) as client:
        for chunk in chunks:
            await client.post(
                f"{BASE_URL}/sendMessage/{API_TOKEN}",
                json={"chatId": chat_id, "message": chunk},
            )
            await asyncio.sleep(0.5)  # slight delay between chunks


async def receive_notification() -> dict | None:
    """Poll Green API for the next incoming message."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE_URL}/receiveNotification/{API_TOKEN}")
        if resp.status_code == 200 and resp.text.strip() not in ["null", ""]:
            return resp.json()
    return None


async def delete_notification(receipt_id: int):
    """Acknowledge / delete a processed notification."""
    async with httpx.AsyncClient(timeout=10) as client:
        await client.delete(
            f"{BASE_URL}/deleteNotification/{API_TOKEN}/{receipt_id}"
        )


def extract_message(notification: dict) -> tuple[str, str] | tuple[None, None]:
    """
    Extract (chat_id, message_text) from a Green API notification.
    Returns (None, None) if not a text message.
    """
    body = notification.get("body", {})
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
# MESSAGE ROUTER
# ═══════════════════════════════════════════════════════════════════════════

async def handle_message(chat_id: str, text: str):
    """Route incoming WhatsApp message to the right research function."""
    msg = text.lower().strip()
    print(f"📩 [{chat_id}]: {text}")

    # Typing indicator
    await send_message(chat_id, "🔍 *Researching...* give me 20–30 seconds.")

    try:
        if msg in ["hi", "hello", "help", "/help", "start", "/start"]:
            reply = engine.get_help_message()

        elif msg.startswith("/daily") or "daily report" in msg:
            reply = await engine.daily_alpha_report()

        elif msg.startswith("/analyse ") or msg.startswith("/analyze "):
            ticker = text.split(" ", 1)[1].strip().upper()
            reply  = await engine.analyse_ticker(ticker)

        elif msg.startswith("/risk "):
            ticker = text.split(" ", 1)[1].strip().upper()
            reply  = await engine.risk_check(ticker)

        elif msg.startswith("/news "):
            topic = text.split(" ", 1)[1].strip()
            reply = await engine.get_news(topic)

        elif msg.startswith("/macro"):
            reply = await engine.macro_briefing()

        else:
            # Free-form: treat as a research question
            reply = await engine.free_research(text)

    except Exception as e:
        reply = (
            f"⚠️ *Error*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{str(e)[:200]}\n\n"
            f"Type /help to see commands."
        )

    await send_message(chat_id, reply)
    print(f"✅ Replied to [{chat_id}]")


# ═══════════════════════════════════════════════════════════════════════════
# POLLING LOOP
# ═══════════════════════════════════════════════════════════════════════════

async def poll_loop():
    """
    Continuously poll Green API for new messages.
    No ngrok. No webhook. Just polling every 2 seconds.
    """
    print("\n⚡ Quantum Alpha WhatsApp Agent — ONLINE")
    print(f"   Instance: {INSTANCE_ID}")
    print("   Polling for messages every 2 seconds...")
    print("   Send 'hi' on WhatsApp to start.\n")

    while True:
        try:
            notif = await receive_notification()

            if notif:
                receipt_id = notif.get("receiptId")
                chat_id, text = extract_message(notif)

                # Always delete the notification first (prevents re-processing)
                if receipt_id:
                    await delete_notification(receipt_id)

                # Process if it's a new text message
                if chat_id and text and receipt_id not in processed:
                    processed.add(receipt_id)
                    # Handle in background so polling continues immediately
                    asyncio.create_task(handle_message(chat_id, text))

        except Exception as e:
            print(f"⚠️ Poll error: {e}")

        await asyncio.sleep(2)  # Poll every 2 seconds


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def check_config():
    """Validate env vars before starting."""
    errors = []
    if not INSTANCE_ID or INSTANCE_ID == "your_instance_id_here":
        errors.append("❌ GREEN_API_INSTANCE_ID not set in .env")
    if not API_TOKEN or API_TOKEN == "your_instance_token_here":
        errors.append("❌ GREEN_API_TOKEN not set in .env")
    if not os.getenv("GEMINI_API_KEY"):
        errors.append("⚠️  GEMINI_API_KEY not set (AI analysis disabled)")
    if not os.getenv("NEWSDATA_API_KEY"):
        errors.append("⚠️  NEWSDATA_API_KEY not set (news disabled)")

    if errors:
        print("\n".join(errors))
        if any("❌" in e for e in errors):
            print("\n👉 See SETUP.md to configure Green API (takes 5 minutes)")
            return False
    return True


if __name__ == "__main__":
    if check_config():
        asyncio.run(poll_loop())
