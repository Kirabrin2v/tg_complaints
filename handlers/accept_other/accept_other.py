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
from utils.buttons import remove_reply_keyboard
from utils.handlers import SearchNextHandler, check_and_edit_fullness_request
from utils.formatter import replace_pattern_html
from handlers.start import start_handler
from .moderation_request import (
    moderation_request_conversation_data,
    moderation_request_handlers,
    moderation_request_fallback,
)
from .blogger_request import (
    blogger_request_conversation_data,
    blogger_request_handlers,
    blogger_request_fallback,
)
from .buildings_request import (
    buildings_request_conversation_data,
    buildings_request_handlers,
    buildings_request_fallback,
)
from .improvements_request import (
    improvements_request_conversation_data,
    improvements_request_handlers,
    improvements_request_fallback,
)
from models import (
    BloggerRequest,
    BuildingsRequest,
    ImprovementsRequest,
    ModerationRequest,
)
from event_bus import event_bus
import constants as const

success_send_request_message = load_html("accept_other/success_send_request.html")

not_fullness_request_message = load_html("accept_other/not_fullness_request.html")
request_exist_message = load_html("accept_other/errors/request_exist.html")


async def accept_other_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    request_type = query.data.split("_other_type")[0]
    if (
        "other" not in context.user_data
        or request_type not in context.user_data["other"]
    ):
        conversation_handler = None

        if query.data == "moderation_request_other_type":
            handlers = moderation_request_handlers
            fallback = moderation_request_fallback

        elif query.data == "blogger_request_other_type":
            handlers = blogger_request_handlers
            fallback = blogger_request_fallback

        elif query.data == "buildings_request_other_type":
            handlers = buildings_request_handlers
            fallback = buildings_request_fallback
            conversation_handler = collect_buildings_request_info_handler

        elif query.data == "improvements_request_other_type":
            print("Зашло в предложения")
            handlers = improvements_request_handlers
            fallback = improvements_request_fallback

        message_info = {
            "chat_id": update.effective_chat.id,
            "parse_mode": "HTML",
            "photo": const.greet_image_path,
        }

        search_next_handler = SearchNextHandler(
            handlers=handlers,
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

        context.user_data["other"] = {
            request_type: {
                "search_next_handler": search_next_handler,
                "request_type": query.data,
                "conversation_handler": conversation_handler,
            }
        }
        # context.user_data["other"][request_type] = {["search_next_handler"] = search_next_handler

    else:
        context.user_data["other"][request_type]["request_type"] = query.data

    context.user_data["other"]["active_request_type"] = request_type

    search_next_handler = context.user_data["other"][request_type][
        "search_next_handler"
    ]
    next_handler = await search_next_handler(
        update, context, context.user_data["other"][request_type]
    )
    return next_handler


async def check_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    active_request_type = context.user_data["other"]["active_request_type"]
    search_next_handler = context.user_data["other"][active_request_type][
        "search_next_handler"
    ]

    is_fullness = await check_and_edit_fullness_request(
        user_data=context.user_data["other"][active_request_type],
        handlers=search_next_handler._handlers,
        chat_id=update.effective_chat.id,
        text=not_fullness_request_message,
    )
    if is_fullness:
        await check_request_exist_and_publish(
            context=context,
            chat_id=update.effective_chat.id,
            request_type=active_request_type,
        )
        return await cancel(update, context)


async def check_request_exist_and_publish(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, request_type: str
):
    search_next_handler = context.user_data["other"][request_type][
        "search_next_handler"
    ]
    need_fields = search_next_handler.get_all_requirements()

    if request_type == "blogger_request":
        Request = BloggerRequest

    elif request_type == "buildings_request":
        Request = BuildingsRequest

    elif request_type == "improvements_request":
        Request = ImprovementsRequest

    elif request_type == "moderation_request":
        Request = ModerationRequest

    requests = await Request.get_active_requests(user_id=chat_id)

    buttons = [
        [
            InlineKeyboardButton(
                const.button_names.to_user("main_menu"), callback_data="main_menu"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    if len(requests) == 0:
        request_data = context.user_data["other"][request_type]
        kwargs = {"user_id": chat_id, "request_type": request_type}

        for field in need_fields:
            kwargs[field] = request_data.get(field)

        request_id = await Request.add_request(**kwargs)

        full_request_type = context.user_data["other"][request_type]["request_type"]
        print(f"new_{full_request_type}")
        await event_bus.publish(f"new_{full_request_type}", [request_id, Request])

        await const.bot.send_photo(
            chat_id=chat_id,
            caption=success_send_request_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
            reply_markup=reply_markup,
        )
    else:
        message_context = {
            "request_type": context.user_data["other"][request_type]["request_type"]
        }
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


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()

    if context.user_data["other"].get("is_edit", False):
        active_request_type = context.user_data["other"]["active_request_type"]
        search_next_handler = context.user_data["other"][active_request_type][
            "search_next_handler"
        ]
        next_handler = await search_next_handler(
            update, context, context.user_data["other"][active_request_type]
        )
        return next_handler

    else:
        del context.user_data["other"]

        await start_handler(update, context)

        return ConversationHandler.END


conversation_fallbacks = [
    CommandHandler("cancel", cancel),
    CallbackQueryHandler(cancel, pattern="^cancel$"),
    CallbackQueryHandler(
        check_request_handler, pattern="^end_collection_request_data$"
    ),
]

moderation_request_conversation_data["fallbacks"].extend(conversation_fallbacks)
moderation_request_conversation_data["entry_points"] = [
    CallbackQueryHandler(
        accept_other_type_handler,
        pattern=moderation_request_conversation_data["pattern"],
    )
]
del moderation_request_conversation_data["pattern"]
collect_moderation_request_info_handler = ConversationHandler(
    **moderation_request_conversation_data
)


blogger_request_conversation_data["fallbacks"].extend(conversation_fallbacks)
blogger_request_conversation_data["entry_points"] = [
    CallbackQueryHandler(
        accept_other_type_handler, pattern=blogger_request_conversation_data["pattern"]
    )
]
del blogger_request_conversation_data["pattern"]
collect_blogger_request_info_handler = ConversationHandler(
    **blogger_request_conversation_data
)


buildings_request_conversation_data["fallbacks"].extend(conversation_fallbacks)
buildings_request_conversation_data["entry_points"] = [
    CallbackQueryHandler(
        accept_other_type_handler,
        pattern=buildings_request_conversation_data["pattern"],
    )
]
del buildings_request_conversation_data["pattern"]
collect_buildings_request_info_handler = ConversationHandler(
    **buildings_request_conversation_data
)


improvements_request_conversation_data["fallbacks"].extend(conversation_fallbacks)
improvements_request_conversation_data["entry_points"] = [
    CallbackQueryHandler(
        accept_other_type_handler,
        pattern=improvements_request_conversation_data["pattern"],
    )
]
del improvements_request_conversation_data["pattern"]
collect_improvements_request_info_handler = ConversationHandler(
    **improvements_request_conversation_data
)
