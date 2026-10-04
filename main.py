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
    rc_number = update.message.text.strip()
    
    if len(rc_number) < 4 or len(rc_number) > 15:
        await update.message.reply_text("⚠️ **Invalid Format!** Please send a valid RC number.", parse_mode="Markdown")
        return

    wait_msg = await update.message.reply_text("🔍 **Searching database, please hold on...**", parse_mode="Markdown")

    details = await asyncio.to_thread(get_vehicle_details, rc_number)

    if not details or (isinstance(details, dict) and "error" in details):
        await wait_msg.edit_text(f"❌ **No details found for RC:** `{rc_number.upper()}`", parse_mode="Markdown")
        return

    vehicle_data = details.get("details", details)
    if isinstance(vehicle_data, dict) and "vehicleDetails" in vehicle_data:
        v_info = vehicle_data["vehicleDetails"]
    else:
        v_info = vehicle_data

    response_text = f"🚘 **VEHICLE INFORMATION REPORT** 🚘\n"
    response_text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    response_text += f"📌 **RC Number:** `{rc_number.upper()}`\n\n"
    
    emoji_map = {
        "firstName": "👤 Owner Name",
        "chassisNo": "🔩 Chassis No",
        "engineNo": "⚙️ Engine No",
        "makerModel": "🏎️ Model",
        "fuelType": "⛽ Fuel Type",
        "registrationDate": "📅 Reg. Date",
        "rtoLocation": "📍 RTO Location",
        "ownerSerialNo": "🔢 Owner Serial",
        "vehicleClass": "🚙 Vehicle Class"
    }

    if isinstance(v_info, dict):
        for key, value in v_info.items():
            if value:
                label = emoji_map.get(key, f"🔹 {key}")
                if key == "firstName":
                    last = v_info.get("lastName", "")
                    response_text += f"👤 **Owner Name:** {value} {last}\n"
                elif key == "lastName":
                    continue
                else:
                    response_text += f"{label}: {value}\n"
    else:
        response_text += f"🔹 {v_info}\n"
            
    response_text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    response_text += f"⚡ **Powered by:** @RD3B4T"

    await wait_msg.edit_text(response_text, parse_mode="Markdown")

def run_telegram_bot():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🤖 Telegram Bot is running with Premium Style...")
    application.run_polling()

if __name__ == "__main__":
    # Run Flask server in a background thread
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False), daemon=True).start()
    
    # Run Telegram bot in the main thread (fixes set_wakeup_fd error)
    run_telegram_bot()
