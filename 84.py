import sqlite3
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# ================= تنظیمات اولیه =================
TOKEN = "5721097506:AAF1bvuRuvMUNvJ7w5ReePpCj8IAumVql0s"  # توکن ربات خود را اینجا قرار دهید
ADMIN_IDS = [805314316]  # آیدی عددی تلگرام خودتان را اینجا قرار دهید
CONSULTANT_PHONE = "09144807280 , 09020226105"  # شماره تماس جهت نمایش به مشتری

PROP_TYPES = [
    ["آپارتمان", "ویلایی"],
    ["دو طبقه", "سه طبقه", "چهار طبقه"],
    ["نیمه‌کاره", "کلنگی"],
    ["مغازه / تجاری", "مسکونی تجاری"],
    ["زمین مسکونی", "زمین تجاری", "زمین مزروعی"],
    ["باغ", "سوله / انبار", "کارگاه / کارخانه"],
    ["🔙 مرحله قبل", "🏠 منوی اصلی"]
]

FILTERABLE_TYPES = [
    "آپارتمان", "ویلایی",
    "دو طبقه", "سه طبقه", "چهار طبقه",
    "نیمه‌کاره", "کلنگی"
]

HOUSE_TYPES = ["ویلایی", "دو طبقه", "سه طبقه", "چهار طبقه", "نیمه‌کاره", "کلنگی"]

BONAB_REGIONS = [
    ["خیابان بهشتی", "خیابان باهنر", "خیابان امام"],
    ["خیابان مطهری", "خیابان رجایی", "خیابان فرهنگ"],
    ["خیابان نویدی", "خیابان آب", "خیابان هوشمندی"],
    ["کوی شهرداری", "کوی کارمندان", "کوی ایثارگران"],
    ["کوی بابک", "کوی بنفشه", "کوی سعدی"],
    ["بلوار لاله", "بلوار سهند", "برق لاله"],
    ["میدان معلم", "میدان بسیج", "شهرک امام"],
    ["گزاواشت", "خرمن کوچه", "شهریار"],
    ["تبریز کوچه سی", "چمران", "بعثت"],
    ["دیزج", "آغداش", "جانبازان"],
    ["آزادگان", "کاملو", "جارچیلار"],
    ["باقرآباد", "امیرکبیر", "مهارت"],
    ["خانیم باغی", "آغاجری", "مهرابادآرخی"],
    ["زرگران", "طالقانی", "کارگر شمالی و جنوبی"],
    ["جاده مراغه", "جاده تبریز", "جاده ملکان"],
    ["لالالی", "میانالار", "صوفی چای"],
    ["رسالت", "اکبر آباد", "محله بهشتی"],
    ["ساری داغ", "سایر مناطق"]
]

# وضعیت‌های مکالمه
(
    ADD_DEAL, ADD_TYPE, ADD_EXCHANGE, ADD_PROGRESS, ADD_DELIVERY, ADD_REGION, ADD_REG_CUSTOM,
    APT_AREA, APT_FLOOR, APT_ROOMS, APT_UNITS, APT_PARKING, APT_WAREHOUSE, APT_ELEVATOR, APT_YEAR, APT_EQUIP,
    HSE_LAND_AREA, HSE_BUILD_AREA, HSE_ROOMS, HSE_STRUCTURE, HSE_ALLEY, HSE_FRONTAGE, HSE_ENTRY, HSE_DEED, HSE_EQUIP,
    SHP_AREA, SHP_FRONTAGE, SHP_BALCONY, SHP_DEED,
    LND_AREA, LND_FRONTAGE, LND_ALLEY, LND_DEED, LND_WATER, LND_ELECTRICITY, LND_GAS,
    GRD_MAN, GRD_WALL, GRD_HOUSE, GRD_WATER, GRD_ELECTRICITY, GRD_GAS,
    WRK_AREA, WRK_FACILITIES,
    COM_ADDRESS, COM_PRICE, COM_RENT, COM_DESC, COM_OWNER_NAME, COM_PHONE, COM_MEDIA,
    SRCH_DEAL, SRCH_TYPE, SRCH_HUB, SRCH_PISH_HUB, SRCH_REGION, SRCH_ROOMS, SRCH_PRICE, SRCH_PROGRESS, SRCH_DELIVERY,
    REQ_TEXT, CHAT_TEXT
) = range(62)


