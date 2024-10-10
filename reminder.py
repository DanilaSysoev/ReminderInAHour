import db_working as db
import json
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes


add_reminder = 'Добавить напоминание'
check_reminder = 'Посмотреть напоминания'
cancel = 'Отмена'
today = 'Сегодня'
tomorrow = 'Завтра'

intro = 'Продолжая работу, Вы соглашаетесь на сохранение ботом Ваших данных (id telegram и данных о Вашем графике) и отправку ботом сообщений в данный чат.'


wait_command_state = 0
wait_title_state = 1
wait_message_state = 2
wait_date_time_state = 3
wait_date_time_for_request_state = 4


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=intro,
    )
    db.set_chat_id(update.effective_user.id, update.effective_chat.id)
    await to_wait_command(update, context)
    

async def to_wait_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Выберите команду',
        reply_markup = ReplyKeyboardMarkup(
            [[add_reminder, check_reminder]],
            resize_keyboard=True
        ),
    )
    db.set_state(update.effective_user.id, wait_command_state)


async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.text == cancel:
        await to_wait_command(update, context)
    elif db.get_state(update.effective_user.id) == wait_command_state:
        await process_wait_state(update, context)
    elif db.get_state(update.effective_user.id) == wait_title_state:
        await process_wait_title_state(update, context)
    elif db.get_state(update.effective_user.id) == wait_message_state:
        await process_wait_message_state(update, context)
    elif db.get_state(update.effective_user.id) == wait_date_time_state:
        await process_wait_date_time_state(update, context)
    elif db.get_state(update.effective_user.id) == wait_date_time_for_request_state:
        await process_wait_date_time_for_request_state(update, context)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Неизвестная команда. Попробуйте еще раз.',
        )
        await to_wait_command(update, context)


async def process_wait_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.text == add_reminder:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Введите заголовок напоминания',
            reply_markup=ReplyKeyboardMarkup([[cancel]], resize_keyboard=True)
        )
        db.set_state(update.effective_user.id, wait_title_state)
    elif update.effective_message.text == check_reminder:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Выберите дату в формате ДД.ММ.ГГГГ',
            reply_markup = ReplyKeyboardMarkup(
                [[today, tomorrow], [cancel]],
                resize_keyboard=True
            )
        )
        db.set_state(update.effective_user.id, wait_date_time_for_request_state)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Неизвестная команда. Попробуйте еще раз.',
        )
        await to_wait_command(update, context)
        
        
async def process_wait_title_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.set_title(update.effective_user.id, update.effective_message.text)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Введите сообщение напоминания',
    )
    db.set_state(update.effective_user.id, wait_message_state)


async def process_wait_message_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.set_message(update.effective_user.id, update.effective_message.text)
    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text='Введите дату и время напоминания в формате ДД.ММ.ГГГГ ЧЧ:ММ',
    )
    db.set_state(update.effective_user.id, wait_date_time_state)


async def process_wait_date_time_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dt = datetime.strptime(update.effective_message.text, '%d.%m.%Y %H:%M')
    except ValueError:
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = 'Неверный формат даты напоминания'
        )
        await to_wait_command(update, context)
        return
    
    db.add_reminder(
        update.effective_user.id, 
        db.get_title(update.effective_user.id),
        db.get_message(update.effective_user.id),
        dt
    )
    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text='Напоминание добавлено',
    )
    await to_wait_command(update, context)


async def process_wait_date_time_for_request_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.text == today:
        await send_reminder_message(
            update,
            context,
            datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )
    elif update.effective_message.text == tomorrow:
        dt = datetime.now() + timedelta(days=1)
        await send_reminder_message(
            update,
            context,
            dt.replace(hour=0, minute=0, second=0, microsecond=0)
        )
    else:
        try:
            dt = datetime.strptime(update.effective_message.text, '%d.%m.%Y')
        except ValueError:
            await context.bot.send_message(
                chat_id = update.effective_chat.id,
                text = 'Неверный формат даты'
            )
            await to_wait_command(update, context)
            return
        await send_reminder_message(
            update,
            context,
            dt
        )
    await to_wait_command(update, context)


async def send_reminder_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, dt: datetime
):
    reminders = db.get_reminder_on_date(update.effective_user.id, dt)
    if len(reminders) == 0:
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = 'Напоминания отсутствуют'
        )
        return
    for reminder in reminders:
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = build_reminder_message(reminder),
            parse_mode = ParseMode.HTML
        )
        

def build_reminder_message(reminder):
    return f'<b>{reminder[2]}</b>\n{reminder[3]}\n<i>{reminder[4]}</i>'


async def remind(context: ContextTypes.DEFAULT_TYPE):
    dt = datetime.now()
    reminds = db.get_reminders_earlier(dt)
    for reminder in reminds:
        chat_id = db.get_chat_id(reminder[1])
        await context.bot.send_message(
            chat_id = chat_id,
            text = build_reminder_message(reminder),
            parse_mode = ParseMode.HTML
        )
    db.remove_reminder_earlier(dt)


def run():
    with open('config_file.json', 'r') as f:
        config = json.load(f)
    db.create_database(config['db_name'])
    app = ApplicationBuilder().token(config['token']).build()
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, process_message)
    app.add_handler(start_handler)
    app.add_handler(message_handler)
    app.job_queue.run_repeating(remind, 10)
    app.run_polling()


if __name__ == '__main__':
    run()