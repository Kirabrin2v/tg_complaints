from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
)
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
)
from utils.load_files import load_html
from utils.formatter import replace_pattern_html
from utils.validator import catch_long_message
from utils.buttons import (
    group_buttons_by_levels,
    manage_selected_buttons,
    show_selected_buttons,
)
from utils.handlers import accept_group_media_handler
import constants as const
import re

ACCEPT_TYPE, ACCEPT_NICK, ACCEPT_IDEA, ACCEPT_MEDIA, WAIT_END_DIALOGUE = range(5)

REG_NICK = re.compile(r"([А-яA-Za-z0-9~!@#$^*\-_=+ёЁ]{1,16})")

wait_end_dialogue_message = load_html("accept_other/wait_end_dialogue.html")

ask_subcategory_message = load_html("accept_other/ask_subcategory.html")
ask_nick_message = load_html("accept_other/improvements_request/ask_nick.html")
ask_idea_message = load_html("accept_other/improvements_request/ask_idea.html")
ask_media_message = load_html("accept_other/improvements_request/ask_media.html")

confirm_request_message = load_html(
    "accept_other/improvements_request/confirm_request.html"
)
choice_edit_request_message = load_html("accept_other/choice_edit_request.html")

incorrect_nick_message = load_html(
    "accept_other/improvements_request/errors/incorrect_nick.html"
)
exceeded_max_len_idea_message = load_html(
    "accept_other/improvements_request/errors/exceeded_max_len_idea.html"
)


@catch_long_message(max_len=16)
async def accept_nick_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nick = update.message.text
    if re.fullmatch(REG_NICK, nick):
        context.user_data["other"]["improvements_request"]["nick"] = update.message.text

        search_next_handler = context.user_data["other"]["improvements_request"][
            "search_next_handler"
        ]
        next_handler = await search_next_handler(
            update, context, context.user_data["other"]["improvements_request"]
        )
        return next_handler

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=incorrect_nick_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


@catch_long_message(max_len=800, text=exceeded_max_len_idea_message)
async def accept_idea_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        context.user_data["other"]["improvements_request"][
            "document_id"
        ] = update.message.document.file_id
        context.user_data["other"]["improvements_request"]["idea"] = "Указано в файле"
    else:
        context.user_data["other"]["improvements_request"]["idea"] = update.message.text
        if "document_id" in context.user_data["other"]["improvements_request"]:
            del context.user_data["other"]["improvements_request"]["document_id"]

    search_next_handler = context.user_data["other"]["improvements_request"][
        "search_next_handler"
    ]
    next_handler = await search_next_handler(
        update, context, context.user_data["other"]["improvements_request"]
    )
    return next_handler


async def accept_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query and query.data == "skip_media":
        await query.answer()
        context.user_data["other"]["improvements_request"]["photo_ids"] = []
        context.user_data["other"]["improvements_request"]["video_ids"] = []
        search_next_handler = context.user_data["other"]["improvements_request"][
            "search_next_handler"
        ]
        next_handler = await search_next_handler(
            update, context, context.user_data["other"]["improvements_request"]
        )
        return next_handler

    else:
        await accept_group_media_handler(
            update=update,
            context=context,
            user_data=context.user_data["other"]["improvements_request"],
        )


async def confirm_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["other"]["is_edit"] = False
    media = [
        InputMediaVideo(
            media=context.user_data["other"]["improvements_request"]["video_ids"][
                index
            ],
            caption=f"Видео №{index+1}",
        )
        for index in range(
            len(context.user_data["other"]["improvements_request"]["video_ids"])
        )
    ]
    media.extend(
        [
            InputMediaPhoto(
                media=context.user_data["other"]["improvements_request"]["photo_ids"][
                    index
                ],
                caption=f"Фото №{index+1}",
            )
            for index in range(
                len(context.user_data["other"]["improvements_request"]["photo_ids"])
            )
        ]
    )
    if "document_id" in context.user_data["other"]["improvements_request"]:
        document_id = context.user_data["other"]["improvements_request"]["document_id"]
        await context.bot.send_document(
            chat_id=update.effective_chat.id, document=document_id
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
        confirm_request_message,
        context.user_data["other"]["improvements_request"],
        const.button_names,
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
    context.user_data["other"]["is_edit"] = True
    query = update.callback_query

    await query.answer()
    # print(context.args)
    buttons = [
        InlineKeyboardButton(
            const.button_names.to_user("edit_nick"), callback_data="edit_nick"
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_idea"), callback_data="edit_idea"
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

    search_next_handler = context.user_data["other"]["improvements_request"][
        "search_next_handler"
    ]
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


# async def accept_pos_or_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
async def wait_end_dialogue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=wait_end_dialogue_message,
        parse_mode="HTML",
        photo=const.greet_image_path,
    )


media_button = [
    [
        InlineKeyboardButton(
            const.button_names.to_user("skip_media"), callback_data="skip_media"
        )
    ]
]
improvements_request_handlers = [
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
        "requirements": [["idea"], ["document_id"]],
        "state": ACCEPT_IDEA,
        "text": ask_idea_message,
        "edit_name": "edit_idea",
    },
    {
        "requirements": [["photo_ids"], ["video_ids"]],
        "state": ACCEPT_MEDIA,
        "text": ask_media_message,
        "edit_name": "edit_media",
        "reply_markup": InlineKeyboardMarkup(media_button),
    },
]

improvements_request_fallback = {
    "handler": confirm_request_handler,
    "state": WAIT_END_DIALOGUE,
}

improvements_request_conversation_data = {
    "pattern": "^improvements_request_other_type$",
    "states": {
        ACCEPT_NICK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_nick_handler)
        ],
        ACCEPT_IDEA: [
            MessageHandler(
                filters.Document.FileExtension("txt") | filters.TEXT & ~filters.COMMAND,
                accept_idea_handler,
            )
        ],
        ACCEPT_MEDIA: [
            MessageHandler(filters.PHOTO | filters.VIDEO, accept_media_handler),
            CallbackQueryHandler(accept_media_handler, pattern="^skip_media$"),
        ],
        WAIT_END_DIALOGUE: [
            MessageHandler(~filters.COMMAND, wait_end_dialogue_handler)
        ],
    },
    "fallbacks": [
        CallbackQueryHandler(choice_edit_request_handler, pattern="^edit_request$"),
        CallbackQueryHandler(redirect_edit_request_handler, pattern="^edit_.*$"),
    ],
}
