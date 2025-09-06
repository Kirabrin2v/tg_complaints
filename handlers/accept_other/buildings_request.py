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

(
    ACCEPT_TYPE,
    ACCEPT_NICK,
    ACCEPT_GAME,
    ACCEPT_MEDIA,
    ACCEPT_DOCUMENT_OR_POS,
    WAIT_END_DIALOGUE,
) = range(6)

REG_NICK = re.compile(r"([А-яA-Za-z0-9~!@#$^*\-_=+ёЁ]{1,16})")
REG_POS = re.compile(r"-?[0-9]* -?[0-9]* -?[0-9]*")

wait_end_dialogue_message = load_html("accept_other/wait_end_dialogue.html")

ask_subcategory_message = load_html("accept_other/ask_subcategory.html")
ask_nick_message = load_html("accept_other/buildings_request/ask_nick.html")
ask_game_message = load_html("accept_other/buildings_request/ask_game.html")
ask_media_message = load_html("accept_other/buildings_request/ask_media.html")
ask_document_or_pos_message = load_html(
    "accept_other/buildings_request/ask_document_or_pos.html"
)

confirm_request_message = load_html(
    "accept_other/buildings_request/confirm_request.html"
)
choice_edit_request_message = load_html("accept_other/choice_edit_request.html")

incorrect_nick_message = load_html(
    "accept_other/buildings_request/errors/incorrect_nick.html"
)
incorrect_pos_message = load_html(
    "accept_other/buildings_request/errors/incorrect_pos.html"
)
incorrect_document_type_message = load_html(
    "accept_other/buildings_request/errors/incorrect_document_type.html"
)
none_pos_and_document_message = load_html(
    "accept_other/buildings_request/errors/none_pos_and_document.html"
)


@catch_long_message(max_len=16)
async def accept_nick_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(dir(filters.Document.FileExtension))
    nick = update.message.text
    if re.fullmatch(REG_NICK, nick):
        context.user_data["other"]["buildings_request"]["nick"] = update.message.text

        search_next_handler = context.user_data["other"]["buildings_request"][
            "search_next_handler"
        ]
        next_handler = await search_next_handler(
            update, context, context.user_data["other"]["buildings_request"]
        )
        return next_handler

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=incorrect_nick_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


async def accept_game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(context.application._conversation_handler_conversations)
    query = update.callback_query
    await query.answer()

    context.user_data["other"]["buildings_request"]["game"] = query.data

    search_next_handler = context.user_data["other"]["buildings_request"][
        "search_next_handler"
    ]
    next_handler = await search_next_handler(
        update, context, context.user_data["other"]["buildings_request"]
    )
    return next_handler


async def accept_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await accept_group_media_handler(
        update=update,
        context=context,
        user_data=context.user_data["other"]["buildings_request"],
    )


@catch_long_message(max_len=64)
async def accept_document_or_pos_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text or update.message.caption
    if update.message.document:
        context.user_data["other"]["buildings_request"][
            "document_id"
        ] = update.message.document.file_id
    else:
        if "document_id" in context.user_data["other"]["buildings_request"]:
            del context.user_data["other"]["buildings_request"]["document_id"]

    if text:
        if re.fullmatch(REG_POS, text):
            pos = text
        else:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                caption=incorrect_pos_message,
                parse_mode="HTML",
                photo=const.greet_image_path,
            )
            return
    else:
        pos = None

    if not pos and "document_id" not in context.user_data["other"]["buildings_request"]:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=none_pos_and_document_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )
    else:
        context.user_data["other"]["buildings_request"][
            "pos"
        ] = pos  # list(map(int, pos.split(" ")))

        search_next_handler = context.user_data["other"]["buildings_request"][
            "search_next_handler"
        ]
        next_handler = await search_next_handler(
            update, context, context.user_data["other"]["buildings_request"]
        )
        return next_handler


async def incorrect_extension_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=incorrect_document_type_message,
        parse_mode="HTML",
        photo=const.greet_image_path,
    )


async def confirm_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["other"]["is_edit"] = False
    media = [
        InputMediaVideo(
            media=context.user_data["other"]["buildings_request"]["video_ids"][index],
            caption=f"Видео №{index+1}",
        )
        for index in range(
            len(context.user_data["other"]["buildings_request"]["video_ids"])
        )
    ]
    media.extend(
        [
            InputMediaPhoto(
                media=context.user_data["other"]["buildings_request"]["photo_ids"][
                    index
                ],
                caption=f"Фото №{index+1}",
            )
            for index in range(
                len(context.user_data["other"]["buildings_request"]["photo_ids"])
            )
        ]
    )
    if "document_id" in context.user_data["other"]["buildings_request"]:
        document_id = context.user_data["other"]["buildings_request"]["document_id"]
        await context.bot.send_document(
            chat_id=update.effective_chat.id, document=document_id
        )

    await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)
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
        context.user_data["other"]["buildings_request"],
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
            const.button_names.to_user("edit_game"), callback_data="edit_game"
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_media"), callback_data="edit_media"
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_document_or_pos"),
            callback_data="edit_document_or_pos",
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

    search_next_handler = context.user_data["other"]["buildings_request"][
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


game_buttons = [
    InlineKeyboardButton(const.button_names.to_user(game), callback_data=game)
    for game in const.games
]
game_buttons = group_buttons_by_levels(game_buttons, 2)

buildings_request_handlers = [
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
        "requirements": [["game"]],
        "state": ACCEPT_GAME,
        "text": ask_game_message,
        "reply_markup": InlineKeyboardMarkup(game_buttons),
        "edit_name": "edit_game",
    },
    {
        "requirements": [["video_ids"], ["photo_ids"]],
        "state": ACCEPT_MEDIA,
        "text": ask_media_message,
        "edit_name": "edit_media",
    },
    {
        "requirements": [["document_id"], ["pos"]],
        "state": ACCEPT_DOCUMENT_OR_POS,
        "text": ask_document_or_pos_message,
        "edit_name": "edit_document_or_pos",
    },
]

buildings_request_fallback = {
    "handler": confirm_request_handler,
    "state": WAIT_END_DIALOGUE,
}

buildings_request_conversation_data = {
    "pattern": "^buildings_request_other_type$",
    "states": {
        ACCEPT_NICK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_nick_handler)
        ],
        ACCEPT_GAME: [CallbackQueryHandler(accept_game_handler, pattern="^.*_game$")],
        ACCEPT_MEDIA: [
            MessageHandler(filters.PHOTO | filters.VIDEO, accept_media_handler)
        ],
        ACCEPT_DOCUMENT_OR_POS: [
            MessageHandler(
                filters.Document.FileExtension("zip")
                | filters.Document.FileExtension("schematic")
                | filters.Document.FileExtension("litematic")
                | filters.Document.FileExtension("schem")
                | filters.TEXT & ~filters.COMMAND,
                accept_document_or_pos_handler,
            ),
            MessageHandler(filters.Document.ALL, incorrect_extension_handler),
        ],
        # ACCEPT_NAME_AND_YEARS: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_name_and_years_handler)],
        # ACCEPT_EXPERIENCE: [CallbackQueryHandler(accept_experience, pattern="^(is_have_experience)|(is_not_have_experience)$")],
        # ACCEPT_DUTIES_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_duties_description_handler)],
        WAIT_END_DIALOGUE: [
            MessageHandler(~filters.COMMAND, wait_end_dialogue_handler)
        ],
    },
    "fallbacks": [
        CallbackQueryHandler(choice_edit_request_handler, pattern="^edit_request$"),
        CallbackQueryHandler(redirect_edit_request_handler, pattern="^edit_.*$"),
    ],
}