# ================= دیتابیس =================
def init_db():
    conn = sqlite3.connect("amlak_bonab_v9.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    deal_type TEXT,
                    prop_type TEXT,
                    is_exchange INTEGER DEFAULT 0,
                    progress TEXT,
                    delivery TEXT,
                    region TEXT,
                    address TEXT,
                    rooms INTEGER DEFAULT 0,
                    area TEXT,
                    price INTEGER,
                    rent_price INTEGER DEFAULT 0,
                    specs_text TEXT,
                    description TEXT,
                    owner_name TEXT,
                    owner_phone TEXT,
                    media_items TEXT,
                    is_approved INTEGER DEFAULT 1
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS favorites (
                    user_id INTEGER,
                    prop_id INTEGER,
                    UNIQUE(user_id, prop_id)
                )''')
    conn.commit()
    conn.close()


def parse_persian_price(text):
    if not text:
        return None
    persian_nums = {'۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
                    ',': '', '،': '', ' ': ''}
    clean_text = text.strip()
    for p, e in persian_nums.items():
        clean_text = clean_text.replace(p, e)
    try:
        if 'میلیارد' in text or 'ملیارد' in text:
            num_str = ''.join([c for c in clean_text if c.isdigit() or c == '.'])
            if num_str:
                return int(float(num_str) * 1000000000)
        elif 'میلیون' in text or 'مليون' in text:
            num_str = ''.join([c for c in clean_text if c.isdigit() or c == '.'])
            if num_str:
                return int(float(num_str) * 1000000)
        digits_only = ''.join([c for c in clean_text if c.isdigit()])
        if digits_only:
            return int(digits_only)
    except Exception:
        pass
    return None


def get_regions_kb(is_search=False):
    kb = [row[:] for row in BONAB_REGIONS]
    if is_search:
        kb.append(["🌐 همه مناطق بناب"])
    kb.append(["🔙 مرحله قبل", "🏠 منوی اصلی"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def main_menu_keyboard(user_id):
    kb = [
        ["🔍 جستجوی ملک", "🖋 سپردن ملک"],
        ["👤 ثبت تقاضا", "💚 علاقه‌مندی‌ها"],
        ["📞 ارتباط با ما", "💬 گفتگو با مشاور"]
    ]
    if user_id in ADMIN_IDS:
        kb.append(["🔐 پنل مدیریت (تایید / حذف ملک)"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🏡 **شما به منوی اصلی سامانه جامع املاک بناب هدایت شدید.**\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_menu_keyboard(user_id),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ================= ۱. سپردن ملک =================
async def add_prop_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['specs'] = []
    context.user_data['media'] = []
    kb = [
        ["فروش", "پیش‌فروش"],
        ["رهن و اجاره"],
        ["🏠 منوی اصلی"]
    ]
    await update.message.reply_text("📌 **نوع معامله** را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return ADD_DEAL


async def add_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['deal_type'] = text

    if text == "پیش‌فروش":
        context.user_data['prop_type'] = "آپارتمان"
        context.user_data['is_exchange'] = 0
        kb = [
            ["فونداسیون / شروع کار", "اسکلت و سقف"],
            ["سفت‌کاری و تیغه‌چینی", "نازک‌کاری / رو به اتمام"],
            ["🔙 مرحله قبل", "🏠 منوی اصلی"]
        ]
        await update.message.reply_text("🏗 **میزان پیشرفت بنا** را انتخاب کنید:",
                                        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                                        parse_mode="Markdown")
        return ADD_PROGRESS
    else:
        await update.message.reply_text("🏠 **نوع ملک** را انتخاب نمایید:",
                                        reply_markup=ReplyKeyboardMarkup(PROP_TYPES, resize_keyboard=True),
                                        parse_mode="Markdown")
        return ADD_TYPE


async def add_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل": return await add_prop_start(update, context)
    context.user_data['prop_type'] = text

    if context.user_data['deal_type'] == "فروش":
        kb = [
            ["بله، قابلیت معاوضه دارد", "خیر، فقط نقدی"],
            ["🔙 مرحله قبل", "🏠 منوی اصلی"]
        ]
        await update.message.reply_text("🔄 آیا این ملک **قابلیت معاوضه** دارد؟",
                                        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                                        parse_mode="Markdown")
        return ADD_EXCHANGE
    else:
        context.user_data['is_exchange'] = 0
        await update.message.reply_text("📍 **منطقه ملک** را انتخاب کنید:", reply_markup=get_regions_kb(is_search=False),
                                        parse_mode="Markdown")
        return ADD_REGION


async def add_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل":
        await update.message.reply_text("🏠 **نوع ملک** را انتخاب نمایید:",
                                        reply_markup=ReplyKeyboardMarkup(PROP_TYPES, resize_keyboard=True),
                                        parse_mode="Markdown")
        return ADD_TYPE
    context.user_data['is_exchange'] = 1 if "بله" in text else 0
    await update.message.reply_text("📍 **منطقه ملک** را از لیست زیر انتخاب کنید:",
                                    reply_markup=get_regions_kb(is_search=False), parse_mode="Markdown")
    return ADD_REGION


async def add_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل": return await add_prop_start(update, context)
    context.user_data['progress'] = text
    kb = [
        ["تا ۶ ماه آینده", "۶ تا ۱۲ ماه آینده"],
        ["بیشتر از ۱ سال"],
        ["🔙 مرحله قبل", "🏠 منوی اصلی"]
    ]
    await update.message.reply_text("📅 **زمان تحویل** واحد را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return ADD_DELIVERY


async def add_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل": return await add_deal(update, context)
    context.user_data['delivery'] = text
    await update.message.reply_text("📍 **منطقه ملک** را از لیست زیر انتخاب کنید:",
                                    reply_markup=get_regions_kb(is_search=False), parse_mode="Markdown")
    return ADD_REGION


async def add_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل": return await add_prop_start(update, context)

    if text == "سایر مناطق":
        kb = [["🏠 منوی اصلی"]]
        await update.message.reply_text("📍 نام منطقه یا محله مورد نظر را تایپ کنید:",
                                        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return ADD_REG_CUSTOM

    context.user_data['region'] = text
    return await route_to_specific_form(update, context)


async def add_reg_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['region'] = text.strip()
    return await route_to_specific_form(update, context)


async def route_to_specific_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ptype = context.user_data['prop_type']
    kb = [["🏠 منوی اصلی"]]
    rm = ReplyKeyboardMarkup(kb, resize_keyboard=True)

    if ptype in ["آپارتمان", "سوئیت"]:
        await update.message.reply_text("📐 **متراژ مفید آپارتمان** را به متر وارد کنید (مثلاً 115):", reply_markup=rm,
                                        parse_mode="Markdown")
        return APT_AREA
    elif ptype in HOUSE_TYPES:
        await update.message.reply_text("📐 **متراژ کل زمین** را به متر وارد کنید (مثلاً 200):", reply_markup=rm,
                                        parse_mode="Markdown")
        return HSE_LAND_AREA
    elif ptype in ["مغازه / تجاری", "مسکونی تجاری"]:
        await update.message.reply_text("📐 **متراژ کل همکف مغازه** را به متر وارد کنید (مثلاً 45):", reply_markup=rm,
                                        parse_mode="Markdown")
        return SHP_AREA
    elif ptype in ["زمین مسکونی", "زمین تجاری", "زمین مزروعی"]:
        await update.message.reply_text(
            "📐 **متراژ زمین** را وارد کنید (می‌توانید متر یا مَن بنویسید، مثلاً 250 متر یا 10 من):", reply_markup=rm,
            parse_mode="Markdown")
        return LND_AREA
    elif ptype == "باغ":
        await update.message.reply_text(
            "🌳 **متراژ باغ** را وارد کنید (می‌توانید متر یا مَن بنویسید، مثلاً 1000 متر یا 15 من):", reply_markup=rm,
            parse_mode="Markdown")
        return GRD_MAN
    else:
        await update.message.reply_text("📐 **متراژ کل سوله / کارگاه** را به متر وارد کنید:", reply_markup=rm,
                                        parse_mode="Markdown")
        return WRK_AREA


# مسیر آپارتمان
async def apt_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['area'] = f"{update.message.text.strip()} متر"
    kb = [["همکف", "طبقه 1", "طبقه 2"], ["طبقه 3", "طبقه 4", "طبقه 5 به بالا"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🏢 **طبقه** واحد را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return APT_FLOOR


async def apt_floor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"طبقه: {update.message.text}")
    kb = [["بدون خواب (0)", "1 خواب", "2 خواب"], ["3 خواب", "4 خواب و بیشتر"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🛏 **تعداد خواب** را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return APT_ROOMS


async def apt_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    rooms_map = {"بدون خواب (0)": 0, "1 خواب": 1, "2 خواب": 2, "3 خواب": 3, "4 خواب و بیشتر": 4}
    context.user_data['rooms'] = rooms_map.get(update.message.text, 0)
    kb = [["تک واحدی", "دو واحدی"], ["سه واحدی", "چهار واحدی و بیشتر"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🚪 **تعداد واحد در هر طبقه** را مشخص کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return APT_UNITS


async def apt_units(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"تعداد واحد در طبقه: {update.message.text}")
    kb = [["دارد", "ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🚗 آیا واحد دارای **پارکینگ** است؟",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return APT_PARKING


async def apt_parking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"پارکینگ: {update.message.text}")
    kb = [["دارد", "ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("📦 آیا واحد دارای **انباری** است؟",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return APT_WAREHOUSE


async def apt_warehouse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"انباری: {update.message.text}")
    kb = [["دارد", "ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🛗 آیا ساختمان دارای **آسانسور** است؟",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return APT_ELEVATOR


async def apt_elevator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"آسانسور: {update.message.text}")
    kb = [["نوساز / کلید نخورده"], ["1400 تا 1404", "1395 تا 1399"], ["قبل از 1395"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("📅 **سال ساخت** بنا را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return APT_YEAR


async def apt_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"سال ساخت: {update.message.text}")
    kb = [["فول نصبیات (کابینت، پکیج، کمد و...)"], ["نصبیات معمولی", "خام / بدون نصبیات"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🛠 **نصبیات موجود** در واحد را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return APT_EQUIP


async def apt_equip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"نصبیات: {update.message.text}")
    return await ask_common_address(update)


# مسیر ویلایی و طبقات
async def hse_land_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['land_area'] = update.message.text.strip()
    await update.message.reply_text("🏗 **متراژ زیربنا (ساخت)** را به متر وارد کنید:",
                                    reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True),
                                    parse_mode="Markdown")
    return HSE_BUILD_AREA


async def hse_build_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    build_a = update.message.text.strip()
    context.user_data['area'] = f"زمین {context.user_data['land_area']}م / ساخت {build_a}م"
    kb = [["1 خواب", "2 خواب", "3 خواب"], ["هر طبقه 2 خواب", "هر طبقه 3 خواب"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🛏 **تعداد خواب هر طبقه** را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return HSE_ROOMS


async def hse_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    txt = update.message.text
    context.user_data['specs'].append(f"خواب: {txt}")
    for num in [1, 2, 3, 4]:
        if str(num) in txt:
            context.user_data['rooms'] = num
            break
    kb = [["بتنی", "اسکلت فلزی (آهنی)"], ["آجری / شناژدار", "چوبی / قدیمی"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🧱 **نوع ساخت (اسکلت بنا)** را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return HSE_STRUCTURE


async def hse_structure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"نوع ساخت: {update.message.text}")
    kb = [["6 متری", "8 متری", "10 متری"], ["12 متری و بالاتر", "بن‌بست"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🛣 **متراژ (عرض) کوچه** را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return HSE_ALLEY


async def hse_alley(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"عرض کوچه: {update.message.text}")
    await update.message.reply_text("📏 **متراژ بَر به کوچه** را وارد کنید (مثلاً 10 متر):",
                                    reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True),
                                    parse_mode="Markdown")
    return HSE_FRONTAGE


async def hse_frontage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"بر به کوچه: {update.message.text}")
    kb = [["ورود به حیاط", "ورود به ساختمان"], ["دو کله / نبش"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🚪 جهت **ورود به ملک** را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return HSE_ENTRY


async def hse_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"جهت ورود: {update.message.text}")
    kb = [["دارد", "ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🚗 آیا ملک دارای **پارکینگ** است؟",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return HSE_DEED


async def hse_deed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"پارکینگ: {update.message.text}")
    kb = [["دارد", "ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🛗 آیا ساختمان دارای **آسانسور** است؟",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return HSE_EQUIP


async def hse_equip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"آسانسور: {update.message.text}")
    kb = [["سند ششدانگ تک‌برگ", "سند ششدانگ منگوله‌دار"], ["قولنامه‌ای معتبر", "اوقافی / سایر"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("📜 **نوع سند** ملک را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return HSE_ALLEY


# مسیر مغازه
async def shp_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['area'] = f"{update.message.text.strip()} متر"
    await update.message.reply_text("📏 **متراژ دهنه مغازه** را وارد کنید:",
                                    reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True),
                                    parse_mode="Markdown")
    return SHP_FRONTAGE


async def shp_frontage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"دهنه: {update.message.text}")
    kb = [["بالکن ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text(
        "🪜 اگر **بالکن** دارد متراژ آن را بنویسید، در غیر این صورت دکمه «بالکن ندارد» را بزنید:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return SHP_BALCONY


async def shp_balcony(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"بالکن: {update.message.text}")
    kb = [["ملکیت (ششدانگ)", "سرقفلی"], ["قولنامه‌ای"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("📜 **نوع سند مغازه** را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return SHP_DEED


async def shp_deed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"سند: {update.message.text}")
    return await ask_common_address(update)


# مسیر زمین (پذیرش متراژ متنی یا مَن محلی)
async def lnd_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['area'] = update.message.text.strip()
    await update.message.reply_text("📏 **بَر زمین** را وارد کنید (مثلاً 10 متر):",
                                    reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True),
                                    parse_mode="Markdown")
    return LND_FRONTAGE


async def lnd_frontage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"بر زمین: {update.message.text}")
    await update.message.reply_text("🛣 **متراژ (عرض) کوچه یا خیابان** را وارد کنید:",
                                    reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True),
                                    parse_mode="Markdown")
    return LND_ALLEY


async def lnd_alley(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"عرض معبر: {update.message.text}")
    kb = [["سند ششدانگ", "قولنامه‌ای معتبر"], ["نسق / مشاع"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("📜 **نوع سند زمین** را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return LND_DEED


async def lnd_deed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"سند: {update.message.text}")
    kb = [["دارد", "ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("💧 آیا زمین دارای **آب** است؟",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return LND_WATER


async def lnd_water(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"آب: {update.message.text}")
    kb = [["دارد", "ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("⚡ آیا زمین دارای **برق** است؟",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return LND_ELECTRICITY


async def lnd_electricity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"برق: {update.message.text}")
    kb = [["دارد", "ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🔥 آیا زمین دارای **گاز** است؟",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return LND_GAS


async def lnd_gas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"گاز: {update.message.text}")
    return await ask_common_address(update)


# مسیر باغ (پذیرش متراژ متنی یا مَن محلی)
async def grd_man(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['area'] = update.message.text.strip()
    kb = [["دیوارکشی کامل دارد", "فنس‌کشی دارد", "بدون دیوار"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🧱 وضعیت **دیوارکشی** باغ را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return GRD_WALL


async def grd_wall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"دیوارکشی: {update.message.text}")
    kb = [["خانه باغ شیک و تکمیل دارد", "اتاق نگهبانی دارد"], ["خانه باغ ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🏡 وضعیت **خانه باغ** را مشخص کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return GRD_HOUSE


async def grd_house(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"خانه باغ: {update.message.text}")
    kb = [["دارد", "ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("💧 آیا باغ دارای **حق آب / موتور آب** است؟",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return GRD_WATER


async def grd_water(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"حق آب: {update.message.text}")
    kb = [["دارد", "ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("⚡ آیا باغ دارای **برق** است؟",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return GRD_ELECTRICITY


async def grd_electricity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"برق: {update.message.text}")
    kb = [["دارد", "ندارد"], ["🏠 منوی اصلی"]]
    await update.message.reply_text("🔥 آیا باغ دارای **گاز** است؟",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return GRD_GAS


async def grd_gas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"گاز: {update.message.text}")
    return await ask_common_address(update)


# مسیر سوله و کارگاه
async def wrk_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['area'] = f"{update.message.text.strip()} متر"
    await update.message.reply_text("⚙️ **امکانات و مشخصات** (برق سه‌فاز، ارتفاع سقف، دفتر اداری و...) را بنویسید:",
                                    reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True),
                                    parse_mode="Markdown")
    return WRK_FACILITIES


async def wrk_facilities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['specs'].append(f"امکانات: {update.message.text}")
    return await ask_common_address(update)


# مراحل مشترک پایانی
async def ask_common_address(update: Update):
    await update.message.reply_text(
        "📍 **آدرس دقیق‌تر ملک** (نام کوچه یا پلاک) را بنویسید:",
        reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True),
        parse_mode="Markdown"
    )
    return COM_ADDRESS


async def com_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['address'] = update.message.text.strip()

    if context.user_data['deal_type'] == "رهن و اجاره":
        await update.message.reply_text("💰 **مبلغ رهن** را وارد کنید (مثلاً: ۳۰۰ میلیون یا 300000000):",
                                        reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True),
                                        parse_mode="Markdown")
        return COM_PRICE
    else:
        await update.message.reply_text("💰 **قیمت کل پیشنهادی** را وارد کنید (مثلاً: ۱۲ میلیارد یا 12000000000):",
                                        reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True),
                                        parse_mode="Markdown")
        return COM_PRICE


async def com_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    txt_input = update.message.text.strip()
    val = parse_persian_price(txt_input)

    if val is not None and val > 0:
        context.user_data['price'] = val

        if context.user_data['deal_type'] == "رهن و اجاره":
            await update.message.reply_text("💰 **مبلغ اجاره ماهیانه** را وارد کنید (اگر اجاره ندارد 0 بنویسید):",
                                            reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True),
                                            parse_mode="Markdown")
            return COM_RENT
        else:
            context.user_data['rent_price'] = 0
            await update.message.reply_text(
                "📝 **توضیحات اضافی ملک** (مثلاً شرایط پرداخت، تخفیف، ویژگی‌های خاص یا اگر توضیحی ندارید کلمه «ندارد» را بفرستید):",
                reply_markup=ReplyKeyboardMarkup([["ندارد"], ["🏠 منوی اصلی"]], resize_keyboard=True),
                parse_mode="Markdown")
            return COM_DESC
    else:
        await update.message.reply_text(
            "❌ مبلغ وارد شده نامعتبر است. لطفاً مبلغ را به صورت عددی یا به صورت (مثلاً 12 میلیارد یا 300 میلیون) بنویسید:")
        return COM_PRICE


async def com_rent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    txt_input = update.message.text.strip()
    val = parse_persian_price(txt_input)

    if val is not None:
        context.user_data['rent_price'] = val
        await update.message.reply_text(
            "📝 **توضیحات اضافی ملک** (مثلاً شرایط پرداخت، تخفیف یا اگر توضیحی ندارید «ندارد» را بزنید):",
            reply_markup=ReplyKeyboardMarkup([["ندارد"], ["🏠 منوی اصلی"]], resize_keyboard=True), parse_mode="Markdown")
        return COM_DESC
    else:
        await update.message.reply_text("❌ مبلغ اجاره نامعتبر است. لطفاً عدد یا مقدار را صحیح وارد کنید:")
        return COM_RENT


async def com_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    desc_text = update.message.text.strip()
    context.user_data['description'] = "" if desc_text == "ندارد" else desc_text

    await update.message.reply_text(
        "👤 **نام و نام خانوادگی مالک** را وارد کنید (این اطلاعات فقط برای شما نمایش داده می‌شود):",
        reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True), parse_mode="Markdown")
    return COM_OWNER_NAME


async def com_owner_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['owner_name'] = update.message.text.strip()
    await update.message.reply_text("📱 **شماره تماس مالک** را جهت هماهنگی وارد کنید:",
                                    reply_markup=ReplyKeyboardMarkup([["🏠 منوی اصلی"]], resize_keyboard=True),
                                    parse_mode="Markdown")
    return COM_PHONE


async def com_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['owner_phone'] = update.message.text.strip()
    kb = [["✅ اتمام و ثبت نهایی ملک"], ["🏠 منوی اصلی"]]
    await update.message.reply_text(
        "📸🎥 **عکس‌ها یا فیلم‌های ملک** را ارسال کنید (می‌توانید چند عکس و ویدیو را پشت سر هم بفرستید).\n\n"
        "وقتی تمام شد دکمه **«✅ اتمام و ثبت نهایی ملک»** را بزنید:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return COM_MEDIA


async def com_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🏠 منوی اصلی": return await start(update, context)

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        context.user_data['media'].append(f"photo:{file_id}")
        count = len(context.user_data['media'])
        await update.message.reply_text(
            f"🖼 فایل شماره **{count}** (عکس) دریافت شد. فایل بعدی را بفرستید یا دکمه ثبت نهایی را بزنید.",
            parse_mode="Markdown")
        return COM_MEDIA

    if update.message.video:
        file_id = update.message.video.file_id
        context.user_data['media'].append(f"video:{file_id}")
        count = len(context.user_data['media'])
        await update.message.reply_text(
            f"🎥 فایل شماره **{count}** (فیلم) دریافت شد. فایل بعدی را بفرستید یا دکمه ثبت نهایی را بزنید.",
            parse_mode="Markdown")
        return COM_MEDIA

    if update.message.text == "✅ اتمام و ثبت نهایی ملک":
        user_id = update.effective_user.id
        is_admin = 1 if user_id in ADMIN_IDS else 0
        data = context.user_data
        specs_str = " | ".join(data['specs'])
        media_str = ",".join(data['media'])
        desc_str = data.get('description', '')

        conn = sqlite3.connect("amlak_bonab_v9.db")
        c = conn.cursor()
        c.execute("SELECT MAX(id) FROM properties")
        last_id = c.fetchone()[0] or 100
        prop_code = str(last_id + 1)

        c.execute('''INSERT INTO properties (code, deal_type, prop_type, is_exchange, progress, delivery, region, address, rooms, area, price, rent_price, specs_text, description, owner_name, owner_phone, media_items, is_approved)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (prop_code, data['deal_type'], data['prop_type'], data.get('is_exchange', 0),
                   data.get('progress'), data.get('delivery'), data['region'], data['address'],
                   data.get('rooms', 0), data.get('area', '-'), data['price'], data.get('rent_price', 0),
                   specs_str, desc_str, data['owner_name'], data['owner_phone'], media_str, is_admin))
        new_id = c.lastrowid
        conn.commit()
        conn.close()

        if is_admin:
            await update.message.reply_text(f"✅ **ملک با کد {prop_code} ثبت و منتشر شد!**",
                                            reply_markup=main_menu_keyboard(user_id), parse_mode="Markdown")
        else:
            await update.message.reply_text(f"✅ **ملک شما با کد {prop_code} ثبت شد و پس از تایید منتشر می‌گردد.**",
                                            reply_markup=main_menu_keyboard(user_id), parse_mode="Markdown")
            for admin_id in ADMIN_IDS:
                if data['media']:
                    await send_media_album(context.bot, admin_id, data['media'])
                inline_kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ تایید و انتشار", callback_data=f"approve_{new_id}"),
                    InlineKeyboardButton("❌ رد و حذف", callback_data=f"reject_{new_id}")
                ]])
                admin_msg = (
                    f"🔔 **سپرده ملک جدید از کاربر!**\n"
                    f"🔖 کد: {prop_code} | نوع معامله: {data['deal_type']} ({data['prop_type']})\n"
                    f"📍 منطقه: {data['region']} ({data['address']})\n"
                    f"📐 متراژ: {data.get('area', '-')}\n"
                    f"📋 {specs_str}\n"
                    f"💬 توضیحات: {desc_str or 'ندارد'}\n"
                    f"💰 قیمت/رهن: {data['price']:,} تومان | اجاره: {data.get('rent_price', 0):,} تومان\n"
                    f"👤 نام مالک: {data['owner_name']}\n"
                    f"📞 تلفن مالک: `{data['owner_phone']}`"
                )
                await context.bot.send_message(chat_id=admin_id, text=admin_msg, reply_markup=inline_kb,
                                               parse_mode="Markdown")

        return ConversationHandler.END

    return COM_MEDIA


