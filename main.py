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
        "🚀 Send me any Vehicle RC Number (e.g., `UP70DN1860`) to get instant comprehensive details.\n\n"
        "⚡ **API DEVELOPER**: @RD3B4T",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rc_number = update.message.text.strip()
    
    if len(rc_number) < 4 or len(rc_number) > 15:
        await update.message.reply_text("⚠️ **Invalid Format!** Please send a valid RC number.", parse_mode="Markdown")
        return

    wait_msg = await update.message.reply_text("🔍 **Searching database, please hold on...**", parse_mode="Markdown")

    details = get_vehicle_details(rc_number)

    if not details or (isinstance(details, dict) and "error" in details):
        await wait_msg.edit_text(f"❌ **No details found for RC:** `{rc_number.upper()}`", parse_mode="Markdown")
        return

    # Premium Styled Response with Emojis
    response_text = f"🚘 **VEHICLE INFORMATION REPORT** 🚘\n"
    response_text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    response_text += f"📌 **RC Number:** `{rc_number.upper()}`\n\n"
    
    emoji_map = {
        "Owner Name": "👤",
        "Father's Name": "👨‍👦",
        "Owner Serial No": "🔢",
        "Model Name": "🏎️",
        "Maker Model": "🏭",
        "Vehicle Class": "🚙",
        "Fuel Type": "⛽",
        "Fuel Norms": "🌿",
        "Registration Date": "📅",
        "Insurance Company": "🏢",
        "Insurance No": "📄",
        "Insurance Expiry": "⏳",
        "Insurance Upto": "⏳",
        "Fitness Upto": "🛠️",
        "Tax Upto": "💰",
        "PUC No": "📋",
        "PUC Upto": "⏱️️",
        "Financier Name": "🏦",
        "Registered RTO": "📍",
        "Address": "🏠",
        "City Name": "🏙️",
        "Phone": "📞"
    }

    if isinstance(details, dict):
        for key, value in details.items():
            if value and key not in ["status", "credit"]:
                icon = emoji_map.get(key, "🔹")
                response_text += f"{icon} **{key}:** {value}\n"
    else:
        response_text += f"🔹 {details}\n"
            
    response_text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    response_text += f"⚡ **Powered by:** @RD3B4T"

    await wait_msg.edit_text(response_text, parse_mode="Markdown")

def run_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🤖 Telegram Bot is running with Premium Style...")
    application.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_telegram_bot, daemon=True).start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
