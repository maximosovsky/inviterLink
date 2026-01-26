import telebot
from datetime import datetime, timedelta, timezone
import urllib.parse
import threading

# 1. ТВОЙ ТОКЕН
API_TOKEN = 'ВАШ_ТОКЕН_ЗДЕСЬ'
bot = telebot.TeleBot(API_TOKEN)

# Функция для отправки напоминания
def send_reminder(chat_id, zoom_link):
    try:
        reminder_text = (
            f"⚡️ На всякий случай, напоминаю,\n"
            f"<b>ZOOM через 40 минут</b>\n"
            f"{zoom_link}"
        )
        bot.send_message(chat_id, reminder_text, parse_mode='HTML', disable_web_page_preview=True)
    except:
        pass

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 
        "Привет! Отправь данные встречи:\n\n"
        "<code>Название, Дата (ДД.ММ.ГГГГ), Время (ЧЧ:ММ) Ist, Ссылка</code>", 
        parse_mode='HTML')

@bot.message_handler(func=lambda m: True)
def create_meeting(message):
    try:
        parts = [p.strip() for p in message.text.split(',')]
        if len(parts) < 4: raise ValueError
        title, date_val, time_val, zoom = parts

        # Логика времени (Стамбул UTC+3)
        naive_dt = datetime.strptime(f"{date_val} {time_val}", "%d.%m.%Y %H:%M")
        ist_tz = timezone(timedelta(hours=3))
        meeting_dt_ist = naive_dt.replace(tzinfo=ist_tz)
        
        # Текущее время в Стамбуле
        now_ist = datetime.now(timezone.utc).astimezone(ist_tz)

        # Расчет городов
        h, m = meeting_dt_ist.hour, meeting_dt_ist.minute
        def calc_city(offset):
            nh = (h + offset + 24) % 24
            return f"{nh:02d}:{m:02d}"
        cities = f"{calc_city(-1)} Riga / {calc_city(-2)} Rome / {calc_city(5)} Иркутск / {calc_city(-11)} LA"

        # Ссылка в календарь
        meeting_utc = meeting_dt_ist.astimezone(timezone.utc)
        iso = meeting_utc.strftime("%Y%m%dT%H%M%SZ")
        gcal_link = "https://www.google.com/calendar/render?" + urllib.parse.urlencode({
            "action": "TEMPLATE", "text": title, "dates": f"{iso}/{iso}",
            "details": f"Zoom: {zoom}", "ctz": "UTC"
        })

        # Текст карточки
        months = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
        days_short = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
        res = (f"<b>{title}</b>\n"
               f"⚡️ <b>{meeting_dt_ist.day} {months[meeting_dt_ist.month-1]} {meeting_dt_ist.year}</b> в <b>{days_short[meeting_dt_ist.weekday()]}</b> в <b>{time_val} Ist</b>\n"
               f"<code>{cities}</code>\n\n"
               f"<b>ZOOM</b> — {zoom}\n\n"
               f"📲 <a href='{gcal_link}'>Добавить в календарь</a>")

        bot.send_message(message.chat.id, res, parse_mode='HTML', disable_web_page_preview=True)

        # Таймер напоминания (за 45 минут)
        reminder_dt_ist = meeting_dt_ist - timedelta(minutes=45)
        delay = (reminder_dt_ist - now_ist).total_seconds()

        if delay > 0:
            threading.Timer(delay, send_reminder, args=[message.chat.id, zoom]).start()
            bot.send_message(message.chat.id, 
                             f"🔔 Напоминание придет в <b>{reminder_dt_ist.strftime('%H:%M')}</b> по Ist\n"
                             f"⏳ Ждать: <b>{int(delay/60)} мин.</b>", parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, "⚠️ Время для напоминания уже прошло.")

    except Exception:
        bot.send_message(message.chat.id, "❌ Ошибка формата!")

# ЭТА СТРОЧКА ВАЖНА: она говорит Телеграму забыть про сайт и вернуться к консоли
bot.remove_webhook()

print("Бот запущен в консоли...")
bot.infinity_polling()