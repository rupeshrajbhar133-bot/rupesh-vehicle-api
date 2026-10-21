import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

TELEGRAM_BOT_TOKEN = "8496632773:AAEu1oWwnVwiov7b0Whs8sN9bSfScEmab5k"

# ------------------- #
# VEHICLE CHALLAN FETCHER #
# ------------------- #
def get_vehicle_details(rc_number: str) -> dict:
    """Fetches vehicle challan details using the updated API."""
    rc = rc_number.strip().upper()
    
    api_url = f"https://challan-info-new-abhigyan.vercel.app/challaninfo?vehicle={rc}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=6)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data
    except Exception as e:
        print(f"API Error: {e}")

    return {"error": "No details found"}

# ------------------- #
# TELEGRAM BOT LOGIC  #
# ------------------- #
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ **Welcome to Premium Vehicle Challan Bot** ✨\n\n"
        "🚀 Send me any Vehicle RC Number (e.g., `UP70AJ2399`) to check pending challans instantly.\n\n"
        "⚡ **API DEVELOPER**: @RD3B4T",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rc_number = update.message.text.strip().upper()
    
    if len(rc_number) < 4 or len(rc_number) > 15:
        await update.message.reply_text("⚠️ **Invalid Format!** Please send a valid RC number.", parse_mode="Markdown")
        return

    wait_msg = await update.message.reply_text("🔍 **Checking challan database, please hold on...**", parse_mode="Markdown")

    data = await asyncio.to_thread(get_vehicle_details, rc_number)

    if not data or (isinstance(data, dict) and data.get("error")):
        await wait_msg.edit_text(f"❌ **No details found for RC:** `{rc_number}`", parse_mode="Markdown")
        return

    vehicle = data.get("vehicle", rc_number)
    pending_count = data.get("pending_count", 0)
    pending_challans = data.get("pendingChallans", [])

    response_text = f"🚨 **ᴠᴇʜɪᴄʟᴇ ᴄʜᴀʟʟᴀɴ ʀᴇᴘᴏʀᴛ** 🚨\n"
    response_text += f"↔️↔️↔️↔️↔️↔️↔️↔️\n\n"
    response_text += f"🚗 **Vehicle Number:** `{vehicle}`\n"
    response_text += f"📋 **Pending Challans:** `{pending_count}`\n\n"

    if pending_count == 0 or not pending_challans:
        response_text += f"✅ **Great news! No pending challans found.**\n"
    else:
        for i, challan in enumerate(pending_challans, 1):
            c_no = challan.get("challanNumber", "N/A")
            issued = challan.get("issuedOn", "N/A")
            loc = challan.get("location", "N/A").replace("_", " ")
            violator = challan.get("violatorName", "N/A")
            
            violations_list = challan.get("violations", ["Traffic Rule Violation"])
            violation_desc = violations_list[0] if violations_list else "Traffic Rule Violation"
            
            amount = challan.get("amount", 0)
            convenience = challan.get("convenienceFees", 0)
            gst = challan.get("gstFee", 0)
            total = challan.get("totalAmount", amount)

            response_text += f"🛑 **Challan #{i}**\n"
            response_text += f"• **Challan No:** `{c_no}`\n"
            response_text += f"• **Issued On:** {issued}\n"
            response_text += f"• **Location:** {loc}\n"
            response_text += f"• **Violator:** {violator}\n"
            response_text += f"• **Violation:** {violation_desc}\n"
            response_text += f"• **Fine Amount:** ₹{amount}\n"
            response_text += f"• **Fees (Conv + GST):** ₹{convenience} + ₹{gst}\n"
            response_text += f"• **Total Amount:** **₹{total}**\n\n"

    response_text += f"↔️↔️↔️↔️↔️↔️↔️↔️\n"
    response_text += f"💻 **@RD3B4T**"

    await wait_msg.edit_text(response_text, parse_mode="Markdown")

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🤖 Telegram Bot is running smoothly and will not stop!")
    application.run_polling()

if __name__ == "__main__":
    main()
    
