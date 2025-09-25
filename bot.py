import telebot
from telebot import types
from twelvedata import TDClient
import time
import threading
import re
import pandas as pd
import numpy as np

# === CONFIG ===
API_KEY_TD = "e1110bca27aa4eefa87cd77b25a0697f"  # <- ton API key TwelveData
BOT_TOKEN = "8222947673:AAG4p4SaUQESQsMh736E9HdBuBu-jj9GAtc"  # <- ton token Telegram

bot = telebot.TeleBot(BOT_TOKEN)
td = TDClient(apikey=API_KEY_TD)

# === LANGUES ===
LANGUAGES = {
    "en": {
        "welcome": "👋 Welcome to *Sigma Bot*! 🎉\n\nChoose your language below 🌍",
        "after_lang": "✨ Welcome to Sigma Bot 🚀\n\n📌 Register on the trading platform with this referral code: *FRIENDZUCRESU35N* 🎁",
        "connect_btn": "🔗 Connect to the platform",
        "id_request": "🆔 Please enter your new account ID",
        "id_success": "✅ Success! Your account is connected 🎉",
        "start_btn": "🚀 Start",
        "choose_market": "📊 Choose your market:",
        "choose_platform": "🛠 Choose your trading platform:",
        "warning_pocket": "⚠️ If you choose Pocket Broker, signals are not for OTC markets but for real Forex 💹",
        "validation": "✅ Market and platform selected! Press below to get your signal 🚀",
        "signal_title": "📊 Market: {symbol}\n📈 Signal: {signal}\n💰 Entry: 2.00\n⛔ Stop Loss: {sl}\n🎯 Take Profit: {tp}\n⏱ Timeframe: 1m"
    },
    "fr": {
        "welcome": "👋 Bienvenue sur *Sigma Bot* 🎉\n\nChoisissez votre langue ci-dessous 🌍",
        "after_lang": "✨ Bienvenue sur Sigma Bot 🚀\n\n📌 Inscrivez-vous sur la plateforme trading avec ce code de parrainage : *FRIENDZUCRESU35N* 🎁",
        "connect_btn": "🔗 Connecter à la plateforme",
        "id_request": "🆔 Entrez l'ID de votre nouveau compte",
        "id_success": "✅ Succès ! Votre compte est connecté 🎉",
        "start_btn": "🚀 Commencer",
        "choose_market": "📊 Choisissez votre marché :",
        "choose_platform": "🛠 Choisissez votre plateforme de trading :",
        "warning_pocket": "⚠️ Si vous choisissez Pocket Broker, les signaux ne concernent pas le marché OTC mais uniquement le marché Forex réel 💹",
        "validation": "✅ Marché et plateforme choisis ! Appuyez ci-dessous pour obtenir votre signal 🚀",
        "signal_title": "📊 Marché : {symbol}\n📈 Signal : {signal}\n💰 Entry: 2.00\n⛔ Stop Loss: {sl}\n🎯 Take Profit: {tp}\n⏱ Timeframe: 1m"
    },
    "ht": {
        "welcome": "👋 Byenvini sou *Sigma Bot* 🎉\n\nChwazi lang ou anba a 🌍",
        "after_lang": "✨ Byenvini sou Sigma Bot 🚀\n\n📌 Enskri sou platfòm trading lan ak kòd parennaj sa a: *FRIENDZUCRESU35N* 🎁",
        "connect_btn": "🔗 Konekte ak platfòm nan",
        "id_request": "🆔 Mete ID nouvo kont ou",
        "id_success": "✅ Siksè ! Kont ou konekte 🎉",
        "start_btn": "🚀 Kòmanse",
        "choose_market": "📊 Chwazi mache ou:",
        "choose_platform": "🛠 Chwazi platfòm trading ou:",
        "warning_pocket": "⚠️ Si w chwazi Pocket Broker, siyal yo pa pou mache OTC men sèlman pou Forex reyèl 💹",
        "validation": "✅ Mache ak platfòm chwazi! Peze anba a pou jwenn siyal ou 🚀",
        "signal_title": "📊 Mache : {symbol}\n📈 Siyal : {signal}\n💰 Entry: 2.00\n⛔ Stop Loss: {sl}\n🎯 Take Profit: {tp}\n⏱ Timeframe: 1m"
    }
}

# === LISTES ===
markets = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD",
    "USD/CAD", "NZD/USD", "EUR/JPY", "GBP/JPY",
    "EUR/GBP", "USD/CHF"
]

platforms = [
    "MetaTrader 4", "MetaTrader 5", "TradingView",
    "Interactive Brokers", "Pocket Broker"
]

# === STOCKAGE ===
user_lang = {}
user_state = {}
countdowns = {}

# === STRATEGIE ZIGZAG ===
def zigzag(df, deviation=5, depth=3, backstep=2):
    df['zigzag'] = np.nan
    last_pivot = None
    for i in range(depth, len(df)-backstep):
        window = df['close'][i-depth:i+backstep]
        if df['close'][i] == window.max():
            last_pivot = ('high', df['close'][i])
        elif df['close'][i] == window.min():
            last_pivot = ('low', df['close'][i])
    return last_pivot

