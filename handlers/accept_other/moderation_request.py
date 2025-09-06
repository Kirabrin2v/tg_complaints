from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
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
from utils.buttons import group_buttons_by_levels
import constants as const
import re

(
    ACCEPT_TYPE,
    ACCEPT_NICK,
    ACCEPT_NAME_AND_YEARS,
    ACCEPT_EXPERIENCE,
    ACCEPT_DUTIES_DESCRIPTION,
    WAIT_END_DIALOGUE,
) = range(6)

REG_NICK = re.compile(r"([А-яA-Za-z0-9~!@#$^*\-_=+ёЁ]{1,16})")
REG_DATE = re.compile(r"[0-9]{2}.[0-9]{2}.[0-9]{4}")
REG_TIME = re.compile(r"[0-2][0-9]:[0-5][0-9]")
REG_NAME = re.compile(r"[А-яA-zёЁ]{1,32}")
REG_YEARS = re.compile(r"[0-9]{1,3}")

wait_end_dialogue_message = load_html("accept_other/wait_end_dialogue.html")

ask_subcategory_message = load_html("accept_other/ask_subcategory.html")
ask_nick_message = load_html("accept_other/moderation_request/ask_nick.html")
ask_name_and_years_message = load_html(
    "accept_other/moderation_request/ask_name_and_years.html"
)
ask_experience_message = load_html(
    "accept_other/moderation_request/ask_experience.html"
)
ask_duties_description_message = load_html(
    "accept_other/moderation_request/ask_duties_description.html"
)

incorrect_nick_message = load_html(
    "accept_other/moderation_request/errors/incorrect_nick.html"
)
incorrect_name_message = load_html(
    "accept_other/moderation_request/errors/incorrect_name.html"
)
incorrect_years_message = load_html(
    "accept_other/moderation_request/errors/incorrect_years.html"
)
none_name_or_years_message = load_html(
    "accept_other/moderation_request/errors/none_name_or_years.html"
)

confirm_request_message = load_html(
    "accept_other/moderation_request/confirm_request.html"
)
choice_edit_request_message = load_html("accept_other/choice_edit_request.html")
wait_edit_request_message = load_html("accept_other/wait_edit_request.html")


async def accept_nick_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nick = update.message.text
    if re.fullmatch(REG_NICK, nick):
        context.user_data["other"]["moderation_request"]["nick"] = update.message.text

        search_next_handler = context.user_data["other"]["moderation_request"][
            "search_next_handler"
        ]
        next_handler = await search_next_handler(
            update, context, context.user_data["other"]["moderation_request"]
        )
        return next_handler

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=incorrect_nick_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


async def accept_name_and_years_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    if len(text.split(",")) >= 2:
        name, years = text.split(",")[:2]
        name = name.strip()
        years = years.strip()

        if re.fullmatch(REG_NAME, name):
            if re.fullmatch(REG_YEARS, years):
                context.user_data["other"]["moderation_request"]["name"] = name
                context.user_data["other"]["moderation_request"]["years"] = int(years)

                search_next_handler = context.user_data["other"]["moderation_request"][
                    "search_next_handler"
                ]
                next_handler = await search_next_handler(
                    update, context, context.user_data["other"]["moderation_request"]
                )
                return next_handler

            else:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    caption=incorrect_years_message,
                    parse_mode="HTML",
                    photo=const.greet_image_path,
                )

        else:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                caption=incorrect_name_message,
                parse_mode="HTML",
                photo=const.greet_image_path,
            )

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=none_name_or_years_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


async def accept_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["other"]["moderation_request"]["is_have_experience"] = (
        query.data == "is_have_experience"
    )

    search_next_handler = context.user_data["other"]["moderation_request"][
        "search_next_handler"
    ]
    next_handler = await search_next_handler(
        update, context, context.user_data["other"]["moderation_request"]
    )
    return next_handler


async def accept_duties_description_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["other"]["moderation_request"][
        "duties_description"
    ] = update.message.text

    search_next_handler = context.user_data["other"]["moderation_request"][
        "search_next_handler"
    ]
    next_handler = await search_next_handler(
        update, context, context.user_data["other"]["moderation_request"]
    )
    return next_handler


async def confirm_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["other"]["is_edit"] = False

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
        context.user_data["other"]["moderation_request"],
        const.button_names,
    )
    print("ТЕКСТ", text)
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
            const.button_names.to_user("edit_name_and_years"),
            callback_data="edit_name_and_years",
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_is_have_experience"),
            callback_data="edit_is_have_experience",
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_duties_description"),
            callback_data="edit_duties_description",
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

    search_next_handler = context.user_data["other"]["moderation_request"][
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


async def wait_end_dialogue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=wait_end_dialogue_message,
        parse_mode="HTML",
        photo=const.greet_image_path,
    )


buttons_experience = [
    [
        InlineKeyboardButton(
            const.button_names.to_user("is_not_have_experience"),
            callback_data="is_not_have_experience",
        ),
        InlineKeyboardButton(
            const.button_names.to_user("is_have_experience"),
            callback_data="is_have_experience",
        ),
    ]
]
moderation_request_handlers = [
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
        "requirements": [["name", "years"]],
        "state": ACCEPT_NAME_AND_YEARS,
        "text": ask_name_and_years_message,
        "edit_name": "edit_name_and_years",
    },
    {
        "requirements": [["is_have_experience"]],
        "state": ACCEPT_EXPERIENCE,
        "text": ask_experience_message,
        "reply_markup": InlineKeyboardMarkup(buttons_experience),
        "edit_name": "edit_is_have_experience",
    },
    {
        "requirements": [["duties_description"]],
        "state": ACCEPT_DUTIES_DESCRIPTION,
        "text": ask_duties_description_message,
        "edit_name": "edit_duties_description",
    },
]

moderation_request_fallback = {
    "handler": confirm_request_handler,
    "state": WAIT_END_DIALOGUE,
}

moderation_request_conversation_data = {
    "pattern": "^moderation_request_other_type$",
    "states": {
        ACCEPT_NICK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_nick_handler)
        ],
        ACCEPT_NAME_AND_YEARS: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, accept_name_and_years_handler
            )
        ],
        ACCEPT_EXPERIENCE: [
            CallbackQueryHandler(
                accept_experience,
                pattern="^(is_have_experience)|(is_not_have_experience)$",
            )
        ],
        ACCEPT_DUTIES_DESCRIPTION: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, accept_duties_description_handler
            )
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

# moderation_request_states = {
#                             ACCEPT_NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_nick_handler)],
#                             ACCEPT_NAME_AND_YEARS: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_name_and_years_handler)],
#                             ACCEPT_EXPERIENCE: [CallbackQueryHandler(accept_experience, pattern="^(is_have_experience)|(is_not_have_experience)$")],
#                             ACCEPT_DUTIES_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_duties_description_handler)],
#                             WAIT_END_DIALOGUE: [MessageHandler(~filters.COMMAND, wait_end_dialogue_handler)]
#                         }
