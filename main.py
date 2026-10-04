from flask import Flask, request, jsonify
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import asyncio
import threading
import os
import time

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
    rc_number = update.message.text.strip()
    
    if len(rc_number) < 4 or len(rc_number) > 15:
        await update.message.reply_text("⚠️ **Invalid Format!** Please send a valid RC number.", parse_mode="Markdown")
        return

    wait_msg = await update.message.reply_text("🔍 **Searching database, please hold on...**", parse_mode="Markdown")

    start_time = time.time()
    raw_data = await asyncio.to_thread(get_vehicle_details, rc_number)
    elapsed_time = round((time.time() - start_time) * 1000, 2)

    if not raw_data or (isinstance(raw_data, dict) and "error" in raw_data):
        await wait_msg.edit_text(f"❌ **No details found for RC:** `{rc_number.upper()}`", parse_mode="Markdown")
        return

    # Extract nested data gracefully
    data = raw_data.get("details", raw_data)
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    owner_name = data.get("name") or data.get("othherData", {}).get("ownername", "N/A")
    brand = data.get("brand") or data.get("logo", "N/A")
    model = data.get("model") or data.get("vahanModel", "N/A")
    fuel = data.get("variant", {}).get("variant", [{}])[0].get("fueltype", "N/A")
    reg_date = data.get("regdate", "N/A")
    rto = data.get("rtoname") or data.get("rtoCity", "N/A")
    
    other = data.get("othherData", {})
    chassis = other.get("chassisNo", "N/A")
    engine = other.get("engineNo", "N/A")
    financer = other.get("finenciarName", "N/A")
    address = other.get("permanentAddress") or other.get("corosAddress", "N/A")

    insurance = data.get("insurance", {})
    ins_company = insurance.get("insurancecomp") or insurance.get("company", "N/A")
    ins_upto = insurance.get("insuranceupto") or insurance.get("expirydate", "N/A")

    # Build the clean, professional response layout
    response_text = f"🎉 **VEHICLE DETAILS FOUND!**\n\n"
    response_text += f"🚗 **RC Number:** `{rc_number.upper()}`\n"
    response_text += f"📊 **Results:** 1 found\n"
    response_text += f"⚡ **Time:** {elapsed_time}ms\n\n"
    response_text += f"📊 ── **Vehicle Details #1** ──\n"
    response_text += f"👤 **Owner Name:** {owner_name}\n"
    response_text += f"🏎️ **Model:** {model}\n"
    response_text += f"🏭 **Manufacturer:** {brand}\n"
    response_text += f"⛽ **Fuel Type:** {fuel}\n"
    response_text += f"📅 **Reg Date:** {reg_date}\n"
    response_text += f"🏢 **RTO:** {rto}\n"
    response_text += f"🔩 **Chassis No:** {chassis}\n"
    response_text += f"⚙️ **Engine No:** {engine}\n"
    response_text += f"🛡️ **Insurance Co:** {ins_company}\n"
    response_text += f"⏳ **Insurance Upto:** {ins_upto}\n"
    response_text += f"🏦 **Financer:** {financer}\n"
    response_text += f"🏠 **Address:** {address}\n\n"
    response_text += f"⚡ **Powered by:** @RD3B4T"

    await wait_msg.edit_text(response_text, parse_mode="Markdown")

def run_telegram_bot():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🤖 Telegram Bot is running with Clean Format...")
    application.run_polling()

if __name__ == "__main__":
    # Run Flask server in a background thread
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False), daemon=True).start()
    
    # Run Telegram bot in the main thread
    run_telegram_bot()
