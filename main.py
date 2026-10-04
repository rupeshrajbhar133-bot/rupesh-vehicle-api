from flask import Flask, request, jsonify
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import asyncio
import threading
import os

app = Flask(__name__)

# ------------------- #
# VEHICLE INFO FETCHER#
# ------------------- #
def get_vehicle_details(rc_number: str) -> dict:
    """Fetches vehicle details using multiple backup APIs."""
    rc = rc_number.strip().upper()
    
    apis = [
        f"https://vehicleinfov1byabhigyan.vercel.app/vehicleinfov1?rc={rc}",
        f"https://vehicleinfov2byabhigyan.vercel.app/vehicleinfov2?rc={rc}",
        f"https://vehicleinfov5byabhigyan.vercel.app/vehicleinfov5?rc={rc}"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
    }

    for url in apis:
        try:
            response = requests.get(url, headers=headers, timeout=6)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data
        except Exception:
            continue

    return {"error": "No details found"}

# ------------------- #
# FLASK API ROUTE     #
# ------------------- #
@app.route("/", methods=["GET"])
def api():
    rc_number = request.args.get("rc_number")

    if not rc_number:
        return jsonify({
            "credit": "API DEVELOPER: @RD3B4T",
            "status": "error",
            "message": "Missing required parameter: rc_number"
        }), 400

    details = get_vehicle_details(rc_number)

    if isinstance(details, dict) and "error" in details:
        return jsonify({
            "credit": "API DEVELOPER: @RD3B4T",
            "status": "not_found",
            "message": details["error"]
        }), 404

    return jsonify({
        "credit": "API DEVELOPER : @RD3B4T",
        "status": "success",
        "rc_number": rc_number.upper(),
        "details": details
    })