async def send_media_album(bot_or_msg, chat_id_or_none, media_list, caption=None, reply_markup=None):
    items = [m for m in media_list if ":" in m][:10]
    if not items:
        return False

    if len(items) == 1:
        m_type, m_id = items[0].split(":", 1)
        if m_type == "photo":
            if chat_id_or_none:
                await bot_or_msg.send_photo(chat_id=chat_id_or_none, photo=m_id, caption=caption,
                                            reply_markup=reply_markup, parse_mode="Markdown")
            else:
                await bot_or_msg.reply_photo(photo=m_id, caption=caption, reply_markup=reply_markup,
                                             parse_mode="Markdown")
        elif m_type == "video":
            if chat_id_or_none:
                await bot_or_msg.send_video(chat_id=chat_id_or_none, video=m_id, caption=caption,
                                            reply_markup=reply_markup, parse_mode="Markdown")
            else:
                await bot_or_msg.reply_video(video=m_id, caption=caption, reply_markup=reply_markup,
                                             parse_mode="Markdown")
        return True
    else:
        media_group = []
        for item in items:
            m_type, m_id = item.split(":", 1)
            if m_type == "photo":
                media_group.append(InputMediaPhoto(media=m_id))
            elif m_type == "video":
                media_group.append(InputMediaVideo(media=m_id))
        if chat_id_or_none:
            await bot_or_msg.send_media_group(chat_id=chat_id_or_none, media=media_group)
        else:
            await bot_or_msg.reply_media_group(media=media_group)
        return False


