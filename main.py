import sys
import telebot
from telebot import types

# تعریف ربات
bot = telebot.TeleBot("8737266392:AAESkBZydXimoMGVbKiFiZ1i9sahQMt-Xvg")

# ایمپورت پلاگین‌ها و دیتابیس
from data_store import admin_states
from database import ensure_user, get_user
from core.registry import get
import plugins.management_plugin
import plugins.economy_plugin, plugins.referral_plugin, plugins.ai_plugin
import plugins.admin_plugin, plugins.profile_plugin, plugins.tools_plugin, plugins.proxy_plugin

CHANNEL_ID = "@Newsswss"
ADMIN_ID = 123456789  # فراموش نکن اینجا آیدی عددی خودت رو بعداً جایگزین کنی

def get_main_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    menu.add(
        types.KeyboardButton("🤖 هوش مصنوعی"), types.KeyboardButton("🛠 ابزارهای مالی"),
        types.KeyboardButton("🎰 گردونه شانس"), types.KeyboardButton("📡 پروکسی"),
        types.KeyboardButton("👤 پروفایل"), types.KeyboardButton("💰 کیف پول"),
        types.KeyboardButton("🛡 پنل مدیریت"), types.KeyboardButton("📢 درخواست اتصال کانال")
    )
    return menu

def check_membership(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    ensure_user(message.from_user.id)
    bot.send_message(message.chat.id, "🦅 ققنوس بیدار شد!", reply_markup=get_main_menu())

@bot.message_handler(func=lambda message: True)
def main_handler(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if text == "📢 درخواست اتصال کانال":
        bot.send_message(message.chat.id, "📝 لطفاً آیدی کانال خود را بفرستید:")
        admin_states[user_id] = "waiting_for_channel"
        return

    if admin_states.get(user_id) == "waiting_for_channel":
        plugins.management_plugin.send_approval_request(bot, user_id, message.from_user.username, text)
        bot.send_message(message.chat.id, "✅ درخواست شما ارسال شد.")
        admin_states[user_id] = None
        return

    if not check_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 عضویت", url="https://t.me/Newsswss"))
        markup.add(types.InlineKeyboardButton("✅ تأیید", callback_data="check_sub"))
        bot.send_message(message.chat.id, "⚠️ ابتدا عضو شوید:", reply_markup=markup)
        return

    plugin_map = {
        "💰 دریافت سکه": "economy", "🎰 گردونه شانس": "economy", "💰 کیف پول": "economy",
        "👤 پروفایل": "profile_system", "🤖 هوش مصنوعی": "ai", "🛠 ابزارهای مالی": "tools",
        "📡 پروکسی": "proxy", "🛡 پنل مدیریت": "management"
    }
    
    plugin_name = plugin_map.get(text, "admin" if text.startswith("/") else None)
    plugin_func = get(plugin_name)
    
    if plugin_func:
        result = plugin_func(message.from_user, text, get_user(user_id))
        res_text = result.get("text") if isinstance(result, dict) else str(result)
        bot.send_message(message.chat.id, res_text, reply_markup=get_main_menu())
    else:
        bot.send_message(message.chat.id, "🦅 متوجه نشدم.", reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith("approve_") or call.data.startswith("reject_"):
        plugins.management_plugin.process_callback(bot, call)
    elif call.data == "check_sub":
        if check_membership(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ تایید شد!")
            bot.send_message(call.message.chat.id, "🦅 خوش آمدید!", reply_markup=get_main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ هنوز عضو نشدید!", show_alert=True)

if __name__ == "__main__":
    while True:
        try:
            bot.infinity_polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            import time
            time.sleep(5)
