import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import time

TOKEN_OWNER = '8854868070:AAFcjbc5MCfemDVbJfMF1ecWEUNUMsuDcq0'
bot = telebot.TeleBot(TOKEN_OWNER)
DB_FILE = 'database.json'

admin_steps = {}

# --- SISTEMA DE SEGURIDAD (WHITELIST) ---
ADMIN_IDS = [8774603043]

def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "banned_resellers": [], 
            "banned_owners": [],
            "keys": [], 
            "resellers": {}, 
            "keys_status": "active", 
            "extra_owners": [], 
            "payment_methods": {"paypal": [], "zelle": []}
        }
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if "keys_status" not in data:
            data["keys_status"] = "active"
        if "extra_owners" not in data:
            data["extra_owners"] = []
        if "banned_owners" not in data:
            data["banned_owners"] = []
        if "payment_methods" not in data:
            data["payment_methods"] = {"paypal": [], "zelle": []}
        elif isinstance(data["payment_methods"], list):
            data["payment_methods"] = {"paypal": data["payment_methods"], "zelle": []}
        return data

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def es_admin_o_dueno(user_id):
    db = load_db()
    
    # Verificar si el owner está baneado en la base de datos
    if user_id in db.get("banned_owners", []):
        return False
    str_user_id = str(user_id)
    if str_user_id in db.get("banned_owners", []):
        return False

    if user_id in ADMIN_IDS:
        return True
        
    if user_id in db.get("extra_owners", []):
        return True
        
    banned_list = db.get("banned_resellers", [])
    resellers_list = db.get("resellers", {})
    
    if str_user_id in banned_list:
        return False
        
    if str_user_id in resellers_list:
        return True
        
    return False

# Decorador para restringir comandos
def solo_propietario_o_autorizado(func):
    def wrapper(message):
        user_id = message.from_user.id
        if not es_admin_o_dueno(user_id):
            bot.reply_to(message, "⛔ **Acceso denegado.** No tienes autorización para usar este bot o has sido baneado.", parse_mode="Markdown")
            return
        return func(message)
    return wrapper

# Decorador para restringir botones (callbacks)
def solo_propietario_callback(func):
    def wrapper(call):
        user_id = call.from_user.id
        if not es_admin_o_dueno(user_id):
            bot.answer_callback_query(call.id, "⛔ Acceso denegado o baneado.", show_alert=True)
            return
        return func(call)
    return wrapper
# ----------------------------------------

