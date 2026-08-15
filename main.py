import telebot
from telebot import types
import json
import os
import random

TOKEN = "8816940858:AAEwDQ94ues00rcG1RVkNMPumQh7Xxgfowc"
bot = telebot.TeleBot(TOKEN)

DB_FILE = "movies.json"
VIP_DB_FILE = "vip_movies.json"
VIP_FILE = "vip.json"
BANNED_FILE = "banned.json"
ADMINS = [8753350906]  # Sizning ID raqamingiz
ADMIN_USERNAME = "mhdnvwv"

CARD_NUMBER = "6262 5701 4806 4381"
CARD_HOLDER = "Obidjonova M"

# 3 ta zaif kanal va 1 ta UzMafiya (jami 4 ta majburiy kanal)
REQUIRED_CHANNELS = [
    {"username": "@kanal_1", "name": "1-Kanal"},
    {"username": "@kanal_2", "name": "2-Kanal"},
    {"username": "@kanal_3", "name": "3-Kanal"},
    {"username": "@uzmafiya", "name": "UzMafiya"}
]

FORBIDDEN_WORDS = ["porno", "sex", "sins", "xxx", "zino", "intim", "porno_video"]

for file_path, default_content in [(DB_FILE, {}), (VIP_DB_FILE, {}), (VIP_FILE, []), (BANNED_FILE, [])]:
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump(default_content, f)

def is_banned(user_id):
    with open(BANNED_FILE, "r") as f:
        banned = json.load(f)
    return user_id in banned

def ban_user(user_id):
    with open(BANNED_FILE, "r") as f:
        banned = json.load(f)
    if user_id not in banned:
        banned.append(user_id)
        with open(BANNED_FILE, "w") as f:
            json.dump(banned, f)

def is_vip(user_id):
    if user_id in ADMINS:
        return True
    with open(VIP_FILE, "r") as f:
        vips = json.load(f)
    return user_id in vips

def add_vip(user_id):
    with open(VIP_FILE, "r") as f:
        vips = json.load(f)
    if user_id not in vips:
        vips.append(user_id)
        with open(VIP_FILE, "w") as f:
            json.dump(vips, f)

def remove_vip(user_id):
    with open(VIP_FILE, "r") as f:
        vips = json.load(f)
    if user_id in vips:
        vips.remove(user_id)
        with open(VIP_FILE, "w") as f:
            json.dump(vips, f)

