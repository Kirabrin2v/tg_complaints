from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from models import User, Moderator
from utils.load_files import load_html
from utils.buttons import remove_reply_keyboard
from utils.message_deleter import delete_messages
from utils.formatter import get_datetime, replace_pattern_html
from event_bus import event_bus
import constants as const
import variables as var

not_support_data_message = load_html("dialogue/errors/not_support_data.html")

end_dialogue_active_message = load_html("dialogue/end_dialogue_active.html")
end_dialoge_passive_message = load_html("dialogue/end_dialogue_passive.html")

DIALOGUE = range(1)


async def dialogue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text
    if text:
        if text in ["Завершить диалог", "/cancel"]:
            await cancel(update, context)
        else:
            await forward_messages_handler(update, context)

    else:
        await message.reply_text(
            text=not_support_data_message,
            parse_mode="HTML",
        )


async def forward_messages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_chat.id
    if tg_id in context.application.bot_data["moderator_dialogue_id"]:
        user_id = context.application.bot_data["moderator_dialogue_id"][tg_id]
        dialogue_info = context.application.bot_data["dialogue_users"][user_id]
        moderator = dialogue_info["moderator"]
        prefix = f"Модератор {moderator.nick}"
        moderator_id = moderator.tg_id
    elif update.effective_chat.id in context.application.bot_data["dialogue_users"]:
        user_id = tg_id
        dialogue_info = context.application.bot_data["dialogue_users"][user_id]
        request = dialogue_info["request"]
        prefix = f"Пользователь {request.nick}"
        moderator_id = request.moderator_id
    else:
        return -1
    message = f"{prefix}: {update.message.text}"
    time_now = get_datetime(to_string=True)

    dialogue_info["context"].append(f"[{time_now}] {message}")
    print(context.application.bot_data["dialogue_users"][user_id])

    for tg_id in [user_id, moderator_id]:
        if tg_id != update.effective_chat.id or const.duplicate_messages:
            message = await context.bot.send_message(
                chat_id=tg_id,
                text=message,
                parse_mode="HTML",
            )

    return DIALOGUE


async def start_dialogue_user_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    tg_id = update.effective_chat.id
    if tg_id in context.application.bot_data["dialogue_users"]:
        text = update.message.text
        if text == "Завершить диалог" or text == "/cancel":
            await cancel(update, context)
            return -1
        elif text:
            await forward_messages_handler(update, context)
            return DIALOGUE
        else:
            await not_support_data_handler(update, context)
    else:
        return -1


async def not_support_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=tg_id,
        text=not_support_data_message,
        parse_mode="HTML",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_chat.id
    if tg_id in context.application.bot_data["dialogue_users"]:
        user_id = tg_id
    else:
        user_id = context.application.bot_data["moderator_dialogue_id"][tg_id]

    if user_id in context.application.bot_data["dialogue_users"]:
        dialogue_info = context.application.bot_data["dialogue_users"][user_id]
        context_chat = dialogue_info["context"]
        request_id = dialogue_info["request"].id
        moderator_id = dialogue_info["moderator"].tg_id
        request_type = dialogue_info["request"].request_type
        start_message_id = dialogue_info["start_message_id"]

        buttons = [
            [
                InlineKeyboardButton(
                    const.button_names.to_user("main_menu"), callback_data="main_menu"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        await delete_messages(
            chat_id=moderator_id,
            message_ids=list(range(start_message_id, update.message.message_id + 1)),
        )

        del context.application.bot_data["dialogue_users"][user_id]
        del context.application.bot_data["moderator_dialogue_id"][moderator_id]

        Request = var.request_type_to_db(request_type=request_type)
        await Request.update_context(request_id=request_id, context=context_chat)

        await remove_reply_keyboard(tg_id=tg_id)
        await context.bot.send_photo(
            chat_id=tg_id,
            caption=end_dialogue_active_message,
            parse_mode="HTML",
            reply_markup=reply_markup,
            photo=const.greet_image_path,
        )

        if moderator_id == tg_id:
            initiator = "Модератор"
            recipient_id = user_id

        else:
            initiator = "Пользователь"
            recipient_id = moderator_id

        context_message = {"initiator": initiator}

        text = replace_pattern_html(
            end_dialoge_passive_message, context=context_message
        )

        await remove_reply_keyboard(tg_id=recipient_id)
        await context.bot.send_photo(
            chat_id=recipient_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
            photo=const.greet_image_path,
        )
