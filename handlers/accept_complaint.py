from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
)
from utils.load_files import load_html
from utils.buttons import group_buttons_by_levels, remove_reply_keyboard
from utils.formatter import replace_pattern_html, get_datetime
from utils.handlers import (
    SearchNextHandler,
    accept_group_media_handler,
    check_and_edit_fullness_request,
)
from utils.validator import catch_long_message
from handlers.start import start_handler
from models import Complaint
from event_bus import event_bus
import constants as const
import re

# Состояния ConversationHandler
(
    ACCEPT_TYPE,
    ACCEPT_NICK,
    ACCEPT_VIOLATOR_NICK,
    ACCEPT_LOCATION,
    ACCEPT_DESCRIPTION,
    ACCEPT_PROOFS,
    WAIT_END_DIALOGUE,
) = range(7)

REG_NICK = re.compile(r"([А-яA-Za-z0-9~!@#$^*\-_=+ёЁ]{1,16})")
REG_DATE = re.compile(r"[0-9]{2}.[0-9]{2}.[0-9]{4}")
REG_TIME = re.compile(r"[0-2][0-9]:[0-5][0-9]")

confirm_complaint_message = load_html("accept_complaint/confirm_request.html")
wait_end_dialogue_message = load_html("wait_end_dialogue.html")
choice_edit_complaint_message = load_html("accept_complaint/choice_edit_request.html")

ask_subcategory_message = load_html("accept_complaint/ask_subcategory.html")
ask_nick_message = load_html("accept_complaint/ask_nick.html")
ask_violator_nick_message = load_html("accept_complaint/ask_violator_nick.html")
ask_location_message = load_html("accept_complaint/ask_location_and_date.html")
ask_description_message = load_html("accept_complaint/ask_description.html")
ask_proofs_message = load_html("accept_complaint/ask_proofs.html")

incorrect_nick_message = load_html("accept_complaint/errors/incorrect_nick.html")
incorrect_violator_nick_message = load_html(
    "accept_complaint/errors/incorrect_violator_nick.html"
)
incorrect_date_message = load_html("accept_complaint/errors/incorrect_date.html")
incorrect_time_message = load_html("accept_complaint/errors/incorrect_time.html")
incorrect_date_or_time_message = load_html(
    "accept_complaint/errors/incorrect_date_or_time.html"
)
none_date_location_message = load_html(
    "accept_complaint/errors/none_date_location.html"
)
none_location_message = load_html("accept_complaint/errors/none_location.html")
not_correct_data_message = load_html("accept_complaint/errors/not_correct_data.html")
not_fullness_complaint_message = load_html(
    "accept_complaint/errors/not_fullness_request.html"
)

complaint_exist_message = load_html("accept_complaint/errors/active_request_exist.html")
success_send_complaint_message = load_html("accept_complaint/success_send_request.html")


async def accept_complaint_type_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    if "complaint" not in context.user_data:
        message_info = {
            "chat_id": update.effective_chat.id,
            "parse_mode": "HTML",
            "photo": const.greet_image_path,
        }
        search_next_handler = SearchNextHandler(
            handlers=handlers_sequence,
            message_info=message_info,
            fallback=fallback,
            shared_reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            const.button_names.to_user("cancel"), callback_data="cancel"
                        )
                    ]
                ]
            ),
        )

        context.user_data["complaint"] = {
            "search_next_handler": search_next_handler,
            "complaint_type": query.data,
            "conversation_handler": collect_complaint_info_handler,
        }

    else:

        context.user_data["complaint"]["complaint_type"] = query.data

    search_next_handler = context.user_data["complaint"]["search_next_handler"]
    next_handler = await search_next_handler(
        update, context, context.user_data["complaint"]
    )

    return next_handler


@catch_long_message(max_len=16)
async def accept_nick_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nick = update.message.text
    if re.fullmatch(REG_NICK, nick):
        context.user_data["complaint"]["nick"] = nick

        search_next_handler = context.user_data["complaint"]["search_next_handler"]
        next_handler = await search_next_handler(
            update, context, context.user_data["complaint"]
        )

        return next_handler

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=incorrect_nick_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


@catch_long_message(max_len=16)
async def accept_violator_nick_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    violator_nick = update.message.text
    if re.fullmatch(REG_NICK, violator_nick):
        context.user_data["complaint"]["violator_nick"] = violator_nick

        search_next_handler = context.user_data["complaint"]["search_next_handler"]
        next_handler = await search_next_handler(
            update, context, context.user_data["complaint"]
        )

        return next_handler

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=incorrect_violator_nick_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