def check_subscriptions(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel["username"], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            pass
    return True

def sub_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(f"📢 {ch['name']}ga obuna bo'lish", url=f"https://t.me/{ch['username'].replace('@', '')}"))
    markup.add(types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if is_banned(user_id):
        bot.send_message(user_id, "❌ Siz bot tomonidan bloklangansiz.")
        return

    if user_id not in ADMINS and not check_subscriptions(user_id):
        bot.send_message(
            user_id,
            "⚠️ **Botdan foydalanish uchun quyidagi 4 ta kanalga obuna bo'lishingiz shart!**\n\nObuna bo'lib, keyin '✅ Obunani tekshirish' tugmasini bosing:",
            reply_markup=sub_keyboard(),
            parse_mode="Markdown"
        )
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Asosiy tugmalar (barcha foydalanuvchilar va admin uchun)
    btn1 = types.KeyboardButton("🎲 Tasodifiy")
    btn2 = types.KeyboardButton("🔍 Qidiruv")
    btn3 = types.KeyboardButton("💡 Kino tavsiya qilish")
    btn4 = types.KeyboardButton("👤 Shaxsiy kino qo'shish")
    btn5 = types.KeyboardButton("📤 Admin orqali qo'shish")
    
    if user_id in ADMINS:
        # Admin uchun qo'shimcha maxsus 2 ta tugma
        btn_admin_norm = types.KeyboardButton("🎬 Oddiy video qo'shish")
        btn_admin_vip = types.KeyboardButton("💎 VIP video qo'shish")
        markup.add(btn_admin_norm, btn_admin_vip, btn1, btn2, btn3, btn4, btn5)
    else:
        markup.add(btn1, btn2, btn3, btn4, btn5)
        
    bot.send_message(
        user_id,
        "🎬 Kino olami botiga xush kelibsiz!\nKerakli bo'limni tanlang yoki kino kodini yuboring:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_sub(call):
    user_id = call.from_user.id
    if check_subscriptions(user_id):
        bot.answer_callback_query(call.id, "Rahmat! Obuna tasdiqlandi.")
        bot.delete_message(user_id, call.message.message_id)
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali hamma kanalga obuna bo'lmadingiz!", show_alert=True)

user_states = {}

@bot.message_handler(content_types=['text', 'video', 'animation', 'document', 'photo'])
def handle_all_messages(message):
    user_id = message.from_user.id
    text = message.text if message.text else message.caption
    is_admin = user_id in ADMINS

    if is_banned(user_id):
        return

    if not is_admin and not check_subscriptions(user_id):
        bot.send_message(user_id, "⚠️ Botdan foydalanish uchun avval 4 ta kanalga obuna bo'ling!", reply_markup=sub_keyboard())
        return

    current_state = user_states.get(user_id, {}).get("action")

    # Chek qabul qilish holati
    if current_state == "wait_receipt":
        if message.photo:
            photo_id = message.photo[-1].file_id
            plan_name = user_states[user_id].get("plan_name", "VIP obuna")
            
            add_vip(user_id)
            del user_states[user_id]
            
            admin_markup = types.InlineKeyboardMarkup()
            admin_markup.add(types.InlineKeyboardButton("❌ VIP dan o'chirish (Soxta chek)", callback_data=f"revoke_{user_id}"))
            
            user_name = message.from_user.first_name
            username = f"@{message.from_user.username}" if message.from_user.username else "Yo'q"
            
            forward_caption = (
                f"🧾 **Yangi VIP to'lov cheki keldi!**\n\n"
                f"👤 Foydalanuvchi: {user_name} ({username})\n"
                f"🆔 ID: `{user_id}`\n"
                f"📦 Tanlangan tarif: {plan_name}"
            )
            
            for admin_id in ADMINS:
                try:
                    bot.send_photo(admin_id, photo_id, caption=forward_caption, reply_markup=admin_markup, parse_mode="Markdown")
                except Exception:
                    pass
            
            bot.send_message(user_id, "✅ Chekingiz adminga yuborildi va bot tomonidan **avtomat tarzda sizga VIP obuna berildi!** Kinolarni bemalol ko'rishingiz mumkin.")
        else:
            bot.send_message(user_id, "❌ Iltimos, to'lov chekining **rasmini** yuboring!")
        return

    # Admin: Oddiy video qo'shish
    if is_admin and text == "🎬 Oddiy video qo'shish":
        user_states[user_id] = {"action": "admin_norm_video"}
        bot.send_message(user_id, "🎬 **Oddiy video qo'shish**\n\nBazaga qo'shish uchun kino **videosini** yuboring:")
        return

    if current_state == "admin_norm_video":
        if message.video or message.animation:
            file_id = message.video.file_id if message.video else message.animation.file_id
            user_states[user_id] = {"action": "admin_norm_code", "file_id": file_id}
            bot.send_message(user_id, "🔢 Endi shu oddiy kino uchun **kod** yuboring:")
        else:
            bot.send_message(user_id, "❌ Iltimos, faqat video fayl yuboring!")
        return
        
    elif current_state == "admin_norm_code":
        file_id = user_states[user_id]["file_id"]
        code = text.strip()
        with open(DB_FILE, "r") as f:
            movies = json.load(f)
        movies[code] = file_id
        with open(DB_FILE, "w") as f:
            json.dump(movies, f, indent=4)
        del user_states[user_id]
        bot.send_message(user_id, f"✅ Oddiy kino bazaga muvaffaqiyatli qo'shildi! Kod: `{code}`", parse_mode="Markdown")
        return

    # Admin: VIP video qo'shish
    if is_admin and text == "💎 VIP video qo'shish":
        user_states[user_id] = {"action": "admin_vip_video"}
        bot.send_message(user_id, "💎 **VIP video qo'shish**\n\nVIP bazaga qo'shish uchun kino **videosini** yuboring:")
        return

    if current_state == "admin_vip_video":
        if message.video or message.animation:
            file_id = message.video.file_id if message.video else message.animation.file_id
            user_states[user_id] = {"action": "admin_vip_code", "file_id": file_id}
            bot.send_message(user_id, "🔢 Endi shu VIP kino uchun **kod** yuboring:")
        else:
            bot.send_message(user_id, "❌ Iltimos, faqat video fayl yuboring!")
        return
        
    elif current_state == "admin_vip_code":
        file_id = user_states[user_id]["file_id"]
        code = text.strip()
        with open(VIP_DB_FILE, "r") as f:
            vip_movies = json.load(f)
        vip_movies[code] = file_id
        with open(VIP_DB_FILE, "w") as f:
            json.dump(vip_movies, f, indent=4)
        del user_states[user_id]
        bot.send_message(user_id, f"✅ VIP kino bazaga muvaffaqiyatli qo'shildi! Kod: `{code}`", parse_mode="Markdown")
        return

    if text:
        lower_text = text.lower()
        if any(word in lower_text for word in FORBIDDEN_WORDS):
            ban_user(user_id)
            if user_id in user_states:
                del user_states[user_id]
            bot.send_message(user_id, "❌ Qoidaga zid kontent aniqlandi va siz botdan bloklandingiz!")
            return

    # Oddiy tugmalar jarayoni
    if text == "🎲 Tasodifiy":
        with open(DB_FILE, "r") as f:
            movies = json.load(f)
        if movies:
            random_code = random.choice(list(movies.keys()))
            bot.send_message(user_id, "🎲 **Tasodifiy kino tanlandi:**")
            send_movie(user_id, random_code, movies[random_code], is_vip=False)
        else:
            bot.send_message(user_id, "🎲 Hozircha bazada kinolar yo'q.")
        return
        
    elif text == "🔍 Qidiruv":
        bot.send_message(user_id, "🔍 Kino topish uchun kino **kodini** yuboring:", parse_mode="Markdown")
        return
        
    elif text == "💡 Kino tavsiya qilish":
        user_states[user_id] = {"action": "suggest"}
        bot.send_message(user_id, "💡 Kino nomini yozib qoldiring, adminga yuboramiz:")
        return
        
    elif text == "👤 Shaxsiy kino qo'shish":
        user_states[user_id] = {"action": "personal_upload_video"}
        bot.send_message(user_id, "👤 Shaxsiy kino qo'shish uchun avval kino **videosini** yuboring (qoidaga zid bo'lmagan):")
        return

    elif text == "📤 Admin orqali qo'shish":
        user_states[user_id] = {"action": "admin_review_upload"}
        bot.send_message(user_id, "📤 Adminga yuborish uchun kino **videosini** yuboring:")
        return

    if current_state == "personal_upload_video":
        if message.video or message.animation:
            file_id = message.video.file_id if message.video else message.animation.file_id
            user_states[user_id] = {"action": "personal_upload_code", "file_id": file_id}
            bot.send_message(user_id, "🔢 Endi bu kino uchun **kod** yuboring:")
        else:
            bot.send_message(user_id, "❌ Iltimos, video yuboring!")
        return
        
    elif current_state == "personal_upload_code":
        file_id = user_states[user_id]["file_id"]
        code = text.strip()
        with open(DB_FILE, "r") as f:
            movies = json.load(f)
        movies[code] = file_id
        with open(DB_FILE, "w") as f:
            json.dump(movies, f, indent=4)
        del user_states[user_id]
        bot.send_message(user_id, f"✅ Kino bazaga qo'shildi! Kod: `{code}`", parse_mode="Markdown")
        return

    elif current_state == "admin_review_upload":
        if message.video or message.animation:
            file_id = message.video.file_id if message.video else message.animation.file_id
            user_states[user_id] = {"action": "admin_review_code", "file_id": file_id}
            bot.send_message(user_id, "🔢 Endi kino uchun **kod** yoki nom yuboring:")
        else:
            bot.send_message(user_id, "❌ Iltimos, video yuboring!")
        return

    elif current_state == "admin_review_code":
        file_id = user_states[user_id]["file_id"]
        info_text = text.strip()
        del user_states[user_id]
        
        user_name = message.from_user.first_name
        username = f"@{message.from_user.username}" if message.from_user.username else "Yo'q"
        
        for admin_id in ADMINS:
            try:
                bot.send_video(admin_id, file_id, caption=f"📤 Yangi foydalanuvchi kino yukladi!\n👤 Kimdan: {user_name} ({username})\n🆔 ID: `{user_id}`\n📝 Izoh/Kod: {info_text}", parse_mode="Markdown")
            except Exception:
                pass
        bot.send_message(user_id, "✅ Admin ko'rib chiqib botga joylashga harakat qiladi. Rahmat!")
        return

    elif current_state == "suggest":
        del user_states[user_id]
        user_name = message.from_user.first_name
        username = f"@{message.from_user.username}" if message.from_user.username else "Yo'q"
        forward_text = f"💡 Yangi kino tavsiyasi!\n👤 Kimdan: {user_name} ({username})\n🆔 ID: {user_id}\n\n📝 Tavsiya: {text}"
        for admin_id in ADMINS:
            try:
                bot.send_message(admin_id, forward_text)
            except Exception:
                pass
        bot.send_message(user_id, "✅ Tavsiyangiz adminga yuborildi!")
        return

    # Kod orqali kino qidirish (Oddiy va VIP bazadan)
    if text:
        with open(DB_FILE, "r") as f:
            movies = json.load(f)
        with open(VIP_DB_FILE, "r") as f:
            vip_movies = json.load(f)
            
        if text in movies:
            send_movie(user_id, text, movies[text], is_vip=False)
        elif text in vip_movies:
            if is_vip(user_id):
                send_movie(user_id, text, vip_movies[text], is_vip=True)
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("💎 VIP Obuna bo'lish", callback_data="vip_menu"))
                bot.send_message(
                    user_id, 
                    "🔒 **Bu VIP kino!**\n\nBu faqat VIP obunachilar uchun, sotib oling:", 
                    reply_markup=markup, 
                    parse_mode="Markdown"
                )
        else:
            bot.send_message(user_id, "❌ Bunday kodli kino topilmadi.")

def send_movie(user_id, code, video_id, is_vip=False):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💎 VIP Obuna", callback_data="vip_menu"))
    markup.add(types.InlineKeyboardButton("📢 Reklama uchun", callback_data="reklama"))
    
    tag = "💎 VIP Kino" if is_vip else "🎬 Oddiy Kino"
    caption = f"{tag}\n🎬 Kod: {code}\n✅ Yoqimli tomosha!"
    bot.send_video(user_id, video_id, caption=caption, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id
    
    if call.data == "vip_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        # 3 ta tildagi alohida narxlar va tariflar
        markup.add(
            types.InlineKeyboardButton("🇺🇿 1 Oylik - 15,000 so'm", callback_data="vip_uz_1"),
            types.InlineKeyboardButton("🇺🇿 3 Oylik - 35,000 so'm", callback_data="vip_uz_3"),
            types.InlineKeyboardButton("🇺🇿 6 Oylik - 50,000 so'm", callback_data="vip_uz_6"),
            types.InlineKeyboardButton("🇷🇺 1 Месяц - 300 руб", callback_data="vip_ru_1"),
            types.InlineKeyboardButton("🇷🇺 3 Месяца - 450 руб", callback_data="vip_ru_3"),
            types.InlineKeyboardButton("🇷🇺 6 Месяцев - 600 руб", callback_data="vip_ru_6"),
            types.InlineKeyboardButton("🇬🇧 1 Month - $12", callback_data="vip_en_1"),
            types.InlineKeyboardButton("🇬🇧 3 Months - $20", callback_data="vip_en_3"),
            types.InlineKeyboardButton("🇬🇧 6 Months - $30", callback_data="vip_en_6")
        )
        bot.edit_message_text(
            "💎 **VIP OBUNA TURLARI / ТАРИФЫ VIP / VIP PLANS**\n\nKerakli tarifni tanlang:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("vip_"):
        plans_info = {
            "vip_uz_1": "1 Oylik (15,000 so'm)",
            "vip_uz_3": "3 Oylik (35,000 so'm)",
            "vip_uz_6": "6 Oylik (50,000 so'm)",
            "vip_ru_1": "1 Месяц (300 руб)",
            "vip_ru_3": "3 Месяца (450 руб)",
            "vip_ru_6": "6 Месяцев (600 руб)",
            "vip_en_1": "1 Month ($12)",
            "vip_en_3": "3 Months ($20)",
            "vip_en_6": "6 Months ($30)"
        }
        selected_plan = plans_info.get(call.data, "VIP Obuna")
        user_states[user_id] = {"action": "wait_receipt", "plan_name": selected_plan}
        
        text = (
            f"💳 **To'lov qilish uchun ma'lumotlar:**\n\n"
            f"👤 **Karta egasi:** `{CARD_HOLDER}`\n"
            f"🔢 **Karta raqami:** `{CARD_NUMBER}`\n\n"
            f"📋 **Shartlar:**\n"
            f"1. Tanlangan tarif uchun pulni kartaga o'tkazing.\n"
            f"2. To'lov chekining rasmini botga yuboring.\n"
            f"3. Chek tashlangach, bot uni ko'rib chiqib avtomat tarzda sizga VIP obuna beradi va kinolarni tashlab beradi.\n\n"
            f"📦 **Tanlangan tarif:** {selected_plan}"
        )
        bot.send_message(user_id, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    elif call.data == "reklama":
        # Reklama tugmasi bosilganda to'g'ridan-to'g'ri admin (sizning) lichkangizga o'tadi
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 Adminga yozish", url=f"https://t.me/{ADMIN_USERNAME}"))
        bot.send_message(user_id, "📢 Reklama bo'yicha bog'lanish uchun quyidagi tugmani bosing:", reply_markup=markup)
        bot.answer_callback_query(call.id)

    elif call.data.startswith("revoke_"):
        target_user_id = int(call.data.split("_")[1])
        remove_vip(target_user_id)
        bot.answer_callback_query(call.id, "Foydalanuvchi VIP dan olib tashlandi!", show_alert=True)
        try:
            bot.send_message(target_user_id, "❌ Chekingiz soxta yoki yaroqsiz deb topildi, shu sababli VIP obunangiz bekor qilindi.")
        except Exception:
            pass
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + "\n\n❌ **HOLAT: VIP obunadan o'chirildi (Soxta chek)**",
                parse_mode="Markdown"
            )
        except Exception:
            pass

print("Bot ishga tushdi...")
bot.infinity_polling()
  
