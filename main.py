import html
import logging
import os
import httpx
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8496632773:AAF50q8E40t2JGin-YtWtcWs5KS1QMqNxas")
API_KEY = os.getenv("API_KEY", "WMVL9")
API_BASE_URL = "https://admin.gbssystems.com/public/api/v1/api.php"

# Updated TG to Number API Configuration
TG_TO_NUM_API_URL = os.getenv("TG_TO_NUM_API_URL", "https://tg-2-num.vaault.in/tg-2-num")
TG_TO_NUM_API_KEY = os.getenv("TG_TO_NUM_API_KEY", "Gautamxlive1")

DEV_TAG = "👨‍💻 <b>Developer:</b> @RD3B4T"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def c(val) -> str:
    """Safe HTML escaping with fallback."""
    if val is None or str(val).strip() in ("", "None", "NA", "null", "false"):
        return "N/A"
    return html.escape(str(val).strip())


def split_message(text: str, max_length: int = 4000) -> list[str]:
    """Split message safely to stay within Telegram character limits."""
    chunks = []
    while len(text) > max_length:
        split_at = text.rfind("\n\n", 0, max_length)
        if split_at <= 0:
            split_at = max_length
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks


# ==========================================
# EXACT FIELD PARSERS
# ==========================================

def format_number_response(data: dict, query: str) -> str:
    records = data.get("result") or data.get("RESULT") or []
    if not records and isinstance(data, dict):
        if any(k in data for k in ("name", "NAME", "aadhar", "AADHAAR", "mobile", "NUMBER")):
            records = [data]

    if not records:
        return f"⚠️ <code>{c(query)}</code> ke liye koi telecom record nahi mila.\n\n{DEV_TAG}"

    total_count = data.get("total_records") or data.get("COUNT") or len(records)
    lines = [
        f"📱 <b>MOBILE LOOKUP RECORDS ({total_count} Found)</b>",
        f"<b>Input:</b> <code>{c(query)}</code>",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    for idx, r in enumerate(records, 1):
        name = r.get("name") or r.get("NAME")
        first = r.get("first_name")
        middle = r.get("middle_name")
        last = r.get("last_name")
        fname = r.get("father_name") or r.get("FNAME")
        mobile = r.get("mobile") or r.get("NUMBER")
        alt = r.get("alternate_mobile") or r.get("ALT")
        aadhar_val = r.get("aadhar") or r.get("AADHAAR") 
        email = r.get("email") or r.get("EMAIL")
        circle = r.get("circle") or r.get("CIRCLE")
        address = r.get("address") or r.get("ADDRESS")

        lines.append(f"\n<b>[Connection #{idx}]</b>")
        lines.append(f"• <b>Full Name:</b> <b>{c(name)}</b>")

        # Name Breakdown
        name_parts = []
        if first:
            name_parts.append(f"First: {first}")
        if middle:
            name_parts.append(f"Mid: {middle}")
        if last:
            name_parts.append(f"Last: {last}")
        if name_parts:
            lines.append(f"• <b>Name Split:</b> <code>{c(' | '.join(name_parts))}</code>")

        if fname:
            lines.append(f"• <b>Father's Name:</b> {c(fname)}")
        if mobile:
            lines.append(f"• <b>Mobile:</b> <code>{c(mobile)}</code>")
        if alt:
            lines.append(f"• <b>Alt Mobile:</b> <code>{c(alt)}</code>")

        # Aadhaar presence status
        if aadhar_val and str(aadhar_val).strip().lower() not in ("none", "null", "na", ""):
            lines.append(f"• <b>Aadhaar:</b> <code>{c(aadhar_val)}</code>")
        else:
            lines.append("• <b>Aadhaar:</b> <code>Not Linked / Not Available</code>")

        if email:
            lines.append(f"• <b>Email:</b> {c(email)}")
        if circle:
            lines.append(f"• <b>Circle / Operator:</b> {c(circle)}")
        if address:
            lines.append(f"• <b>Address:</b> {c(address)}")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━")
    lines.append(DEV_TAG)
    return "\n".join(lines)


def format_tg_to_num_response(payload: dict, query_val: str) -> str:
    """Dedicated parser for the tg-2-num API response structure."""
    resp_obj = payload.get("response") or {}
    data_list = resp_obj.get("data") or []
    params = resp_obj.get("parameters") or {}
    provider = payload.get("developer", "N/A")

    if not data_list:
        return (
            f"⚠️ <b>Telegram ID:</b> <code>{c(query_val)}</code> ke liye koi linked phone number nahi mila.\n\n"
            f"{DEV_TAG}"
        )

    lines = [
        "✈️ <b>TG TO NUMBER REPORT</b>",
        f"<b>Target:</b> <code>{c(query_val)}</code>",
        f"<b>API Provider:</b> <code>{c(provider)}</code>",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    for idx, item in enumerate(data_list, 1):
        num = item.get("number")
        c_code = item.get("country_code", "")
        country = item.get("country")
        u_id = item.get("user_id")

        lines.append(f"\n<b>[Match #{idx}]</b>")
        if num:
            full_phone = f"{c_code} {num}".strip()
            lines.append(f"• <b>Phone:</b> <code>{c(full_phone)}</code>")
        if u_id:
            lines.append(f"• <b>User ID:</b> <code>{c(u_id)}</code>")
        if country:
            lines.append(f"• <b>Country:</b> {c(country)}")

    if params.get("service"):
        lines.append(f"\n• <b>Service:</b> {c(params.get('service'))}")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(DEV_TAG)
    return "\n".join(lines)


def format_hp_response(data: dict, query: str) -> str:
    info = data.get("data") or data
    if not info or data.get("error"):
        return f"⚠️ <code>{c(query)}</code> ke liye HP connection details nahi mili.\n\n{DEV_TAG}"

    name = info.get("consumerName") or info.get("name")
    phone = info.get("consumerPhone1") or query
    dob = info.get("dob")
    pincode = info.get("pinCode")

    return (
        f"⛽ <b>HP GAS CONNECTION RECORD</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Consumer Name:</b> <b>{c(name)}</b>\n"
        f"• <b>Registered Phone:</b> <code>{c(phone)}</code>\n"
        f"• <b>Date of Birth:</b> {c(dob)}\n"
        f"• <b>Pincode:</b> <code>{c(pincode)}</code>\n"
        f"• <b>Status:</b> 🟢 Verified\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{DEV_TAG}"
    )


def format_pan_v1_response(data: dict, query: str) -> str:
    info = data.get("data") or {}
    pan_no = data.get("pan") or query
    name = info.get("customerName") or f"{c(info.get('firstName'))} {c(info.get('lastName'))}".strip()
    status = info.get("panStatus", "VALID")
    dob = info.get("dob")

    return (
        f"💳 <b>PAN CARD RECORD (V1)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>PAN Number:</b> <code>{c(pan_no)}</code>\n"
        f"• <b>Name:</b> <b>{c(name)}</b>\n"
        f"• <b>DOB:</b> {c(dob)}\n"
        f"• <b>Status:</b> 🟢 {c(status)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{DEV_TAG}"
    )


def format_pan_v2_response(data: dict, query: str) -> str:
    info = data.get("data") or {}
    pan_no = info.get("pan_number") or query
    name = info.get("name") or f"{c(info.get('first_name'))} {c(info.get('last_name'))}".strip()
    status = info.get("pan_status", "VALID")
    dob = info.get("dob")
    gender = info.get("gender")
    category = info.get("category")
    is_linked = "Yes" if info.get("is_aadhaar_linked") else "No"

    return (
        f"💳 <b>PAN CARD RECORD (V2)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>PAN Number:</b> <code>{c(pan_no)}</code>\n"
        f"• <b>Name:</b> <b>{c(name)}</b>\n"
        f"• <b>Gender / Category:</b> {c(gender)} | {c(category)}\n"
        f"• <b>DOB:</b> {c(dob)}\n"
        f"• <b>Aadhaar Linked:</b> <code>{is_linked}</code>\n"
        f"• <b>PAN Status:</b> 🟢 {c(status)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{DEV_TAG}"
    )


def format_family_response(data: dict, query: str) -> str:
    details = data.get("details", {}).get("pd", {})
    rc_no = data.get("rationCardNumber") or details.get("rcId")
    scheme = details.get("schemeName") or details.get("schemeId")
    address = details.get("address")
    fps = details.get("fpsId")
    members = details.get("memberDetailsList", [])

    lines = [
        "👨‍👩‍👧‍👦 <b>RATION CARD & FAMILY TREE</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"• <b>Ration Card No:</b> <code>{c(rc_no)}</code>",
        f"• <b>Scheme:</b> {c(scheme)}",
        f"• <b>Dealer (FPS ID):</b> <code>{c(fps)}</code>",
        f"• <b>Address:</b> {c(address)}",
        f"\n<b>Registered Family Members ({len(members)}):</b>",
    ]

    for idx, m in enumerate(members, 1):
        m_name = m.get("memberName")
        rel = m.get("releationship_name")
        lines.append(f"  {idx}. <b>{c(m_name)}</b> — <i>{c(rel)}</i>")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(DEV_TAG)
    return "\n".join(lines)


def format_aadhar_response(data: dict, query: str) -> str:
    records = data.get("result") or data.get("RESULT") or []
    count = data.get("total_records") or data.get("COUNT") or len(records)

    if not records:
        return f"⚠️ <code>{c(query)}</code> ke liye koi linked record nahi mila.\n\n{DEV_TAG}"

    lines = [
        f"📑 <b>LINKED CONNECTIONS REPORT ({count} Records)</b>",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    for idx, r in enumerate(records, 1):
        name = r.get("name") or r.get("NAME")
        fname = r.get("father_name") or r.get("FNAME")
        num = r.get("mobile") or r.get("NUMBER")
        alt = r.get("alternate_mobile") or r.get("ALT")
        aadhar_val = str(r.get("aadhar") or r.get("AADHAAR") or r.get("aadhaar") or "").strip()
        circle = r.get("circle") or r.get("CIRCLE")
        email = r.get("email") or r.get("EMAIL")
        address = r.get("address") or r.get("ADDRESS")

        lines.append(f"\n<b>[Link #{idx}]</b>")
        lines.append(f"• <b>Name:</b> <b>{c(name)}</b>")
        lines.append(f"• <b>Father:</b> {c(fname)}")
        lines.append(f"• <b>Phone:</b> <code>{c(num)}</code>")
        if alt:
            lines.append(f"• <b>Alt Phone:</b> <code>{c(alt)}</code>")
        if aadhar_val and aadhar_val.lower() not in ("none", "null", "na"):
            lines.append(f"• <b>Aadhaar:</b> <code>{c(aadhar_val)}</code>")
        else:
            lines.append("• <b>Aadhaar:</b> <code>Not Linked / Not Available</code>")
        if email:
            lines.append(f"• <b>Email:</b> {c(email)}")
        lines.append(f"• <b>Circle:</b> {c(circle)}")
        if address:
            lines.append(f"• <b>Address:</b> {c(address)}")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━")
    lines.append(DEV_TAG)
    return "\n".join(lines)


def format_generic_card(cmd: str, payload: dict, query: str) -> str:
    if payload.get("error") == "no data found" or payload.get("status") == "FAILED":
        return f"⚠️ <b>No records found</b> for query: <code>{c(query)}</code>\n\n{DEV_TAG}"

    if cmd == "number":
        return format_number_response(payload, query)
    elif cmd == "hp":
        return format_hp_response(payload, query)
    elif cmd == "pan":
        return format_pan_v1_response(payload, query)
    elif cmd == "pan2":
        return format_pan_v2_response(payload, query)
    elif cmd == "family":
        return format_family_response(payload, query)
    elif cmd == "aadhar":
        return format_aadhar_response(payload, query)
    else:
        inner = payload.get("data") or payload.get("result") or payload
        lines = [
            f"🔎 <b>SEARCH REPORT: {cmd.upper()}</b>",
            "━━━━━━━━━━━━━━━━━━━━",
            f"• <b>Input:</b> <code>{c(query)}</code>",
        ]
        if isinstance(inner, dict):
            for k, v in inner.items():
                if isinstance(v, (str, int, float, bool)):
                    lines.append(f"• <b>{c(k).replace('_', ' ').title()}:</b> <code>{c(v)}</code>")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append(DEV_TAG)
        return "\n".join(lines)


# ==========================================
# COMMAND DISPATCHERS
# ==========================================

async def generic_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.split()[0].replace("/", "").lower()

    if not context.args:
        await update.message.reply_text(
            f"⚠️ <b>Input missing!</b>\nExample: <code>/{cmd} &lt;query&gt;</code>\n\n{DEV_TAG}",
            parse_mode=ParseMode.HTML,
        )
        return

    query_value = " ".join(context.args).strip()
    msg = await update.message.reply_text("🔄 <i>Searching records...</i>", parse_mode=ParseMode.HTML)

    params = {
        "key": API_KEY,
        "cmd": cmd,
        "query": query_value,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(API_BASE_URL, params=params)

        if resp.status_code != 200:
            await msg.edit_text(
                f"❌ <b>Server Error:</b> HTTP {resp.status_code}\n\n{DEV_TAG}",
                parse_mode=ParseMode.HTML,
            )
            return

        payload = resp.json()
        formatted_text = format_generic_card(cmd, payload, query_value)

        chunks = split_message(formatted_text)
        if len(chunks) == 1:
            await msg.edit_text(chunks[0], parse_mode=ParseMode.HTML)
        else:
            await msg.delete()
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode=ParseMode.HTML)

    except httpx.TimeoutException:
        await msg.edit_text(f"⏳ <b>Timeout:</b> API server took too long to respond.\n\n{DEV_TAG}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Error handling /{cmd}: {e}")
        await msg.edit_text(f"❌ <b>Error:</b> {c(str(e))}\n\n{DEV_TAG}", parse_mode=ParseMode.HTML)


async def tg_to_number_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            f"⚠️ <b>Input missing!</b>\nUsage: <code>/tg2num &lt;telegram_id_or_username&gt;</code>\n\n{DEV_TAG}",
            parse_mode=ParseMode.HTML,
        )
        return

    query_val = context.args[0].strip().replace("@", "")
    msg = await update.message.reply_text("🔄 <i>Searching Telegram ID...</i>", parse_mode=ParseMode.HTML)

    params = {
        "key": TG_TO_NUM_API_KEY,
        "q": query_val,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(TG_TO_NUM_API_URL, params=params)

        if resp.status_code != 200:
            await msg.edit_text(
                f"❌ <b>Server Error:</b> HTTP {resp.status_code}\n\n{DEV_TAG}",
                parse_mode=ParseMode.HTML,
            )
            return

        payload = resp.json()

        if isinstance(payload, dict) and payload.get("error"):
            err_msg = payload.get("error")
            await msg.edit_text(
                f"⚠️ <b>Service Notice:</b> {c(err_msg)}\n\n{DEV_TAG}",
                parse_mode=ParseMode.HTML,
            )
            return

        formatted_text = format_tg_to_num_response(payload, query_val)

        chunks = split_message(formatted_text)
        if len(chunks) == 1:
            await msg.edit_text(chunks[0], parse_mode=ParseMode.HTML)
        else:
            await msg.delete()
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode=ParseMode.HTML)

    except httpx.TimeoutException:
        await msg.edit_text(f"⏳ <b>Timeout:</b> Server took too long to respond.\n\n{DEV_TAG}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Error in tg2num: {e}")
        await msg.edit_text(f"❌ <b>Error:</b> {c(str(e))}\n\n{DEV_TAG}", parse_mode=ParseMode.HTML)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "✨ <b>RECORD VERIFICATION PORTAL</b> ✨\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Available commands:\n\n"
        "• <code>/number &lt;mobile&gt;</code> - Telecom records\n"
        "• <code>/hp &lt;mobile&gt;</code> - HP Gas connection\n"
        "• <code>/pan &lt;pan_no&gt;</code> - PAN verification (v1)\n"
        "• <code>/pan2 &lt;pan_no&gt;</code> - PAN details & seeding (v2)\n"
        "• <code>/upi &lt;vpa_id&gt;</code> - UPI verification\n"
        "• <code>/tg &lt;id&gt;</code> - Telegram user info (GBS API)\n"
        "• <code>/tg2num &lt;id&gt;</code> - Telegram to phone\n"
        "• <code>/family &lt;ref_id&gt;</code> - Ration / Family tree\n"
        "• <code>/aadhar &lt;ref_id&gt;</code> - Linked mobile records\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{DEV_TAG}"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)


def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("tg2num", tg_to_number_handler))

    commands = ["number", "hp", "upi", "pan", "pan2", "tg", "family", "aadhar"]
    for c_name in commands:
        app.add_handler(CommandHandler(c_name, generic_query_handler))

    print("Portal bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