@catch_long_message(max_len=64)
async def accept_location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.split(",")
    if len(text) >= 3:
        date_event, time_event, *location = text
        date_event = date_event.strip()
        time_event = time_event.strip()
        location = ",".join(location).strip()
        if re.fullmatch(REG_DATE, date_event):
            if re.fullmatch(REG_TIME, time_event):
                date = get_datetime(string_time=f"{date_event} {time_event}")
                if date:
                    context.user_data["complaint"]["date"] = date
                    context.user_data["complaint"]["location"] = location

                    search_next_handler = context.user_data["complaint"][
                        "search_next_handler"
                    ]
                    next_handler = await search_next_handler(
                        update, context, context.user_data["complaint"]
                    )
                    return next_handler

                else:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        caption=incorrect_date_or_time_message,
                        parse_mode="HTML",
                        photo=const.greet_image_path,
                    )

            else:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    caption=incorrect_time_message,
                    parse_mode="HTML",
                    photo=const.greet_image_path,
                )

        else:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                caption=incorrect_date_message,
                parse_mode="HTML",
                photo=const.greet_image_path,
            )

    elif len(text) == 2:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=none_location_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )

    elif len(text) == 1:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=none_date_location_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


@catch_long_message(max_len=600)
async def accept_description_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["complaint"]["description"] = update.message.text

    search_next_handler = context.user_data["complaint"]["search_next_handler"]
    next_handler = await search_next_handler(
        update, context, context.user_data["complaint"]
    )
    return next_handler


async def accept_proofs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await accept_group_media_handler(
        update=update, context=context, user_data=context.user_data["complaint"]
    )


async def confirm_complaint_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["complaint"]["is_edit"] = False
    message = update.message or update.callback_query.message

    media = [
        InputMediaVideo(
            media=context.user_data["complaint"]["video_ids"][index],
            caption=f"Видео №{index+1}",
        )
        for index in range(len(context.user_data["complaint"]["video_ids"]))
    ]
    media.extend(
        [
            InputMediaPhoto(
                media=context.user_data["complaint"]["photo_ids"][index],
                caption=f"Фото №{index+1}",
            )
            for index in range(len(context.user_data["complaint"]["photo_ids"]))
        ]
    )

    await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)
    keyboard = [
        [
            InlineKeyboardButton(
                const.button_names.to_user("edit_complaint"),
                callback_data="edit_complaint",
            )
        ],
        [
            InlineKeyboardButton(
                const.button_names.to_user("end_collection_complaint_data"),
                callback_data="end_collection_complaint_data",
            )
        ],
        [
            InlineKeyboardButton(
                const.button_names.to_user("cancel"), callback_data="cancel"
            )
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = replace_pattern_html(
        confirm_complaint_message, context.user_data["complaint"], const.button_names
    )
    await message.reply_photo(
        caption=text,
        parse_mode="HTML",
        photo=const.greet_image_path,
        reply_markup=reply_markup,
    )


async def wait_end_dialogue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=wait_end_dialogue_message,
        parse_mode="HTML",
        photo=const.greet_image_path,
    )


async def not_correct_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Зашло not_correct_data_handler")
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=not_correct_data_message,
        parse_mode="HTML",
        photo=const.greet_image_path,
    )


async def choice_edit_complaint_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["complaint"]["is_edit"] = True
    query = update.callback_query

    await query.answer()
    # print(context.args)
    buttons = [
        InlineKeyboardButton(
            const.button_names.to_user("edit_nick"), callback_data="edit_nick"
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_violator_nick"),
            callback_data="edit_violator_nick",
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_date_location"),
            callback_data="edit_date_location",
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_description"),
            callback_data="edit_description",
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_proofs"), callback_data="edit_proofs"
        ),
    ]
    buttons = group_buttons_by_levels(buttons, 2)
    buttons.append(
        [
            InlineKeyboardButton(
                const.button_names.to_user("cancel"), callback_data="cancel"
            )
        ]
    )
    reply_markup = InlineKeyboardMarkup(buttons)
    # print(dir(query))
    # print(query.edit_message_caption.__annotations__)
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=choice_edit_complaint_message,
        parse_mode="HTML",
        reply_markup=reply_markup,
        photo=const.greet_image_path,
    )


async def redirect_edit_complaint_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    search_next_handler = context.user_data["complaint"]["search_next_handler"]
    handler_info = await search_next_handler(edit_name=query.data, context=context)

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=handler_info["text"],
        parse_mode="HTML",
        reply_markup=(
            handler_info["reply_markup"] if "reply_markup" in handler_info else None
        ),
        photo=const.greet_image_path,
    )

    return handler_info["state"]


# async def search_next_handler(update: Update, context: ContextTypes. DEFAULT_TYPE):
# 	 if "nick" not in context.user_data:
# 		 buttons = [[InlineKeyboardButton("/cancel")]]

# 		 reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
# 		 #await confirm_complaint_handler(update, context)
# 		 await context.bot.send_photo(
# 				 chat_id=update.effective_chat.id,
# 				 caption=question_nick_message,
# 				 parse_mode="HTML",
# 				 reply_markup=reply_markup,
# 				 photo=const.greet_image_path
# 			 )
# 		 return ACCEPT_NICK

# 	 elif "date" not in context.user_data or "location" not in context.user_data:
# 		 #await confirm_complaint_handler(update, context)
# 		 await context.bot.send_photo(
# 				 chat_id=update.effective_chat.id,
# 				 caption=question_location_message,
# 				 parse_mode="HTML",
# 				 photo=const.greet_image_path
# 			 )

