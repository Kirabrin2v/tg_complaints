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
from models import ErrorRequest
from event_bus import event_bus
import constants as const
import re

(
    ACCEPT_TYPE,
    ACCEPT_NICK,
    ACCEPT_LOCATION,
    ACCEPT_DATE,
    ACCEPT_DESCRIPTION,
    ACCEPT_MEDIA,
    WAIT_END_DIALOGUE,
) = range(7)

REG_NICK = re.compile(r"([А-яA-Za-z0-9~!@#$^*\-_=+ёЁ]{1,16})")
REG_DATE = re.compile(r"[0-9]{2}.[0-9]{2}.[0-9]{4}")
REG_TIME = re.compile(r"[0-2][0-9]:[0-5][0-9]")

confirm_request_message = load_html("accept_errors/confirm_request.html")
wait_end_dialogue_message = load_html("wait_end_dialogue.html")
choice_edit_request_message = load_html("accept_errors/choice_edit_request.html")
wait_edit_request_message = load_html("accept_errors/wait_edit_request.html")

ask_subcategory_message = load_html("accept_errors/ask_subcategory.html")
ask_nick_message = load_html("accept_errors/ask_nick.html")
ask_location_message = load_html("accept_errors/ask_location.html")
ask_date_message = load_html("accept_errors/ask_date.html")
ask_description_message = load_html("accept_errors/ask_description.html")
ask_media_message = load_html("accept_errors/ask_media.html")

incorrect_nick_message = load_html("accept_errors/errors/incorrect_nick.html")
incorrect_date_message = load_html("accept_errors/errors/incorrect_date.html")
incorrect_time_message = load_html("accept_errors/errors/incorrect_time.html")
none_date_message = load_html("accept_errors/errors/none_date.html")
not_fullness_request_message = load_html(
    "accept_errors/errors/not_fullness_request.html"
)

request_exist_message = load_html("accept_errors/errors/request_exist.html")
success_send_request_message = load_html("accept_errors/success_send_request.html")


async def accept_subcategory_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    if "errors" not in context.user_data:
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

        context.user_data["errors"] = {
            "search_next_handler": search_next_handler,
            "request_type": query.data,
            "conversation_handler": collect_errors_info_handler,
        }

    else:
        context.user_data["errors"]["request_type"] = query.data

    search_next_handler = context.user_data["errors"]["search_next_handler"]
    next_handler = await search_next_handler(
        update, context, context.user_data["errors"]
    )

    return next_handler


async def accept_location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["errors"]["location"] = query.data

    search_next_handler = context.user_data["errors"]["search_next_handler"]
    next_handler = await search_next_handler(
        update, context, context.user_data["errors"]
    )
    return next_handler


@catch_long_message(max_len=16)
async def accept_nick_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nick = update.message.text
    if re.fullmatch(REG_NICK, nick):
        context.user_data["errors"]["nick"] = update.message.text

        search_next_handler = context.user_data["errors"]["search_next_handler"]
        next_handler = await search_next_handler(
            update, context, context.user_data["errors"]
        )
        return next_handler

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=incorrect_nick_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