# ================= ۲. جستجوی هوشمند =================
async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    kb = [
        ["فروش", "پیش‌فروش"],
        ["رهن و اجاره"],
        ["🏠 منوی اصلی"]
    ]
    await update.message.reply_text("🔍 **بخش مورد نظر** را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return SRCH_DEAL


async def srch_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    context.user_data['s_deal'] = text

    if text == "رهن و اجاره":
        conn = sqlite3.connect("amlak_bonab_v9.db")
        c = conn.cursor()
        c.execute("SELECT * FROM properties WHERE is_approved = 1 AND deal_type = 'رهن و اجاره' ORDER BY id DESC")
        results = c.fetchall()
        conn.close()

        user_id = update.effective_user.id
        if not results:
            await update.message.reply_text("ℹ️ در حال حاضر موردی برای **رهن و اجاره** ثبت نشده است.",
                                            reply_markup=main_menu_keyboard(user_id), parse_mode="Markdown")
            return ConversationHandler.END

        await update.message.reply_text(f"✅ لیست تمامی فایل‌های **رهن و اجاره** ({len(results)} مورد):",
                                        reply_markup=main_menu_keyboard(user_id), parse_mode="Markdown")
        for row in results:
            await send_property_card(update.message, row)
        return ConversationHandler.END

    elif text == "پیش‌فروش":
        context.user_data['s_type'] = "آپارتمان"
        return await show_pishforoush_hub(update, context)

    elif text == "فروش":
        await update.message.reply_text("🏠 **نوع ملک** مورد نظر را انتخاب کنید:",
                                        reply_markup=ReplyKeyboardMarkup(PROP_TYPES, resize_keyboard=True),
                                        parse_mode="Markdown")
        return SRCH_TYPE

    return SRCH_DEAL


async def show_pishforoush_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        ["📋 نمایش همه پیش‌فروش‌ها"],
        ["📍 فیلتر بر اساس منطقه", "🛏 فیلتر بر اساس تعداد خواب"],
        ["🏗 میزان پیشرفت بنا", "📅 زمان تحویل"],
        ["💰 فیلتر بر اساس قیمت"],
        ["🔙 مرحله قبل", "🏠 منوی اصلی"]
    ]
    await update.message.reply_text("🏢 **بخش پیش‌فروش آپارتمان**\n\nنحوه فیلتر را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return SRCH_PISH_HUB


async def srch_pish_hub_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل": return await search_start(update, context)

    if text == "📋 نمایش همه پیش‌فروش‌ها":
        return await run_search_query(update, context)
    elif text == "📍 فیلتر بر اساس منطقه":
        await update.message.reply_text("📍 **منطقه** را انتخاب کنید:", reply_markup=get_regions_kb(is_search=True),
                                        parse_mode="Markdown")
        return SRCH_REGION
    elif text == "🛏 فیلتر بر اساس تعداد خواب":
        kb = [["1 خواب", "2 خواب", "3 خواب"], ["4 خواب و بیشتر"], ["🔙 مرحله قبل", "🏠 منوی اصلی"]]
        await update.message.reply_text("🛏 **تعداد خواب** را انتخاب کنید:",
                                        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                                        parse_mode="Markdown")
        return SRCH_ROOMS
    elif text == "💰 فیلتر بر اساس قیمت":
        kb = [
            ["تا ۵ میلیارد", "۵ تا ۱۰ میلیارد"],
            ["۱۰ تا ۱۵ میلیارد", "۱۵ تا ۲۰ میلیارد"],
            ["۲۰ تا ۲۵ میلیارد", "۲۵ تا ۳۰ میلیارد"],
            ["۳۰ میلیارد به بالا"],
            ["🔙 مرحله قبل", "🏠 منوی اصلی"]
        ]
        await update.message.reply_text("💰 **بازه بودجه** را انتخاب کنید:",
                                        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                                        parse_mode="Markdown")
        return SRCH_PRICE
    elif text == "🏗 میزان پیشرفت بنا":
        kb = [["فونداسیون / شروع کار", "اسکلت و سقف"], ["سفت‌کاری و تیغه‌چینی", "نازک‌کاری / رو به اتمام"],
              ["🔙 مرحله قبل", "🏠 منوی اصلی"]]
        await update.message.reply_text("🏗 **مرحله پیشرفت ساخت** را انتخاب کنید:",
                                        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                                        parse_mode="Markdown")
        return SRCH_PROGRESS
    elif text == "📅 زمان تحویل":
        kb = [["تا ۶ ماه آینده", "۶ تا ۱۲ ماه آینده"], ["بیشتر از ۱ سال"], ["🔙 مرحله قبل", "🏠 منوی اصلی"]]
        await update.message.reply_text("📅 **زمان تحویل** را انتخاب کنید:",
                                        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                                        parse_mode="Markdown")
        return SRCH_DELIVERY

    return SRCH_PISH_HUB


async def srch_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل": return await search_start(update, context)
    context.user_data['s_type'] = text

    if text in FILTERABLE_TYPES:
        return await show_foroush_hub(update, context)
    else:
        return await run_search_query(update, context)


async def show_foroush_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s_type = context.user_data['s_type']
    kb = [
        [f"📋 نمایش همه ({s_type})"],
        ["📍 فیلتر بر اساس منطقه", "🛏 فیلتر بر اساس تعداد خواب"],
        ["💰 فیلتر بر اساس قیمت", "🔄 موارد قابل معاوضه"],
        ["🔙 مرحله قبل", "🏠 منوی اصلی"]
    ]
    await update.message.reply_text(f"✅ انتخاب شما: **فروش {s_type}**\n\nنحوه نمایش را انتخاب کنید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="Markdown")
    return SRCH_HUB


async def srch_hub_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل":
        await update.message.reply_text("🏠 **نوع ملک** را انتخاب کنید:",
                                        reply_markup=ReplyKeyboardMarkup(PROP_TYPES, resize_keyboard=True),
                                        parse_mode="Markdown")
        return SRCH_TYPE

    if text.startswith("📋 نمایش همه"):
        return await run_search_query(update, context)
    elif text == "🔄 موارد قابل معاوضه":
        return await run_search_query(update, context, only_exchange=True)
    elif text == "📍 فیلتر بر اساس منطقه":
        await update.message.reply_text("📍 **منطقه** را انتخاب کنید:", reply_markup=get_regions_kb(is_search=True),
                                        parse_mode="Markdown")
        return SRCH_REGION
    elif text == "🛏 فیلتر بر اساس تعداد خواب":
        kb = [["بدون خواب (0)", "1 خواب", "2 خواب"], ["3 خواب", "4 خواب و بیشتر"], ["🔙 مرحله قبل", "🏠 منوی اصلی"]]
        await update.message.reply_text("🛏 **تعداد خواب** را انتخاب کنید:",
                                        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                                        parse_mode="Markdown")
        return SRCH_ROOMS
    elif text == "💰 فیلتر بر اساس قیمت":
        kb = [
            ["تا ۵ میلیارد", "۵ تا ۱۰ میلیارد"],
            ["۱۰ تا ۱۵ میلیارد", "۱۵ تا ۲۰ میلیارد"],
            ["۲۰ تا ۲۵ میلیارد", "۲۵ تا ۳۰ میلیارد"],
            ["۳۰ میلیارد به بالا"],
            ["🔙 مرحله قبل", "🏠 منوی اصلی"]
        ]
        await update.message.reply_text("💰 **بازه بودجه** را انتخاب کنید:",
                                        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                                        parse_mode="Markdown")
        return SRCH_PRICE

    return SRCH_HUB


async def back_to_proper_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('s_deal') == "پیش‌فروش":
        return await show_pishforoush_hub(update, context)
    return await show_foroush_hub(update, context)


async def srch_region_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل": return await back_to_proper_hub(update, context)
    if text == "🌐 همه مناطق بناب":
        return await run_search_query(update, context)
    return await run_search_query(update, context, filter_region=text)


async def srch_rooms_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل": return await back_to_proper_hub(update, context)
    rooms_map = {"بدون خواب (0)": 0, "1 خواب": 1, "2 خواب": 2, "3 خواب": 3, "4 خواب و بیشتر": 4}
    return await run_search_query(update, context, filter_rooms=rooms_map.get(text, 0))


async def srch_price_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل": return await back_to_proper_hub(update, context)
    price_ranges = {
        "تا ۵ میلیارد": (0, 5000000000),
        "۵ تا ۱۰ میلیارد": (5000000000, 10000000000),
        "۱۰ تا ۱۵ میلیارد": (10000000000, 15000000000),
        "۱۵ تا ۲۰ میلیارد": (15000000000, 20000000000),
        "۲۰ تا ۲۵ میلیارد": (20000000000, 25000000000),
        "۲۵ تا ۳۰ میلیارد": (25000000000, 30000000000),
        "۳۰ میلیارد به بالا": (30000000000, 999999999999)
    }
    return await run_search_query(update, context, filter_price=price_ranges.get(text))


async def srch_progress_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل": return await show_pishforoush_hub(update, context)
    return await run_search_query(update, context, filter_progress=text)


async def srch_delivery_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    if text == "🔙 مرحله قبل": return await show_pishforoush_hub(update, context)
    return await run_search_query(update, context, filter_delivery=text)


async def run_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE, filter_region=None, filter_rooms=None,
                           filter_price=None, only_exchange=False, filter_progress=None, filter_delivery=None):
    s_deal = context.user_data['s_deal']
    s_type = context.user_data['s_type']

    sql = "SELECT * FROM properties WHERE is_approved = 1 AND deal_type = ? AND prop_type = ?"
    params = [s_deal, s_type]

    if only_exchange:
        sql += " AND is_exchange = 1"
    if filter_region:
        sql += " AND region = ?"
        params.append(filter_region)
    if filter_rooms is not None:
        sql += " AND rooms = ?"
        params.append(filter_rooms)
    if filter_price:
        sql += " AND price BETWEEN ? AND ?"
        params.extend(filter_price)
    if filter_progress:
        sql += " AND progress = ?"
        params.append(filter_progress)
    if filter_delivery:
        sql += " AND delivery = ?"
        params.append(filter_delivery)

    conn = sqlite3.connect("amlak_bonab_v9.db")
    c = conn.cursor()
    c.execute(sql, params)
    results = c.fetchall()
    conn.close()

    user_id = update.effective_user.id
    if not results:
        await update.message.reply_text(
            f"❌ در حال حاضر فایلی برای **{s_type}** ({s_deal}) با این مشخصات ثبت نشده است.",
            reply_markup=main_menu_keyboard(user_id),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await update.message.reply_text(f"✅ تعداد **{len(results)}** ملک یافت شد:",
                                    reply_markup=main_menu_keyboard(user_id), parse_mode="Markdown")

    for row in results:
        await send_property_card(update.message, row)

    return ConversationHandler.END


async def send_property_card(message, row):
    price_val = row[11]
    rent_val = row[12]

    if row[2] == "رهن و اجاره":
        price_str = f"رهن: {price_val:,} تومان | اجاره: {rent_val:,} تومان"
    else:
        if price_val >= 1000000000:
            price_str = f"{price_val / 1000000000:g} میلیارد تومان ({price_val:,} تومان)"
        else:
            price_str = f"{price_val:,} تومان"

    price_label = "مبالغ" if row[2] == "رهن و اجاره" else "قیمت پیشنهادی"

    extra_info = ""
    if row[2] == "پیش‌فروش":
        extra_info = f"🏗 پیشرفت: {row[5] or '-'} | 📅 تحویل: {row[6] or '-'}\n"
    elif row[2] == "فروش" and row[4] == 1:
        extra_info = "🔄 **قابلیت معاوضه دارد**\n"

    rooms_text = f" | 🛏 {row[9]} خواب" if row[3] in FILTERABLE_TYPES and row[9] > 0 else ""
    specs_formatted = "\n".join([f"▫️ {item}" for item in row[13].split(" | ") if item])
    desc_text = f"\n💬 **توضیحات:** {row[14]}" if row[14] else ""

    caption = (
        f"🔖 **کد ملک: {row[1]}** | {row[2]}\n"
        f"🏠 نوع: {row[3]}\n"
        f"📍 منطقه: {row[7]} ({row[8]})\n"
        f"{extra_info}"
        f"📐 متراژ: {row[10]}{rooms_text}\n"
        f"{specs_formatted}\n"
        f"{desc_text}\n"
        f"💰 {price_label}: **{price_str}**\n\n"
        f"📞 تماس با مشاور: `{CONSULTANT_PHONE}`"
    )
    inline_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💚 افزودن به علاقه‌مندی‌ها", callback_data=f"fav_{row[0]}")]
    ])

    media_list = [m for m in (row[17] or "").split(",") if m]
    if media_list:
        caption_sent = await send_media_album(message, None, media_list, caption=caption, reply_markup=inline_kb)
        if not caption_sent:
            await message.reply_text(caption, reply_markup=inline_kb, parse_mode="Markdown")
    else:
        await message.reply_text(caption, reply_markup=inline_kb, parse_mode="Markdown")


