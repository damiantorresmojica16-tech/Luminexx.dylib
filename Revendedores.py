import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import random
import string
import time

TOKEN_RESELLER = “8712217253:AAGmnCdbIYFLOKtaHQLjLoGlc7bWsDgo2xI”
bot = telebot.TeleBot(TOKEN_RESELLER)
DB_FILE = 'database.json'

PRICES = {
    "1_day": {"name": "1 Día", "price": 7.00, "code": "DAY"},
    "7_days": {"name": "7 Días", "price": 15.00, "code": "WEEK"},
    "31_days": {"name": "31 Días", "price": 25.00, "code": "MONTH"}
}

def load_db():
    if not os.path.exists(DB_FILE):
        return {"banned_resellers": [], "keys": [], "resellers": {}}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def is_banned(user_id):
    db = load_db()
    return str(user_id) in db.get("banned_resellers", [])

def get_reseller_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("💳 Generate license key", callback_data="generate_key"))
    markup.add(
        InlineKeyboardButton("🔑 My Keys", callback_data="my_keys"),
        InlineKeyboardButton("🚫 Ban Key", callback_data="ban_key")
    )
    markup.add(
        InlineKeyboardButton("💰 Wallet Info", callback_data="wallet_info"),
        InlineKeyboardButton("🌐 Language", callback_data="language")
    )
    markup.add(InlineKeyboardButton("💬 Support", callback_data="support"))
    return markup

@bot.message_handler(commands=['start'])
def send_reseller_start(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.reply_to(message, "❌ **Acceso denegado:** Tu cuenta ha sido baneada por el administrador.", parse_mode="Markdown")
        return

    db = load_db()
    resellers_data = db.get("resellers", {})
    user_str = str(user_id)
    
    reseller_info = resellers_data.get(user_str, {"wallet": 30.00, "keys_generated": [], "banned_keys": []})
    
    total_keys = len(reseller_info.get("keys_generated", []))
    active_keys = total_keys - len(reseller_info.get("banned_keys", []))

    panel_text = (
        f"👮 **RESELLER PANEL**\n\n"
        f"Welcome back! 👋\n\n"
        f"📊 Your Statistics:\n"
        f"┣ 💰 Wallet: ${reseller_info.get('wallet', 30.00):.2f}\n"
        f"┣ 🔑 Keys: {total_keys}\n"
        f"┗ ✅ Active: {active_keys}\n\n"
        f"💲 Pricing:\n"
        f"┣ Day: $7.00\n"
        f"┣ Week: $15.00\n"
        f"┗ Month: $25.00\n\n"
        f"🎯 Select an option:"
    )
    bot.send_message(message.chat.id, panel_text, parse_mode="Markdown", reply_markup=get_reseller_menu())

@bot.callback_query_handler(func=lambda call: True)
def reseller_callbacks(call):
    user_id = call.from_user.id
    
    if is_banned(user_id):
        bot.answer_callback_query(call.id, text="Acceso denegado (Baneado)", show_alert=True)
        return

    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    if call.data == "generate_key":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📅 1 Día ($7.00)", callback_data="buy_1_day"),
            InlineKeyboardButton("📅 7 Días ($15.00)", callback_data="buy_7_days"),
            InlineKeyboardButton("📅 31 Días ($25.00)", callback_data="buy_31_days")
        )
        bot.send_message(chat_id, "⏱️ **Selecciona la duración de la key que deseas generar:**", parse_mode="Markdown", reply_markup=markup)

    elif call.data.startswith("buy_"):
        duration_key = call.data.replace("buy_", "")
        if duration_key not in PRICES:
            return
            
        selected_plan = PRICES[duration_key]
        cost = selected_plan["price"]
        
        db = load_db()
        user_str = str(user_id)
        
        if "resellers" not in db:
            db["resellers"] = {}
        if user_str not in db["resellers"]:
            db["resellers"][user_str] = {"wallet": 30.00, "keys_generated": [], "banned_keys": []}
            
        current_wallet = db["resellers"][user_str].get("wallet", 30.00)
        
        if current_wallet < cost:
            bot.send_message(
                chat_id, 
                f"❌ **Saldo insuficiente:** No tienes suficiente dinero en tu wallet.\n"
                f"┣ Costo de la key: **${cost:.2f}**\n"
                f"┗ Tu balance actual: **${current_wallet:.2f}**", 
                parse_mode="Markdown"
            )
            return

        db["resellers"][user_str]["wallet"] = current_wallet - cost
        
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        new_key = f"WIDMAN-WEB-{selected_plan['code']}-{random_suffix}"
        
        db["resellers"][user_str]["keys_generated"].append(new_key)
        
        if "keys" not in db:
            db["keys"] = []
        db["keys"].append(new_key)
        
        save_db(db)
        
        new_balance = db["resellers"][user_str]["wallet"]
        bot.send_message(
            chat_id, 
            f"✅ **Licencia Generada ({selected_plan['name']}):**\n"
            f"`{new_key}`\n\n"
            f"💰 Nuevo balance en wallet: **${new_balance:.2f}**\n"
            f"*Tap the code or copy to send to the user.*", 
            parse_mode="Markdown"
        )

    elif call.data == "my_keys":
        db = load_db()
        user_str = str(user_id)
        resellers_data = db.get("resellers", {})
        
        keys = []
        if user_str in resellers_data:
            keys = resellers_data[user_str].get("keys_generated", [])
            
        keys_text = "\n".join(keys) if keys else "No tienes keys generadas."
        bot.send_message(chat_id, f"🔑 **Tus Keys Generadas:**\n\n{keys_text}", parse_mode="Markdown")

    elif call.data == "wallet_info":
        db = load_db()
        user_str = str(user_id)
        resellers_data = db.get("resellers", {})
        wallet = 30.00
        if user_str in resellers_data:
            wallet = resellers_data[user_str].get("wallet", 30.00)
            
        bot.send_message(chat_id, f"💰 **Estado de tu Wallet:**\nBalance actual: ${wallet:.2f}", parse_mode="Markdown")

    else:
        bot.send_message(chat_id, f"Opción seleccionada: {call.data}")

if __name__ == "__main__":
    print("Bot de Revendedor iniciado y en línea...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Error de conexión: {e}. Reiniciando en 5 segundos...")
            time.sleep(5)