def get_signal(symbol, lang):
    try:
        ts = td.time_series(symbol=symbol, interval="1min", outputsize=100).as_pandas()
        ts = ts.reset_index()
        last_pivot = zigzag(ts)

        pip = 0.01 if "JPY" in symbol else 0.0001
        price = ts['close'].iloc[-1]

        sl_distance = 10 * pip
        tp_distance = 20 * pip

        if last_pivot and last_pivot[0] == 'low':
            signal = "BUY 🟢"
            sl = round(price - sl_distance, 5)
            tp = round(price + tp_distance, 5)
        else:
            signal = "SELL 🔴"
            sl = round(price + sl_distance, 5)
            tp = round(price - tp_distance, 5)

        return LANGUAGES[lang]["signal_title"].format(symbol=symbol, signal=signal, sl=sl, tp=tp)

    except Exception as e:
        return f"⚠️ Error fetching signal for {symbol}: {e}"

def start_countdown(chat_id):
    countdowns[chat_id] = 180
    while countdowns[chat_id] > 0:
        time.sleep(1)
        countdowns[chat_id] -= 1

# === HANDLERS ===
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    markup.add(types.InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"))
    markup.add(types.InlineKeyboardButton("🇭🇹 Kreyòl", callback_data="lang_ht"))
    bot.send_message(message.chat.id, "👋 Welcome / Bienvenue / Byenvini 🌍", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def choose_language(call):
    lang = call.data.replace("lang_", "")
    chat_id = call.message.chat.id
    user_lang[chat_id] = lang
    user_state[chat_id] = {}

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(LANGUAGES[lang]["connect_btn"], url="https://pocket-friends.com/r/zucresu35n")
    markup.add(btn)

    bot.send_message(chat_id, LANGUAGES[lang]["after_lang"], parse_mode="Markdown", reply_markup=markup)

    def ask_id():
        time.sleep(8)
        bot.send_message(chat_id, LANGUAGES[lang]["id_request"])
    threading.Thread(target=ask_id).start()

@bot.message_handler(func=lambda msg: msg.chat.id in user_lang and "market" not in user_state.get(msg.chat.id, {}) and re.fullmatch(r"\d{8}", msg.text))
def get_id(msg):
    lang = user_lang.get(msg.chat.id, "fr")
    bot.send_message(msg.chat.id, LANGUAGES[lang]["id_success"])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(LANGUAGES[lang]["start_btn"], callback_data="choose_market"))
    bot.send_message(msg.chat.id, "👇", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "choose_market")
def choose_market(call):
    lang = user_lang.get(call.message.chat.id, "fr")
    markup = types.InlineKeyboardMarkup()
    for m in markets:
        markup.add(types.InlineKeyboardButton(m, callback_data=f"market_{m}"))
    bot.send_message(call.message.chat.id, LANGUAGES[lang]["choose_market"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("market_"))
def choose_platform(call):
    chat_id = call.message.chat.id
    lang = user_lang.get(chat_id, "fr")
    market = call.data.replace("market_", "")
    user_state.setdefault(chat_id, {})
    user_state[chat_id]["market"] = market

    markup = types.InlineKeyboardMarkup()
    for p in platforms:
        markup.add(types.InlineKeyboardButton(p, callback_data=f"platform_{p}"))
    bot.send_message(chat_id, LANGUAGES[lang]["choose_platform"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("platform_"))
def confirm_strategy(call):
    chat_id = call.message.chat.id
    lang = user_lang.get(chat_id, "fr")
    platform = call.data.replace("platform_", "")
    user_state.setdefault(chat_id, {})
    user_state[chat_id]["platform"] = platform
    market = user_state[chat_id].get("market", "❓")

    if platform == "Pocket Broker":
        time.sleep(2)
        bot.send_message(chat_id, LANGUAGES[lang]["warning_pocket"])
        time.sleep(2)

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🚀 Get Signal / Obtenir un signal", callback_data="get_signal")
    markup.add(btn)

    # ✅ Message boosté avec marché et plateforme
    validation_msg = (
        f"✅🎉 Super!\n\n"
        f"📊 Market choisi : *{market}*\n"
        f"🛠 Plateforme : *{platform}*\n\n"
        f"🚀 Appuyez ci-dessous pour recevoir votre signal 🔥"
    )

    bot.send_message(chat_id, validation_msg, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "get_signal")
def send_signal(call):
    chat_id = call.message.chat.id
    lang = user_lang.get(chat_id, "fr")
    market = user_state.get(chat_id, {}).get("market", "EUR/USD")

    if chat_id in countdowns and countdowns[chat_id] > 0:
        mins, secs = divmod(countdowns[chat_id], 60)
        bot.answer_callback_query(call.id, f"⏳ Wait {mins}m {secs}s before next signal")
        return

    signal_msg = get_signal(market, lang)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Other Signal", callback_data="get_signal"))

    bot.send_message(chat_id, signal_msg, reply_markup=markup)

    threading.Thread(target=start_countdown, args=(chat_id,)).start()

# === RUN ===
print("🤖 Bot is running...")
bot.polling(none_stop=True)