# ================= ۳. قابلیت ویرایش توسط ادمین =================
async def req_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["🏠 منوی اصلی"]]
    await update.message.reply_text(
        "👤 **ثبت تقاضای خرید / رهن و اجاره**\n\n"
        "لطفاً مشخصات ملک مورد نظر را به همراه شماره تماس خود بنویسید:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return REQ_TEXT


async def req_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    user = update.effective_user
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"📥 **تقاضای جدید مشتری**\n👤 نام: {user.full_name} (@{user.username or 'ندارد'})\n\n📝 متن تقاضا:\n{text}",
            parse_mode="Markdown"
        )
    await update.message.reply_text("✅ تقاضای شما ثبت و برای مشاور ارسال شد.", reply_markup=main_menu_keyboard(user.id))
    return ConversationHandler.END


async def chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["🏠 منوی اصلی"]]
    await update.message.reply_text("💬 پیام یا سوال خود را برای مشاور بنویسید:",
                                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CHAT_TEXT


async def chat_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🏠 منوی اصلی": return await start(update, context)
    user = update.effective_user
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"💬 **پیام جدید از کاربر**\n👤 {user.full_name} (`{user.id}`):\n\n{text}",
            parse_mode="Markdown"
        )
    await update.message.reply_text("✅ پیام شما به مشاور تحویل داده شد.", reply_markup=main_menu_keyboard(user.id))
    return ConversationHandler.END