def get_owner_menu():
    db = load_db()
    current_status = db.get("keys_status", "active")
    freeze_text = "🟢 Unfreeze All Keys" if current_status == "frozen" else "❄️ Freeze All Keys"

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ Add Reseller", callback_data="add_reseller"),
        InlineKeyboardButton("🚫 Ban Reseller", callback_data="ban_reseller")
    )
    markup.add(
        InlineKeyboardButton("👑 Add Owner", callback_data="add_owner"),
        InlineKeyboardButton("⛔ Ban Owner", callback_data="ban_owner")
    )
    markup.add(
        InlineKeyboardButton("🔑 All Keys", callback_data="all_keys"),
        InlineKeyboardButton("🧹 Delete All Keys", callback_data="delete_all_keys")
    )
    markup.add(
        InlineKeyboardButton(freeze_text, callback_data="toggle_freeze_keys"),
        InlineKeyboardButton("📋 Resellers List", callback_data="resellers_list")
    )
    markup.add(
        InlineKeyboardButton("💵 Withdraw Money", callback_data="withdraw_money"),
        InlineKeyboardButton("💳 Métodos de Pago", callback_data="payment_methods_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
@solo_propietario_o_autorizado
def send_welcome(message):
    db = load_db()
    resellers_count = len(db.get("resellers", {}))
    keys_count = len(db.get("keys", []))
    status_text = "❄️ Congeladas" if db.get("keys_status") == "frozen" else "🟢 Activas"
    
    stats_text = (
        "👑 **OWNER CONTROL PANEL**\n\n"
        "📊 System Statistics:\n"
        f"┣ 👮 Resellers: {resellers_count}\n"
        f"┣ 🔑 Keys: {keys_count}\n"
        f"┣ 🛡️ Estado de Keys: {status_text}\n"
        "┗ 💲 Revenue: $45.00\n\n"
        "🎯 Select an option:"
    )
    bot.send_message(message.chat.id, stats_text, parse_mode="Markdown", reply_markup=get_owner_menu())

@bot.callback_query_handler(func=lambda call: True)
@solo_propietario_callback
def owner_callbacks(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    if call.data == "add_reseller":
        msg = bot.send_message(chat_id, "➕ Envía el **ID de Telegram o Username** del nuevo revendedor que deseas agregar:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_add_reseller)

    elif call.data == "add_owner":
        msg = bot.send_message(chat_id, "👑 Envía el **ID numérico de Telegram** del nuevo Owner que deseas agregar:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_add_owner)

    elif call.data == "ban_owner":
        msg = bot.send_message(chat_id, "⛔ Envía el **ID numérico de Telegram** del Owner que deseas banear:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_ban_owner)

    elif call.data == "ban_reseller":
        msg = bot.send_message(chat_id, "🚫 Envía el **ID de Telegram** del revendedor que deseas banear:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_ban_reseller)

    elif call.data == "all_keys":
        db = load_db()
        keys_list = "\n".join(db.get("keys", [])) if db.get("keys") else "No hay keys registradas."
        bot.send_message(chat_id, f"🔑 **Keys del Sistema:**\n\n{keys_list}", parse_mode="Markdown")

    elif call.data == "toggle_freeze_keys":
        db = load_db()
        current_status = db.get("keys_status", "active")
        
        if current_status == "active":
            db["keys_status"] = "frozen"
            msg_text = "❄️ **Contraseñas pausadas por actualización**"
        else:
            db["keys_status"] = "active"
            msg_text = "🟢 **¡Todas las keys han sido reactivadas!**"
            
        save_db(db)
        
        try:
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_owner_menu())
        except Exception:
            pass
            
        bot.send_message(chat_id, msg_text, parse_mode="Markdown")

    elif call.data == "delete_all_keys":
        db = load_db()
        db["keys"] = []
        for res_id in db.get("resellers", {}):
            db["resellers"][res_id]["keys_generated"] = []
        save_db(db)
        
        try:
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_owner_menu())
        except Exception:
            pass
            
        bot.send_message(chat_id, "🗑️ **Todas las keys han sido eliminadas**", parse_mode="Markdown")

    elif call.data == "resellers_list":
        msg = bot.send_message(chat_id, "📋 Envía el **ID o Username del revendedor** para ver cuántas keys ha generado y cuáles son:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_check_reseller_keys)

    elif call.data == "withdraw_money":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("➕ Agregar Saldo", callback_data="step_add_balance"),
            InlineKeyboardButton("➖ Restar Saldo", callback_data="step_sub_balance")
        )
        bot.send_message(chat_id, "💵 **Withdraw Money / Gestión de Saldo:**\n¿Qué acción deseas realizar?", parse_mode="Markdown", reply_markup=markup)

    elif call.data == "step_add_balance":
        admin_steps[chat_id] = {"action": "add"}
        msg = bot.send_message(chat_id, "👤 ¿A qué revendedor quieres agregarle saldo?\n\n*Envía el ID de Telegram o Username:*", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_ask_reseller_id)

    elif call.data == "step_sub_balance":
        admin_steps[chat_id] = {"action": "sub"}
        msg = bot.send_message(chat_id, "👤 ¿A qué revendedor quieres restarle saldo?\n\n*Envía el ID de Telegram o Username:*", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_ask_reseller_id)

    # --- MENÚ PRINCIPAL DE MÉTODOS DE PAGO ---
    elif call.data == "payment_methods_menu":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🅿️ PayPal", callback_data="pm_paypal"),
            InlineKeyboardButton("⚡ Zelle", callback_data="pm_zelle")
        )
        markup.add(InlineKeyboardButton("🔙 Volver al Menú", callback_data="back_to_main"))
        bot.edit_message_text("💳 **Gestión de Métodos de Pago**\nSelecciona el método que deseas gestionar:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    # --- SUBMENÚ PAYPAL ---
    elif call.data == "pm_paypal":
        text = (
            "🅿️ **PayPal Configurado:**\n\n"
            "Puedes realizar tus pagos a través del siguiente enlace:\n"
            "🔗 paypal.me/cuentasfreefire11"
        )
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🌐 Ir a Pagar (PayPal)", url="https://paypal.me/cuentasfreefire11"),
            InlineKeyboardButton("🔙 Volver", callback_data="payment_methods_menu")
        )
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True)

    # --- SUBMENÚ ZELLE ---
    elif call.data == "pm_zelle":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("➕ Agregar Datos Zelle", callback_data="add_zelle"),
            InlineKeyboardButton("📋 Ver Datos Zelle", callback_data="list_zelle"),
            InlineKeyboardButton("🔙 Volver", callback_data="payment_methods_menu")
        )
        bot.edit_message_text("⚡ **Gestión de Zelle**\n¿Qué deseas hacer?", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "add_zelle":
        msg = bot.send_message(chat_id, "⚡ Envía el correo o teléfono registrado en **Zelle**:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_save_zelle)

    elif call.data == "list_zelle":
        db = load_db()
        zelle_list = db.get("payment_methods", {}).get("zelle", [])
        if not zelle_list:
            text = "⚡ **Cuentas Zelle:**\n\nNo hay datos de Zelle configurados."
        else:
            list_str = "\n".join([f"• {item}" for item in zelle_list])
            text = f"⚡ **Cuentas Zelle Configuradas:**\n\n{list_str}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Volver", callback_data="pm_zelle"))
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "back_to_main":
        db = load_db()
        resellers_count = len(db.get("resellers", {}))
        keys_count = len(db.get("keys", []))
        status_text = "❄️ Congeladas" if db.get("keys_status") == "frozen" else "🟢 Activas"
        
        stats_text = (
            "👑 **OWNER CONTROL PANEL**\n\n"
            "📊 System Statistics:\n"
            f"┣ 👮 Resellers: {resellers_count}\n"
            f"┣ 🔑 Keys: {keys_count}\n"
            f"┣ 🛡️ Estado de Keys: {status_text}\n"
            "┗ 💲 Revenue: $45.00\n\n"
            "🎯 Select an option:"
        )
        bot.edit_message_text(stats_text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=get_owner_menu())

def process_save_zelle(message):
    if not es_admin_o_dueno(message.from_user.id):
        return
    new_zelle = message.text.strip()
    db = load_db()
    
    if "payment_methods" not in db:
        db["payment_methods"] = {"paypal": [], "zelle": []}
    if "zelle" not in db["payment_methods"]:
        db["payment_methods"]["zelle"] = []
        
    db["payment_methods"]["zelle"].append(new_zelle)
    save_db(db)
    bot.reply_to(message, f"✅ ¡Datos de Zelle agregados con éxito!\n\n`{new_zelle}`", parse_mode="Markdown")

def process_add_owner(message):
    if not es_admin_o_dueno(message.from_user.id):
        return
    
    try:
        new_owner_id = int(message.text.strip())
    except ValueError:
        bot.reply_to(message, "❌ El ID del Owner debe ser un número entero válido.")
        return

    db = load_db()
    if "extra_owners" not in db:
        db["extra_owners"] = []

    if new_owner_id not in db["extra_owners"] and new_owner_id not in ADMIN_IDS:
        db["extra_owners"].append(new_owner_id)
        save_db(db)
        bot.reply_to(message, f"👑 ¡El usuario con ID `{new_owner_id}` ha sido agregado como **Owner** exitosamente!", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Este usuario ya es un Owner registrado o es el Administrador principal.")

def process_ban_owner(message):
    if not es_admin_o_dueno(message.from_user.id):
        return
    
    try:
        banned_owner_id = int(message.text.strip())
    except ValueError:
        bot.reply_to(message, "❌ El ID del Owner debe ser un número entero válido.")
        return

    if banned_owner_id in ADMIN_IDS:
        bot.reply_to(message, "⛔ No puedes banear al administrador principal del sistema.")
        return

    db = load_db()
    if "banned_owners" not in db:
        db["banned_owners"] = []

    str_banned_id = str(banned_owner_id)
    if banned_owner_id not in db["banned_owners"] and str_banned_id not in db["banned_owners"]:
        db["banned_owners"].append(banned_owner_id)
        
        # Opcional: removerlo también de extra_owners si estaba ahí
        if banned_owner_id in db.get("extra_owners", []):
            db["extra_owners"].remove(banned_owner_id)

        save_db(db)
        bot.reply_to(message, f"⛔ El Owner con ID `{banned_owner_id}` ha sido **baneado** y ya no tiene acceso al bot.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Este Owner ya se encontraba baneado.")

def process_ask_reseller_id(message):
    if not es_admin_o_dueno(message.from_user.id):
        return
    chat_id = message.chat.id
    target_id = message.text.strip()
    
    if chat_id not in admin_steps:
        admin_steps[chat_id] = {}
        
    admin_steps[chat_id]["target_id"] = target_id
    
    msg = bot.send_message(chat_id, f"💰 ¿Cuánto saldo deseas **agregar/modificar** al revendedor `{target_id}`?\n\n*Envía únicamente el monto en números (Ej: 50 o 15.50):*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_receive_amount)

def process_receive_amount(message):
    if not es_admin_o_dueno(message.from_user.id):
        return
    chat_id = message.chat.id
    
    try:
        amount = float(message.text.strip())
    except ValueError:
        bot.reply_to(message, "❌ El monto debe ser un número válido. Inténtalo de nuevo desde el menú principal.")
        if chat_id in admin_steps:
            del admin_steps[chat_id]
        return
        
    if chat_id not in admin_steps or "target_id" not in admin_steps[chat_id]:
        bot.reply_to(message, "❌ Ocurrió un error en el proceso. Vuelve a iniciar la acción.")
        return
        
    data = admin_steps[chat_id]
    target_id = data["target_id"]
    action = data["action"]
    
    db = load_db()
    if "resellers" not in db:
        db["resellers"] = {}
        
    if target_id not in db["resellers"]:
        db["resellers"][target_id] = {"wallet": 30.00, "keys_generated": [], "banned_keys": []}
        
    current_wallet = db["resellers"][target_id]["wallet"]
    
    if action == "add":
        db["resellers"][target_id]["wallet"] = current_wallet + amount
        action_text = f"agregado (+${amount:.2f})"
    else:
        db["resellers"][target_id]["wallet"] = max(0.0, current_wallet - amount)
        action_text = f"restado (-${amount:.2f})"
        
    save_db(db)
    new_balance = db["resellers"][target_id]["wallet"]
    
    if chat_id in admin_steps:
        del admin_steps[chat_id]
    
    bot.reply_to(
        message,
        f"✅ **¡Saldo actualizado con éxito!**\n\n"
        f"┣ Revendedor: `{target_id}`\n"
        f"┣ Acción: Se han {action_text}\n"
        f"┗ **Nuevo balance en su Wallet:** ${new_balance:.2f}",
        parse_mode="Markdown"
    )

def process_add_reseller(message):
    if not es_admin_o_dueno(message.from_user.id):
        return
    new_reseller = message.text.strip()
    db = load_db()
    
    if "resellers" not in db:
        db["resellers"] = {}
        
    if new_reseller not in db["resellers"]:
        db["resellers"][new_reseller] = {"wallet": 30.00, "keys_generated": [], "banned_keys": []}
        save_db(db)
        bot.reply_to(message, f"✅ ¡Revendedor `{new_reseller}` agregado correctamente!", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Este revendedor ya se encuentra registrado.")

def process_ban_reseller(message):
    if not es_admin_o_dueno(message.from_user.id):
        return
    banned_id = message.text.strip()
    db = load_db()
    
    if "banned_resellers" not in db:
        db["banned_resellers"] = []
        
    if banned_id not in db["banned_resellers"]:
        db["banned_resellers"].append(banned_id)
        save_db(db)
        bot.reply_to(message, f"🚫 El revendedor `{banned_id}` ha sido **baneado**.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Este revendedor ya estaba baneado.")

def process_check_reseller_keys(message):
    if not es_admin_o_dueno(message.from_user.id):
        return
    target_reseller = message.text.strip()
    db = load_db()
    resellers_data = db.get("resellers", {})
    
    if target_reseller in resellers_data:
        reseller_info = resellers_data[target_reseller]
        keys_list = reseller_info.get("keys_generated", [])
        total_keys = len(keys_list)
        keys_str = "\n".join(keys_list) if keys_list else "Ninguna"
        
        response_text = (
            f"📋 **Reporte del Revendedor:** `{target_reseller}`\n\n"
            f"┣ 🔑 Keys generadas: **{total_keys}**\n"
            f"┗ 📝 Listado:\n{keys_str}"
        )
        bot.reply_to(message, response_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, f"❌ No se encontró ningún registro para el revendedor `{target_reseller}`.", parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot Owner activo y funcionando...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Error de conexión: {e}. Reiniciando en 5 segundos...")
            time.sleep(5)