# ------------------- #
# TELEGRAM BOT LOGIC  #
# ------------------- #
TELEGRAM_BOT_TOKEN = "8496632773:AAHdTKxY_iNN3-sSsJmgzBw4zmOIZeB5mrY"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ **Welcome to Premium Vehicle Info Bot** ✨\n\n"
        "🚀 Send me any Vehicle RC Number (e.g., `UP61BN5256`) to get instant comprehensive details.\n\n"
        "⚡ **API DEVELOPER**: @RD3B4T",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rc_number = update.message.text.strip().upper()
    
    if len(rc_number) < 4 or len(rc_number) > 15:
        await update.message.reply_text("⚠️ **Invalid Format!** Please send a valid RC number.", parse_mode="Markdown")
        return

    wait_msg = await update.message.reply_text("🔍 **Searching database, please hold on...**", parse_mode="Markdown")

    raw_data = await asyncio.to_thread(get_vehicle_details, rc_number)

    if not raw_data or (isinstance(raw_data, dict) and "error" in raw_data):
        await wait_msg.edit_text(f"❌ **No details found for RC:** `{rc_number}`", parse_mode="Markdown")
        return

    # Extracting inner structure safely
    data = raw_data.get("details", raw_data)
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    other = data.get("othherData", {})
    if not isinstance(other, dict):
        other = {}

    insurance = data.get("insurance", {})
    if not isinstance(insurance, dict):
        insurance = {}

    variant_list = data.get("variant", {}).get("variant", [])
    variant_info = variant_list[0] if isinstance(variant_list, list) and len(variant_list) > 0 else {}

    # Field Mappings matching your exact desired look
    reg_no = data.get("RegNumber") or rc_number
    owner_name = data.get("name") or other.get("ownername") or "NA"
    mobile = data.get("phone") or "NA"
    brand = data.get("brand") or variant_info.get("vMake", "NA")
    model = data.get("model") or data.get("vahanModel") or variant_info.get("vModel", "NA")
    variant_name = variant_info.get("label") or "NA"
    v_class = data.get("type", "M-Cycle/Scooter(2WN)")
    fuel_type = variant_info.get("fueltype") or data.get("fuelType", "PETROL")
    engine_no = other.get("engineNo") or "NA"
    chassis_no = other.get("chassisNo") or "NA"
    cc = variant_info.get("cc")
    engine_capacity = f"{cc}.00 CC" if cc else "NA"
    reg_date = data.get("regdate") or "NA"
    rto_city = data.get("rtoname") or data.get("rtoCity") or "NA"
    rto_state = data.get("rtoState", "")
    rto_full = f"{rto_city}, {rto_state}" if rto_state else rto_city
    
    ins_comp = insurance.get("insurancecomp") or insurance.get("company", "NA")
    ins_upto = insurance.get("insuranceupto") or insurance.get("expirydate", "NA")
    policy_no = insurance.get("insurancepolicyno") or insurance.get("policynumber", "NA")
    pucc_no = insurance.get("puccno", "NA")
    financer = other.get("finenciarName", "NA")
    financed = "Yes" if financer and financer != "NA" else "No"
    
    address = other.get("permanentAddress") or other.get("corosAddress") or "NA"

    # Constructing the exact requested output format
    response_text = f"🚘 ʀᴄ ᴏᴡɴᴇʀ ʟᴏᴏᴋᴜᴘ\n"
    response_text += f"↔️↔️↔️↔️↔️↔️↔️↔️\n\n"
    response_text += f"🔍 Qᴜᴇʀʏ: {rc_number}\n\n"
    response_text += f"✨ ᴅᴇᴛᴀɪʟꜱ\n"
    response_text += f"• ꜱᴜᴄᴄᴇꜱꜱ: True\n"
    response_text += f"• ʀᴇꜱᴜʟᴛ\n"
    response_text += f"  • Qᴜᴇʀʏ: {rc_number}\n"
    response_text += f"  • ᴅᴀᴛᴀ\n"
    response_text += f"    • ʀᴇɢɪꜱᴛʀᴀᴛɪᴏɴ ɴᴜᴍʙᴇʀ: {reg_no}\n"
    response_text += f"    • ᴏᴡɴᴇʀ ɴᴀᴍᴇ: {owner_name}\n"
    response_text += f"    • ᴍᴏʙɪʟᴇ: {mobile}\n"
    response_text += f"    • ᴏᴡɴᴇʀ ᴄᴏᴜɴᴛ: 1\n"
    response_text += f"    • ꜱᴛᴀᴛᴜꜱ: ACTIVE\n"
    response_text += f"    • ᴍᴀɴᴜꜰᴀᴄᴛᴜʀᴇʀ: {brand}\n"
    response_text += f"    • ᴍᴏᴅᴇʟ: {model}\n"
    response_text += f"    • ᴠᴀʀɪᴀɴᴛ: {variant_name}\n"
    response_text += f"    • ᴠᴇʜɪᴄʟᴇ ᴄʟᴀꜱꜱ: {v_class}\n"
    response_text += f"    • ᴄᴀᴛᴇɢᴏʀʏ: 2WN\n"
    response_text += f"    • ꜰᴜᴇʟ ᴛʏᴘᴇ: {fuel_type}\n"
    response_text += f"    • ᴄᴏᴍᴍᴇʀᴄɪᴀʟ ᴠᴇʜɪᴄʟᴇ: No\n"
    response_text += f"    • ᴇɴɢɪɴᴇ ɴᴏ: {engine_no}\n"
    response_text += f"    • ᴄʜᴀꜱꜱɪꜱ ɴᴏ: {chassis_no}\n"
    response_text += f"    • ᴇɴɢɪɴᴇ ᴄᴀᴘᴀᴄɪᴛʏ: {engine_capacity}\n"
    response_text += f"    • ꜱᴇᴀᴛɪɴɢ ᴄᴀᴘᴀᴄɪᴛʏ: 2\n"
    response_text += f"    • ʀᴇɢɪꜱᴛʀᴀᴛɪᴏɴ ᴅᴀᴛᴇ: {reg_date}\n"
    response_text += f"    • ʀᴛᴏ: {rto_full}\n"
    response_text += f"    • ᴄᴏᴍᴘᴀɴʏ: {ins_comp}\n"
    response_text += f"    • ᴠᴀʟɪᴅ ᴛɪʟʟ: {ins_upto}\n"
    response_text += f"    • ᴘᴏʟɪᴄʏ ɴᴏ: {policy_no}\n"
    response_text += f"    • ᴘᴜᴄ ɴᴏ: {pucc_no}\n"
    response_text += f"    • ꜰɪɴᴀɴᴄᴇᴅ: {financed}\n"
    response_text += f"    • ᴘᴜʀᴄʜᴀꜱᴇ ᴛʏᴘᴇ: {financer}\n"
    response_text += f"    • ᴘʀᴇꜱᴇɴᴛ: {address}\n"
    response_text += f"    • ᴘᴇʀᴍᴀɴᴇɴᴛ: {address}\n"
    response_text += f"    • ᴇʟᴇᴄᴛʀɪᴄ ᴠᴇʜɪᴄʟᴇ: No\n\n\n"
    response_text += f"↔️↔️↔️↔️↔️️↔️↔️↔️\n"
    response_text += f"💻 @RD3B4T"

    await wait_msg.edit_text(response_text)

def run_telegram_bot():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🤖 Telegram Bot is running with exact custom format...")
    application.run_polling()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False), daemon=True).start()
    run_telegram_bot()