async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("amlak_bonab_v9.db")
    c = conn.cursor()
    c.execute('''SELECT p.* FROM properties p
                 JOIN favorites f ON p.id = f.prop_id
                 WHERE f.user_id = ? AND p.is_approved = 1''', (user_id,))
    results = c.fetchall()
    conn.close()
    if not results:
        await update.message.reply_text("💚 لیست علاقه‌مندی‌های شما خالی است.")
        return
    for row in results:
        await send_property_card(update.message, row)


async def contact_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏢 **سامانه جامع املاک بناب**\n\n"
        f"📞 شماره تماس مستقیم: `{CONSULTANT_PHONE}`\n"
        "⏰ ساعات پاسخگویی: ۹ صبح تا ۹ شب",
        parse_mode="Markdown"
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    await update.message.reply_text(
        "🔐 **پنل مدیریت**\n\n"
        "• برای حذف ملک، دستور `/del کد_ملک` را بفرستید (مثال: `/del 101`).\n"
        "• برای ویرایش قیمت ملک، دستور `/editprice کد_ملک قیمت_جدید` را بفرستید.\n"
        "• برای ویرایش توضیحات ملک، دستور `/editdesc کد_ملک توضیحات_جدید` را بفرستید.",
        parse_mode="Markdown"
    )


async def delete_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS or not context.args: return
    code = context.args[0]
    conn = sqlite3.connect("amlak_bonab_v9.db")
    c = conn.cursor()
    c.execute("DELETE FROM properties WHERE code = ?", (code,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    await update.message.reply_text(f"🗑 ملک کد **{code}** حذف شد." if deleted else "❌ کدی یافت نشد.",
                                    parse_mode="Markdown")


async def edit_property_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS or len(context.args) < 2:
        await update.message.reply_text("❌ نحوه استفاده: `/editprice کد_ملک قیمت_جدید`")
        return
    code = context.args[0]
    new_price_raw = " ".join(context.args[1:])
    new_price = parse_persian_price(new_price_raw)

    if not new_price:
        await update.message.reply_text("❌ مبلغ جدید نامعتبر است.")
        return

    conn = sqlite3.connect("amlak_bonab_v9.db")
    c = conn.cursor()
    c.execute("UPDATE properties SET price = ? WHERE code = ?", (new_price, code))
    updated = c.rowcount
    conn.commit()
    conn.close()

    if updated:
        await update.message.reply_text(f"✅ قیمت ملک کد **{code}** به `{new_price:,} تومان` ویرایش شد.",
                                        parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ ملکی با این کد پیدا نشد.")


async def edit_property_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS or len(context.args) < 2:
        await update.message.reply_text("❌ نحوه استفاده: `/editdesc کد_ملک متن_جدید_توضیحات`")
        return
    code = context.args[0]
    new_desc = " ".join(context.args[1:])

    conn = sqlite3.connect("amlak_bonab_v9.db")
    c = conn.cursor()
    c.execute("UPDATE properties SET description = ? WHERE code = ?", (new_desc, code))
    updated = c.rowcount
    conn.commit()
    conn.close()

    if updated:
        await update.message.reply_text(f"✅ توضیحات ملک کد **{code}** با موفقیت ویرایش شد.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ ملکی با این کد پیدا نشد.")


async def inline_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    if data.startswith("fav_"):
        prop_id = int(data.split("_")[1])
        conn = sqlite3.connect("amlak_bonab_v9.db")
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO favorites (user_id, prop_id) VALUES (?, ?)", (user_id, prop_id))
        conn.commit()
        conn.close()
        await query.answer("💚 به علاقه‌مندی‌ها اضافه شد!", show_alert=True)

    elif data.startswith("approve_") and user_id in ADMIN_IDS:
        prop_id = int(data.split("_")[1])
        conn = sqlite3.connect("amlak_bonab_v9.db")
        c = conn.cursor()
        c.execute("UPDATE properties SET is_approved = 1 WHERE id = ?", (prop_id,))
        conn.commit()
        conn.close()
        await query.answer("تایید شد")
        await query.edit_message_text(query.message.text + "\n\n✅ **تایید و منتشر شد.**", parse_mode="Markdown")

    elif data.startswith("reject_") and user_id in ADMIN_IDS:
        prop_id = int(data.split("_")[1])
        conn = sqlite3.connect("amlak_bonab_v9.db")
        c = conn.cursor()
        c.execute("DELETE FROM properties WHERE id = ?", (prop_id,))
        conn.commit()
        conn.close()
        await query.answer("حذف شد")
        await query.edit_message_text(query.message.text + "\n\n❌ **رد و حذف شد.**", parse_mode="Markdown")


# ================= اجرای برنامه =================
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    add_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🖋 سپردن ملک$"), add_prop_start)],
        states={
            ADD_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_deal)],
            ADD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_type)],
            ADD_EXCHANGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_exchange)],
            ADD_PROGRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_progress)],
            ADD_DELIVERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_delivery)],
            ADD_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_region)],
            ADD_REG_CUSTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_reg_custom)],
            APT_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, apt_area)],
            APT_FLOOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, apt_floor)],
            APT_ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, apt_rooms)],
            APT_UNITS: [MessageHandler(filters.TEXT & ~filters.COMMAND, apt_units)],
            APT_PARKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, apt_parking)],
            APT_WAREHOUSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, apt_warehouse)],
            APT_ELEVATOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, apt_elevator)],
            APT_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, apt_year)],
            APT_EQUIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, apt_equip)],
            HSE_LAND_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, hse_land_area)],
            HSE_BUILD_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, hse_build_area)],
            HSE_ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, hse_rooms)],
            HSE_STRUCTURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, hse_structure)],
            HSE_ALLEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, hse_alley)],
            HSE_FRONTAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, hse_frontage)],
            HSE_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, hse_entry)],
            HSE_DEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, hse_deed)],
            HSE_EQUIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, hse_equip)],
            SHP_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, shp_area)],
            SHP_FRONTAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, shp_frontage)],
            SHP_BALCONY: [MessageHandler(filters.TEXT & ~filters.COMMAND, shp_balcony)],
            SHP_DEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, shp_deed)],
            LND_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, lnd_area)],
            LND_FRONTAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, lnd_frontage)],
            LND_ALLEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, lnd_alley)],
            LND_DEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, lnd_deed)],
            LND_WATER: [MessageHandler(filters.TEXT & ~filters.COMMAND, lnd_water)],
            LND_ELECTRICITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, lnd_electricity)],
            LND_GAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, lnd_gas)],
            GRD_MAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, grd_man)],
            GRD_WALL: [MessageHandler(filters.TEXT & ~filters.COMMAND, grd_wall)],
            GRD_HOUSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, grd_house)],
            GRD_WATER: [MessageHandler(filters.TEXT & ~filters.COMMAND, grd_water)],
            GRD_ELECTRICITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, grd_electricity)],
            GRD_GAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, grd_gas)],
            WRK_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, wrk_area)],
            WRK_FACILITIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, wrk_facilities)],
            COM_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, com_address)],
            COM_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, com_price)],
            COM_RENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, com_rent)],
            COM_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, com_desc)],
            COM_OWNER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, com_owner_name)],
            COM_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, com_phone)],
            COM_MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO | filters.TEXT, com_media_handler)],
        },
        fallbacks=[CommandHandler("start", start), MessageHandler(filters.Regex("^🏠 منوی اصلی$"), start)],
    )

    search_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍 جستجوی ملک$"), search_start)],
        states={
            SRCH_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_deal)],
            SRCH_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_type)],
            SRCH_HUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_hub_choice)],
            SRCH_PISH_HUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_pish_hub_choice)],
            SRCH_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_region_done)],
            SRCH_ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_rooms_done)],
            SRCH_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_price_done)],
            SRCH_PROGRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_progress_done)],
            SRCH_DELIVERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, srch_delivery_done)],
        },
        fallbacks=[CommandHandler("start", start), MessageHandler(filters.Regex("^🏠 منوی اصلی$"), start)],
    )

    req_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^👤 ثبت تقاضا$"), req_start)],
        states={REQ_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_save)]},
        fallbacks=[CommandHandler("start", start), MessageHandler(filters.Regex("^🏠 منوی اصلی$"), start)],
    )

    chat_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💬 گفتگو با مشاور$"), chat_start)],
        states={CHAT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat_send)]},
        fallbacks=[CommandHandler("start", start), MessageHandler(filters.Regex("^🏠 منوی اصلی$"), start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("del", delete_property))
    app.add_handler(CommandHandler("editprice", edit_property_price))
    app.add_handler(CommandHandler("editdesc", edit_property_desc))
    app.add_handler(add_conv)
    app.add_handler(search_conv)
    app.add_handler(req_conv)
    app.add_handler(chat_conv)
    app.add_handler(MessageHandler(filters.Regex("^💚 علاقه‌مندی‌ها$"), show_favorites))
    app.add_handler(MessageHandler(filters.Regex("^📞 ارتباط با ما$"), contact_us))
    app.add_handler(MessageHandler(filters.Regex("^🔐 پنل مدیریت"), admin_panel))
    app.add_handler(CallbackQueryHandler(inline_callbacks))

    print("ربات جامع املاک بناب با قابلیت متراژ مَن محلی و اصلاحات جدید روشن شد...")
    app.run_polling()


if __name__ == "__main__":
    main()