import html
import logging
import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Direct credentials configuration
BOT_TOKEN = "8496632773:AAFTkCgRk8592Ij9Xz5uHy505dcO9_iRiNE"
API_KEY = "5RM3M"
API_URL = "https://admin.gbssystems.com/public/api/v1/api.php"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def clean(val) -> str:
    if val is None or str(val).strip() in ("", "None", "NA", "Array", "null"):
        return "N/A"
    return html.escape(str(val).strip())


def format_vehicle_rc(rc: dict) -> list[str]:
    lines = [
        "🚗 <b>VEHICLE REGISTRATION (RC) DETAILS</b>",
        f"• <b>RC Number:</b> <code>{clean(rc.get('rc_regn_no'))}</code>",
        f"• <b>Owner Name:</b> <b>{clean(rc.get('rc_owner_name'))}</b> (Owner #{clean(rc.get('rc_owner_sr'))})",
        f"• <b>Father / Husband:</b> {clean(rc.get('rc_f_name'))}",
        f"• <b>Mobile:</b> <code>{clean(rc.get('rc_mobile_no'))}</code>",
        f"• <b>Vehicle Model:</b> {clean(rc.get('rc_maker_model'))}",
        f"• <b>Manufacturer:</b> {clean(rc.get('rc_maker_desc'))}",
        f"• <b>Class / Body:</b> {clean(rc.get('rc_vh_class_desc'))} ({clean(rc.get('rc_body_type_desc'))})",
        f"• <b>Fuel Type:</b> {clean(rc.get('rc_fuel_desc'))} | <b>Color:</b> {clean(rc.get('rc_color'))}",
        f"• <b>Engine No:</b> <code>{clean(rc.get('rc_eng_no'))}</code>",
        f"• <b>Chassis No:</b> <code>{clean(rc.get('rc_chasi_no'))}</code>",
        f"• <b>Registration Date:</b> {clean(rc.get('rc_regn_dt'))}",
        f"• <b>Fitness / Tax Upto:</b> {clean(rc.get('rc_regn_upto'))}",
        f"• <b>RC Status:</b> <b>{clean(rc.get('rc_status'))}</b>",
        f"• <b>Registered RTO:</b> {clean(rc.get('rc_registered_at'))}",
        "\n🛡️ <b>Insurance & Compliance:</b>",
        f"• <b>Insurance Co:</b> {clean(rc.get('rc_insurance_comp'))}",
        f"• <b>Policy No:</b> <code>{clean(rc.get('rc_insurance_policy_no'))}</code>",
        f"• <b>Insurance Validity:</b> {clean(rc.get('rc_insurance_upto'))}",
        f"• <b>PUCC Validity:</b> {clean(rc.get('rc_pucc_upto'))} (<code>{clean(rc.get('rc_pucc_no'))}</code>)",
        f"\n📍 <b>Registered Address:</b>\n{clean(rc.get('rc_present_address'))}",
    ]
    return lines


def format_challans(challan_list: list) -> list[str]:
    lines = [f"📋 <b>TRAFFIC CHALLAN RECORDS ({len(challan_list)} Found)</b>"]
    for idx, ch in enumerate(challan_list, 1):
        status_text = clean(ch.get("status"))
        is_paid = ch.get("challan_status", False)
        status_badge = (
            "🟢 PAID"
            if (is_paid or status_text.lower() == "cash")
            else "🔴 PENDING"
        )

        lines.append(f"\n<b>[Challan #{idx}] - {status_badge}</b>")
        lines.append(f"• <b>Challan No:</b> <code>{clean(ch.get('challan_no'))}</code>")
        lines.append(f"• <b>Date & Time:</b> {clean(ch.get('challan_date'))}")
        lines.append(f"• <b>Fine Amount:</b> ₹{clean(ch.get('challan_fine'))}")

        offences = ch.get("offence_details", [])
        if offences:
            offence_names = [clean(o.get("name")) for o in offences]
            lines.append(f"• <b>Offence:</b> {', '.join(offence_names)}")

        lines.append(
            f"• <b>Location / RTO:</b> {clean(ch.get('rto_name'))} ({clean(ch.get('area_name'))})"
        )

        if ch.get("is_challan_in_court") == 1:
            lines.append(f"• ⚖️ <b>Sent To Court:</b> {clean(ch.get('court_name'))}")

        if is_paid and ch.get("payment_date"):
            lines.append(
                f"• <b>Paid On:</b> {clean(ch.get('payment_date'))} (Txn: <code>{clean(ch.get('transaction_id'))}</code>)"
            )

    return lines


def parse_vehicle_payload(data: dict) -> list[str]:
    messages = []
    blocks = []

    input_no = clean(data.get("input", "N/A"))
    blocks.append(f"🔎 <b>VEHICLE SEARCH REPORT</b>: <code>{input_no}</code>\n")

    vehicle_obj = data.get("results", {}).get("vehicle", {})

    v_details = vehicle_obj.get("vehicle_details")
    if v_details:
        blocks.extend(format_vehicle_rc(v_details))
        blocks.append("")
    else:
        blocks.append("⚠️ <i>RC details not found in API response.</i>\n")

    challans = vehicle_obj.get("challan_details", [])
    if challans:
        blocks.extend(format_challans(challans))
    else:
        blocks.append("✅ <b>No traffic challans recorded for this vehicle.</b>")

    full_text = "\n".join(blocks)

    while len(full_text) > 4000:
        split_idx = full_text.rfind("\n\n", 0, 4000)
        if split_idx == -1:
            split_idx = full_text.rfind("\n", 0, 4000)
        if split_idx == -1:
            split_idx = 4000
        messages.append(full_text[:split_idx].strip())
        full_text = full_text[split_idx:].strip()

    if full_text:
        messages.append(full_text)

    return messages


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Gadi ka registration number bhejein (jaise: <code>HR26EV0001</code>) RC aur Challan status janne ke liye.",
        parse_mode=ParseMode.HTML,
    )


async def handle_vehicle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rc_number = update.message.text.strip().replace(" ", "").upper()

    if len(rc_number) < 6:
        await update.message.reply_text("⚠️ Kripya valid registration number enter karein.")
        return

    msg = await update.message.reply_text("🔄 <i>Fetching RC and Challan records...</i>", parse_mode=ParseMode.HTML)

    try:
        params = {
            "key": API_KEY,
            "cmd": "vehicleall",
            "query": rc_number,
        }
        response = requests.get(API_URL, params=params, timeout=30)

        if response.status_code != 200:
            await msg.edit_text(f"❌ Server Error: HTTP {response.status_code}")
            return

        payload = response.json()

        if not payload.get("results") or not payload.get("results", {}).get("vehicle"):
            await msg.edit_text(f"⚠️ <code>{rc_number}</code> ke liye koi record nahi mila.", parse_mode=ParseMode.HTML)
            return

        chunks = parse_vehicle_payload(payload)
        await msg.delete()

        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode=ParseMode.HTML)

    except requests.exceptions.Timeout:
        await msg.edit_text("⏳ Request timeout ho gaya. API server respond nahi kar raha.")
    except Exception as e:
        logging.error(f"Execution Error: {e}")
        await msg.edit_text(f"❌ Error: {clean(str(e))}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vehicle_query))

    print("Vehicle Info Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
                                            
