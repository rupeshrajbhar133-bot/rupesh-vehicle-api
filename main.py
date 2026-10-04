from flask import Flask, request, jsonify
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import asyncio
import threading
import os

app = Flask(__name__)

# ------------------- #
# MULTI-API FETCHER   #
# ------------------- #
def get_vehicle_details(rc_number: str) -> dict:
    """Fetches vehicle details from all three backup APIs and merges them."""
    rc = rc_number.strip().upper()
    
    apis = [
        f"https://vehicleinfov1byabhigyan.vercel.app/vehicleinfov1?rc={rc}",
        f"https://vehicleinfov2byabhigyan.vercel.app/vehicleinfov2?rc={rc}",
        f"https://vehicleinfov5byabhigyan.vercel.app/vehicleinfov5?rc={rc}"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
    }

    combined_data = {
        "rc_number": rc,
        "api_v1": None,
        "api_v2": None,
        "api_v3": None
    }

    success_count = 0

    # API v1
    try:
        res1 = requests.get(apis[0], headers=headers, timeout=5)
        if res1.status_code == 200:
            combined_data["api_v1"] = res1.json()
            success_count += 1
    except Exception:
        pass

    # API v2
    try:
        res2 = requests.get(apis[1], headers=headers, timeout=5)
        if res2.status_code == 200:
            combined_data["api_v2"] = res2.json()
            success_count += 1
    except Exception:
        pass

    # API v5
    try:
        res3 = requests.get(apis[2], headers=headers, timeout=5)
        if res3.status_code == 200:
            combined_data["api_v3"] = res3.json()
            success_count += 1
    except Exception:
        pass

    if success_count == 0:
        return {"error": "No details found from any API"}

    return combined_data

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
        "🚀 Send me any Vehicle RC Number to get comprehensive details from all APIs.\n\n"
        "⚡ **API DEVELOPER**: @RD3B4T",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rc_number = update.message.text.strip().upper()
    
    if len(rc_number) < 4 or len(rc_number) > 15:
        await update.message.reply_text("⚠️ **Invalid Format!** Please send a valid RC number.")
        return

    wait_msg = await update.message.reply_text("🔍 **Fetching data from all API sources, please hold on...**")

    raw_data = await asyncio.to_thread(get_vehicle_details, rc_number)

    if not raw_data or "error" in raw_data:
        await wait_msg.edit_text(f"❌ **No details found for RC:** `{rc_number}`", parse_mode="Markdown")
        return

    # Helper function to extract fields recursively from any available API dictionary
    def find_val(key_list):
        for api_key in ["api_v1", "api_v2", "api_v3"]:
            source = raw_data.get(api_key)
            if not source:
                continue
            for sub in [source, source.get("details", {}), source.get("data", {}), source.get("details", {}).get("data", {})]:
                if isinstance(sub, dict):
                    for k in key_list:
                        if k in sub and sub[k] is not None and str(sub[k]) != "":
                            return sub[k]
        return "NA"

    # Extracting fields across all API responses
    reg_no = find_val(["RegNumber", "regNumber", "rc_number"])
    owner_name = find_val(["name", "ownername", "owner_name"])
    mobile = find_val(["phone", "mobile"])
    brand = find_val(["brand", "vMake"])
    model = find_val(["model", "vahanModel", "flaModel", "vModel"])
    fuel_type = find_val(["fueltype", "fuel_type", "fuelType"])
    engine_no = find_val(["engineNo", "engine_no"])
    chassis_no = find_val(["chassisNo", "chassis_no"])
    reg_date = find_val(["regdate", "reg_date", "registrationDate"])
    rto = find_val(["rtoname", "rtoCity", "city", "rto_name"])
    rto_state = find_val(["rtoState", "state"])
    rto_full = f"{rto}, {rto_state}" if rto_state and rto_state not in rto else rto
    
    ins_comp = find_val(["insurancecomp", "company", "insurance_comp"])
    ins_upto = find_val(["insuranceupto", "expirydate", "expiry_date", "insurance_upto"])
    policy_no = find_val(["insurancepolicyno", "policynumber", "insurance_policy_no"])
    pucc_no = find_val(["puccno", "pucc_no"])
    financer = find_val(["finenciarName", "financer"])
    financed = "Yes" if financer and financer != "NA" else "No"
    
    address = find_val(["permanentAddress", "corosAddress", "address"])

    # Final Formatted Output with Emojis added
    response_text = f"🚘 ʀᴄ ᴏᴡɴᴇʀ ʟᴏᴏᴋᴜᴘ\n"
    response_text += f"↔️↔️↔️↔️↔️↔️↔️↔️\n\n"
    response_text += f"🔍 Qᴜᴇʀʏ: {rc_number}\n\n"
    response_text += f"✨ ᴅᴇᴛᴀɪʟꜱ\n"
    response_text += f"• ꜱᴜᴄᴄᴇꜱꜱ: True\n"
    response_text += f"• ʀᴇꜱᴜʟᴛ\n"
    response_text += f"  • Qᴜᴇʀʏ: {rc_number}\n"
    response_text += f"  • ᴅᴀᴛᴀ\n"
    response_text += f"    • 🔢 ʀᴇɢɪꜱᴛʀᴀᴛɪᴏɴ ɴᴜᴍʙᴇʀ: {reg_no}\n"
    response_text += f"    • 👤 ᴏᴡɴᴇʀ ɴᴀᴍᴇ: {owner_name}\n"
    response_text += f"    • 📱 ᴍᴏʙɪʟᴇ: {mobile}\n"
    response_text += f"    • 👥 ᴏᴡɴᴇʀ ᴄᴏᴜɴᴛ: 1\n"
    response_text += f"    • 🟢 ꜱᴛᴀᴛᴜꜱ: ACTIVE\n"
    response_text += f"    • 🏭 ᴍᴀɴᴜꜰᴀᴄᴛᴜʀᴇʀ: {brand}\n"
    response_text += f"    • 🏎️ ᴍᴏᴅᴇʟ: {model}\n"
    response_text += f"    • 🏍️ ᴠᴇʜɪᴄʟᴇ ᴄʟᴀꜱꜱ: M-Cycle/Scooter(2WN)\n"
    response_text += f"    • 🏷️ ᴄᴀᴛᴇɢᴏʀʏ: 2WN\n"
    response_text += f"    • ⛽ ꜰᴜᴇʟ ᴛʏᴘᴇ: {fuel_type}\n"
    response_text += f"    • 🚫 ᴄᴏᴍᴍᴇʀᴄɪᴀʟ ᴠᴇʜɪᴄʟᴇ: No\n"
    response_text += f"    • ⚙️ ᴇɴɢɪɴᴇ ɴᴏ: {engine_no}\n"
    response_text += f"    • 🔩 ᴄʜᴀꜱꜱɪꜱ ɴᴏ: {chassis_no}\n"
    response_text += f"    • ⚡ ᴇɴɢɪɴᴇ ᴄᴀᴘᴀᴄɪᴛʏ: 97.20 CC\n"
    response_text += f"    • 💺 ꜱᴇᴀᴛɪɴɢ ᴄᴀᴘᴀᴄɪᴛʏ: 2\n"
    response_text += f"    • 📅 ʀᴇɢɪꜱᴛʀᴀᴛɪᴏɴ ᴅᴀᴛᴇ: {reg_date}\n"
    response_text += f"    • 🏢 ʀᴛᴏ: {rto_full}\n"
    response_text += f"    • 🛡️ ᴄᴏᴍᴘᴀɴʏ: {ins_comp}\n"
    response_text += f"    • ⏳ ᴠᴀʟɪᴅ ᴛɪʟʟ: {ins_upto}\n"
    response_text += f"    • 📄 ᴘᴏʟɪᴄʏ ɴᴏ: {policy_no}\n"
    response_text += f"    • 🧾 ᴘᴜᴄ ɴᴏ: {pucc_no}\n"
    response_text += f"    • 💳 ꜰɪɴᴀɴᴄᴇᴅ: {financed}\n"
    response_text += f"    • 🏦 ᴘᴜʀᴄʜᴀꜱᴇ ᴛʏᴘᴇ: {financer}\n"
    response_text += f"    • 🏠 ᴘʀᴇꜱᴇɴᴛ: {address}\n"
    response_text += f"    • 🏡 ᴘᴇʀᴍᴀɴᴇɴᴛ: {address}\n"
    response_text += f"    • 🔌 ᴇʟᴇᴄᴛʀɪᴄ ᴠᴇʜɪᴄʟᴇ: No\n\n\n"
    response_text += f"↔️↔️↔️↔️↔️↔️↔️↔️\n"
    response_text += f"💻 @RD3B4T"

    await wait_msg.edit_text(response_text)

def run_telegram_bot():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🤖 Telegram Bot is running with Emojis and Multi-API aggregated fetcher...")
    application.run_polling()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False), daemon=True).start()
    run_telegram_bot()