# 		 print(context.user_data, type(context.user_data))
# 		 return ACCEPT_LOCATION

# 	 elif "description" not in context.user_data:
# 		 #await confirm_complaint_handler(update, context)

# 		 await context.bot.send_photo(
# 				 chat_id=update.effective_chat.id,
# 				 caption=question_description_message,
# 				 parse_mode="HTML",
# 				 photo=const.greet_image_path
# 			 )

# 		 return ACCEPT_DESCRIPTION

# 	 elif "video_ids" not in context.user_data and "photo_ids" not in context.user_data:
# 		 # await confirm_complaint_handler(update, context)

# 		 await context.bot.send_photo(
# 				 chat_id=update.effective_chat.id,
# 				 caption=question_proofs_message,
# 				 parse_mode="HTML",
# 				 photo=const.greet_image_path
# 			 )

# 		 return ACCEPT_PROOFS

# 	 else:
# 		 await confirm_complaint_handler(update, context)
# 		 return WAIT_END_DIALOGUE


async def check_complaint_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    is_fullness = await check_and_edit_fullness_request(
        user_data=context.user_data["complaint"],
        handlers=handlers_sequence,
        chat_id=update.effective_chat.id,
        text=not_fullness_complaint_message,
    )
    if is_fullness:
        await check_complaint_exist(update, context)
        return await cancel(update, context)


async def check_complaint_exist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    requests = await Complaint.get_active_requests(user_id=update.effective_chat.id)

    buttons = [
        [
            InlineKeyboardButton(
                const.button_names.to_user("main_menu"), callback_data="main_menu"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    if len(requests) == 0:
        request_data = context.user_data["complaint"]
        request_type = request_data["complaint_type"]
        request_id = await Complaint.add_complaint(
            date_event=request_data["date"],
            user_id=update.effective_chat.id,
            nick=request_data["nick"],
            violator_nick=request_data["violator_nick"],
            request_type=request_type,
            location=request_data["location"],
            description=request_data["description"],
            photo_ids=request_data["photo_ids"],
            video_ids=request_data["video_ids"],
        )

        await event_bus.publish(f"new_{request_type}", [request_id, Complaint])

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=success_send_complaint_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
            reply_markup=reply_markup,
        )
    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=complaint_exist_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
            reply_markup=reply_markup,
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()

    if context.user_data["complaint"].get("is_edit", False):
        search_next_handler = context.user_data["complaint"]["search_next_handler"]
        next_handler = await search_next_handler(
            update, context, context.user_data["complaint"]
        )
        return next_handler

    else:
        del context.user_data["complaint"]

        await start_handler(update, context)

        return ConversationHandler.END


handlers_sequence = [
    {
        "requirements": [["complaint_type"]],
        "state": ACCEPT_TYPE,
        "text": ask_subcategory_message,
    },
    {
        "requirements": [["nick"]],
        "state": ACCEPT_NICK,
        "text": ask_nick_message,
        "edit_name": "edit_nick",
    },
    {
        "requirements": [["violator_nick"]],
        "state": ACCEPT_VIOLATOR_NICK,
        "text": ask_violator_nick_message,
        "edit_name": "edit_violator_nick",
    },
    {
        "requirements": [["date", "location"]],
        "state": ACCEPT_LOCATION,
        "text": ask_location_message,
        "edit_name": "edit_date_location",
    },
    {
        "requirements": [["description"]],
        "state": ACCEPT_DESCRIPTION,
        "text": ask_description_message,
        "edit_name": "edit_description",
    },
    {
        "requirements": [["photo_ids"], ["video_ids"]],
        "state": ACCEPT_PROOFS,
        "text": ask_proofs_message,
        "edit_name": "edit_proofs",
    },
]

fallback = {"handler": confirm_complaint_handler, "state": WAIT_END_DIALOGUE}

collect_complaint_info_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            accept_complaint_type_handler, pattern="^.*_complaint_type$"
        )
    ],
    states={
        ACCEPT_NICK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_nick_handler)
        ],
        ACCEPT_VIOLATOR_NICK: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, accept_violator_nick_handler
            )
        ],
        ACCEPT_LOCATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_location_handler)
        ],
        ACCEPT_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_description_handler)
        ],
        ACCEPT_PROOFS: [
            MessageHandler(filters.PHOTO | filters.VIDEO, accept_proofs_handler)
        ],
        WAIT_END_DIALOGUE: [
            MessageHandler(~filters.COMMAND, wait_end_dialogue_handler)
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(cancel, pattern="^cancel$"),
        CallbackQueryHandler(
            check_complaint_handler, pattern="^end_collection_complaint_data$"
        ),
        CallbackQueryHandler(choice_edit_complaint_handler, pattern="^edit_complaint$"),
        CallbackQueryHandler(redirect_edit_complaint_handler, pattern="^edit_.*$"),
        MessageHandler(filters.ALL, not_correct_data_handler),
    ],
    name="accept_complaint",
)