@catch_long_message(max_len=64)
async def accept_date_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.split(",")
    if len(text) >= 2:
        date_event, time_event, *location = text
        date_event = date_event.strip()
        time_event = time_event.strip()
        if re.fullmatch(REG_DATE, date_event):
            if re.fullmatch(REG_TIME, time_event):
                date = get_datetime(string_time=f"{date_event} {time_event}")
                if date:
                    context.user_data["errors"]["date_event"] = date

                    search_next_handler = context.user_data["errors"][
                        "search_next_handler"
                    ]
                    next_handler = await search_next_handler(
                        update, context, context.user_data["errors"]
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

    elif len(text) == 1:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=none_date_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


@catch_long_message(max_len=800)
async def accept_description_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["errors"]["description"] = update.message.text

    search_next_handler = context.user_data["errors"]["search_next_handler"]
    next_handler = await search_next_handler(
        update, context, context.user_data["errors"]
    )
    return next_handler


async def accept_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if query and query.data == "skip_media":
        await query.answer()
        context.user_data["errors"]["photo_ids"] = []
        context.user_data["errors"]["video_ids"] = []
        search_next_handler = context.user_data["errors"]["search_next_handler"]
        next_handler = await search_next_handler(
            update, context, context.user_data["errors"]
        )
        return next_handler
    else:
        await accept_group_media_handler(
            update=update, context=context, user_data=context.user_data["errors"]
        )


async def confirm_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["errors"]["is_edit"] = False
    message = update.message or update.callback_query.message

    media = [
        InputMediaVideo(
            media=context.user_data["errors"]["video_ids"][index],
            caption=f"Видео №{index+1}",
        )
        for index in range(len(context.user_data["errors"]["video_ids"]))
    ]
    media.extend(
        [
            InputMediaPhoto(
                media=context.user_data["errors"]["photo_ids"][index],
                caption=f"Фото №{index+1}",
            )
            for index in range(len(context.user_data["errors"]["photo_ids"]))
        ]
    )

    if len(media) != 0:
        await context.bot.send_media_group(
            chat_id=update.effective_chat.id, media=media
        )
    keyboard = [
        [
            InlineKeyboardButton(
                const.button_names.to_user("edit_request"), callback_data="edit_request"
            )
        ],
        [
            InlineKeyboardButton(
                const.button_names.to_user("end_collection_request_data"),
                callback_data="end_collection_request_data",
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
        confirm_request_message, context.user_data["errors"], const.button_names
    )

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=text,
        parse_mode="HTML",
        photo=const.greet_image_path,
        reply_markup=reply_markup,
    )


async def choice_edit_request_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["errors"]["is_edit"] = True
    query = update.callback_query

    await query.answer()
    # print(context.args)
    buttons = [
        InlineKeyboardButton(
            const.button_names.to_user("edit_nick"), callback_data="edit_nick"
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_date"), callback_data="edit_date"
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_location"), callback_data="edit_location"
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_media"), callback_data="edit_media"
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

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=choice_edit_request_message,
        parse_mode="HTML",
        reply_markup=reply_markup,
        photo=const.greet_image_path,
    )


async def redirect_edit_request_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    search_next_handler = context.user_data["errors"]["search_next_handler"]
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


async def check_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    search_next_handler = context.user_data["errors"]["search_next_handler"]

    is_fullness = await check_and_edit_fullness_request(
        user_data=context.user_data["errors"],
        handlers=search_next_handler._handlers,
        chat_id=update.effective_chat.id,
        text=not_fullness_request_message,
    )
    if is_fullness:
        print("Заявка хорошая!")
        await check_request_exist_and_publish(
            context=context,
            chat_id=update.effective_chat.id,
        )
        return await cancel(update, context)


async def check_request_exist_and_publish(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int
):
    search_next_handler = context.user_data["errors"]["search_next_handler"]
    need_fields = search_next_handler.get_all_requirements()

    requests = await ErrorRequest.get_active_requests(user_id=chat_id)

    buttons = [
        [
            InlineKeyboardButton(
                const.button_names.to_user("main_menu"), callback_data="main_menu"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    if len(requests) == 0:
        request_data = context.user_data["errors"]
        request_type = request_data["request_type"]
        kwargs = {"user_id": chat_id, "request_type": request_type}

        for field in need_fields:
            kwargs[field] = request_data.get(field)

        request_id = await ErrorRequest.add_request(**kwargs)

        await event_bus.publish(f"new_{request_type}", [request_id, ErrorRequest])

        await const.bot.send_photo(
            chat_id=chat_id,
            caption=success_send_request_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
            reply_markup=reply_markup,
        )
    else:
        message_context = {"request_type": context.user_data["errors"]["request_type"]}
        text = replace_pattern_html(
            text=request_exist_message,
            context=message_context,
            bimap=const.button_names,
        )
        await const.bot.send_photo(
            chat_id=chat_id,
            caption=text,
            parse_mode="HTML",
            photo=const.greet_image_path,
            reply_markup=reply_markup,
        )


# async def accept_pos_or_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
async def wait_end_dialogue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=wait_end_dialogue_message,
        parse_mode="HTML",
        photo=const.greet_image_path,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()

    if context.user_data["errors"].get("is_edit", False):
        search_next_handler = context.user_data["errors"]["search_next_handler"]
        next_handler = await search_next_handler(
            update, context, context.user_data["errors"]
        )
        return next_handler

    else:
        del context.user_data["errors"]

        await start_handler(update, context)

        return ConversationHandler.END


location_buttons = [
    InlineKeyboardButton(const.button_names.to_user(location), callback_data=location)
    for location in const.locations
]
location_buttons = group_buttons_by_levels(location_buttons, 2)

media_button = [
    [
        InlineKeyboardButton(
            const.button_names.to_user("skip_media"), callback_data="skip_media"
        )
    ]
]
handlers_sequence = [
    {
        "requirements": [["request_type"]],
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
        "requirements": [["location"]],
        "state": ACCEPT_LOCATION,
        "text": ask_location_message,
        "reply_markup": InlineKeyboardMarkup(location_buttons),
        "edit_name": "edit_location",
    },
    {
        "requirements": [["date_event"]],
        "state": ACCEPT_DATE,
        "text": ask_date_message,
        "edit_name": "edit_date",
    },
    {
        "requirements": [["description"]],
        "state": ACCEPT_DESCRIPTION,
        "text": ask_description_message,
        "edit_name": "edit_description",
    },
    {
        "requirements": [["photo_ids"], ["video_ids"]],
        "state": ACCEPT_MEDIA,
        "text": ask_media_message,
        "edit_name": "edit_media",
        "reply_markup": InlineKeyboardMarkup(media_button),
    },
]

fallback = {"handler": confirm_request_handler, "state": WAIT_END_DIALOGUE}

pattern_location = "^(" + ")|(".join(const.locations) + ")$"
collect_errors_info_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(accept_subcategory_handler, pattern="^.*_errors_type$")
    ],
    states={
        ACCEPT_NICK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_nick_handler)
        ],
        ACCEPT_LOCATION: [
            CallbackQueryHandler(accept_location_handler, pattern=pattern_location)
        ],
        ACCEPT_DATE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_date_handler)
        ],
        ACCEPT_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_description_handler)
        ],
        ACCEPT_MEDIA: [
            MessageHandler(filters.PHOTO | filters.VIDEO, accept_media_handler),
            CallbackQueryHandler(accept_media_handler, pattern="^skip_media$"),
        ],
        WAIT_END_DIALOGUE: [
            MessageHandler(~filters.COMMAND, wait_end_dialogue_handler)
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(cancel, pattern="^cancel$"),
        CallbackQueryHandler(
            check_request_handler, pattern="^end_collection_request_data$"
        ),
        CallbackQueryHandler(choice_edit_request_handler, pattern="^edit_request$"),
        CallbackQueryHandler(redirect_edit_request_handler, pattern="^edit_.*$"),
    ],
)
