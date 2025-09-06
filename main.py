from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import os
from dotenv import load_dotenv
import re
import asyncio
from handlers.start import (
    start_handler,
    choice_subcategory_handler,
    show_user_requests_list_handler,
    show_user_request_handler,
)
from handlers.accept_complaint import collect_complaint_info_handler
from handlers.accept_other.accept_other import (
    collect_moderation_request_info_handler,
    collect_blogger_request_info_handler,
    collect_buildings_request_info_handler,
    collect_improvements_request_info_handler,
)
from handlers.accept_errors import collect_errors_info_handler
from handlers.admin_mode import admin_handler
from handlers.bridge import dialogue_handler
from handlers.moderators.moderators import (
    moderator_handler,
    start_dialogue_handler,
)
from filters import active_dialogue_filter
import constants as const
from models import User


load_dotenv()
TOKEN = os.getenv("TG_TOKEN")


async def logging(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.message.chat
    tg_id = update.effective_chat.id
    first_name = chat.first_name
    last_name = chat.last_name
    username = chat.username

    update_user = await User.get_user_by_id(tg_id=tg_id)
    if update_user:
        if (
            update_user.username != username
            or update_user.fullname != f"{first_name} {last_name}"
        ):
            await User.update_user(
                tg_id=tg_id,
                new_username=username,
                first_name=first_name,
                last_name=last_name,
            )
    else:
        match_user = await User.get_user_by_username(username=username)
        if match_user:
            await User.update_user(
                tg_id=match_user.tg_id, new_username=None, fullname=match_user.fullname
            )

        await User.add_user(
            tg_id=tg_id, username=username, first_name=first_name, last_name=last_name
        )

    return None


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)


# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    bot = app.bot
    app.bot_data["dialogue_users"] = {}
    app.bot_data["moderator_dialogue_id"] = {}
    const.bot = bot
    const.app = app

    app.add_handler(MessageHandler(filters.ALL, logging), group=-1)

    app.add_handler(MessageHandler(active_dialogue_filter, dialogue_handler))
    app.add_handler(
        CallbackQueryHandler(start_dialogue_handler, pattern="^start_dialogue_[0-9]*$")
    )
    app.add_handler(
        CallbackQueryHandler(show_user_request_handler, pattern="^active_.*$")
    )

    app.add_handler(admin_handler)
    app.add_handler(moderator_handler)
    app.add_handler(collect_complaint_info_handler)
    app.add_handler(collect_errors_info_handler)
    app.add_handler(collect_moderation_request_info_handler)
    app.add_handler(collect_blogger_request_info_handler)
    app.add_handler(collect_buildings_request_info_handler)
    app.add_handler(collect_improvements_request_info_handler)
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CallbackQueryHandler(start_handler, pattern="^main_menu$"))
    app.add_handler(
        CallbackQueryHandler(
            choice_subcategory_handler, pattern="^complaint|error|other$"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            show_user_requests_list_handler, pattern="^show_user_active_requests$"
        )
    )

    app.run_polling()
