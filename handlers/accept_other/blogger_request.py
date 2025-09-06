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
from utils.validator import catch_long_message
from utils.buttons import (
    group_buttons_by_levels,
    manage_selected_buttons,
    show_selected_buttons,
)
import constants as const
import re

(
    ACCEPT_TYPE,
    ACCEPT_NICK,
    ACCEPT_NAME_AND_YEARS,
    ACCEPT_COUNT_SUBSCRIBERS,
    ACCEPT_GAMES,
    ACCEPT_CHANNEL_HREFS,
    ACCEPT_VIDEO_HREFS,
    WAIT_END_DIALOGUE,
) = range(8)

REG_NICK = re.compile(r"([А-яA-Za-z0-9~!@#$^*\-_=+ёЁ]{1,16})")
REG_DATE = re.compile(r"[0-9]{2}.[0-9]{2}.[0-9]{4}")
REG_TIME = re.compile(r"[0-2][0-9]:[0-5][0-9]")
REG_NAME = re.compile(r"[А-яA-zёЁ]{1,32}")
REG_YEARS = re.compile(r"[0-9]{1,3}")
REG_COUNT_SUBSCRIBERS = re.compile(r"[0-9]*")

REG_YOUTUBE_CHANNEL_HREF = r"youtube\.com/@[a-zA-Z0-9._-]+"
REG_TWITCH_CHANNEL_HREF = r"twitch\.tv/[a-zA-Z0-9_-]+"
REG_TIKTOK_CHANNEL_HREF = r"tiktok\.com/@[a-zA-Z0-9._-]+"
REG_CHANNEL_HREF = re.compile(
    f"(?:{REG_YOUTUBE_CHANNEL_HREF})|(?:{REG_TWITCH_CHANNEL_HREF})|(?:{REG_TIKTOK_CHANNEL_HREF})"
)

REG_YOUTUBE_VIDEO_HREF = r"(?:youtube\.com/watch\?v=[\w-]{11})|(?:youtu\.be/.*)"
REG_TWITCH_VIDEO_HREF = r"twitch\.tv/videos/\d+"
REG_TIKTOK_VIDEO_HREF = r"tiktok\.com/@[a-zA-Z0-9._-]+/video/\d+"
REG_VIDEO_HREF = re.compile(
    f"(?:{REG_YOUTUBE_VIDEO_HREF})|(?:{REG_TWITCH_VIDEO_HREF})|(?:{REG_TIKTOK_VIDEO_HREF})"
)

wait_end_dialogue_message = load_html("accept_other/wait_end_dialogue.html")

ask_subcategory_message = load_html("accept_other/ask_subcategory.html")
ask_nick_message = load_html("accept_other/blogger_request/ask_nick.html")
ask_name_and_years_message = load_html(
    "accept_other/blogger_request/ask_name_and_years.html"
)
ask_count_subsribers_message = load_html(
    "accept_other/blogger_request/ask_count_subsribers.html"
)
ask_games_message = load_html("accept_other/blogger_request/ask_games.html")
ask_channel_hrefs_message = load_html(
    "accept_other/blogger_request/ask_channel_hrefs.html"
)
ask_video_hrefs_message = load_html("accept_other/blogger_request/ask_video_hrefs.html")

incorrect_nick_message = load_html(
    "accept_other/blogger_request/errors/incorrect_nick.html"
)
incorrect_name_message = load_html(
    "accept_other/blogger_request/errors/incorrect_name.html"
)
incorrect_years_message = load_html(
    "accept_other/blogger_request/errors/incorrect_years.html"
)
none_name_or_years_message = load_html(
    "accept_other/blogger_request/errors/none_name_or_years.html"
)
incorrect_count_subscribers_message = load_html(
    "accept_other/blogger_request/errors/incorrect_count_subscribers.html"
)
none_channel_hrefs_message = load_html(
    "accept_other/blogger_request/errors/none_channel_hrefs.html"
)
none_video_hrefs_message = load_html(
    "accept_other/blogger_request/errors/none_video_hrefs.html"
)
none_games_message = load_html("accept_other/blogger_request/errors/none_games.html")

confirm_request_message = load_html("accept_other/blogger_request/confirm_request.html")
choice_edit_request_message = load_html("accept_other/choice_edit_request.html")
wait_edit_request_message = load_html("accept_other/wait_edit_request.html")


@catch_long_message(max_len=16)
async def accept_nick_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nick = update.message.text
    if re.fullmatch(REG_NICK, nick):
        context.user_data["other"]["blogger_request"]["nick"] = update.message.text

        search_next_handler = context.user_data["other"]["blogger_request"][
            "search_next_handler"
        ]
        next_handler = await search_next_handler(
            update, context, context.user_data["other"]["blogger_request"]
        )
        return next_handler

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=incorrect_nick_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


@catch_long_message(max_len=32)
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
                context.user_data["other"]["blogger_request"]["name"] = name
                context.user_data["other"]["blogger_request"]["years"] = int(years)

                search_next_handler = context.user_data["other"]["blogger_request"][
                    "search_next_handler"
                ]
                next_handler = await search_next_handler(
                    update, context, context.user_data["other"]["blogger_request"]
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


@catch_long_message(max_len=16)
async def accept_count_subscribers_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    count_subscribers = update.message.text
    if re.fullmatch(REG_COUNT_SUBSCRIBERS, count_subscribers):
        context.user_data["other"]["blogger_request"]["count_subscribers"] = int(
            count_subscribers
        )

        search_next_handler = context.user_data["other"]["blogger_request"][
            "search_next_handler"
        ]
        next_handler = await search_next_handler(
            update, context, context.user_data["other"]["blogger_request"]
        )
        return next_handler

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=incorrect_count_subscribers_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


async def accept_games_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data == "confirm_blogger_games":

        if (
            "games" in context.user_data["other"]["blogger_request"]
            and len(context.user_data["other"]["blogger_request"]["games"]) > 0
        ):
            await query.answer()

            search_next_handler = context.user_data["other"]["blogger_request"][
                "search_next_handler"
            ]
            next_handler = await search_next_handler(
                update, context, context.user_data["other"]["blogger_request"]
            )
            return next_handler

        else:
            await query.answer(none_games_message)

    else:
        await manage_selected_buttons(
            update=update,
            context=context,
            button_names=const.games,
            callback_data="confirm_blogger_games",
            user_data=context.user_data["other"]["blogger_request"],
            namespace="games",
        )


@catch_long_message(max_len=150)
async def accept_channel_hrefs_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    print("Текст, каналы", text)
    hrefs = re.findall(REG_CHANNEL_HREF, text)
    print("Каналы:", hrefs)
    if len(hrefs) > 0:
        context.user_data["other"]["blogger_request"]["channel_hrefs"] = hrefs

        search_next_handler = context.user_data["other"]["blogger_request"][
            "search_next_handler"
        ]
        next_handler = await search_next_handler(
            update, context, context.user_data["other"]["blogger_request"]
        )
        return next_handler

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=none_channel_hrefs_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


@catch_long_message(max_len=150)
async def accept_video_hrefs_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text
    hrefs = re.findall(REG_VIDEO_HREF, text)
    if len(hrefs) > 0:
        context.user_data["other"]["blogger_request"]["video_hrefs"] = hrefs

        search_next_handler = context.user_data["other"]["blogger_request"][
            "search_next_handler"
        ]
        next_handler = await search_next_handler(
            update, context, context.user_data["other"]["blogger_request"]
        )
        return next_handler

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=none_video_hrefs_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


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
        context.user_data["other"]["blogger_request"],
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
            const.button_names.to_user("edit_name_and_years"),
            callback_data="edit_name_and_years",
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_count_subsribers"),
            callback_data="edit_count_subsribers",
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_games"), callback_data="edit_games"
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_channel_hrefs"),
            callback_data="edit_channel_hrefs",
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_video_hrefs"),
            callback_data="edit_video_hrefs",
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

    search_next_handler = context.user_data["other"]["blogger_request"][
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


def generate_game_buttons(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    if (
        "other" in context.user_data
        and "games" in context.user_data["other"]["blogger_request"]
    ):
        pressed_buttons = context.user_data["other"]["blogger_request"]["games"]
    else:
        pressed_buttons = []

    game_buttons = show_selected_buttons(
        all_button_names=const.games, pressed_buttons=pressed_buttons
    )
    game_buttons = group_buttons_by_levels(game_buttons, 2)
    game_buttons.append(
        [
            InlineKeyboardButton(
                const.button_names.to_user("confirm_blogger_games"),
                callback_data="confirm_blogger_games",
            )
        ]
    )

    return InlineKeyboardMarkup(game_buttons)


blogger_request_handlers = [
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
        "requirements": [["count_subscribers"]],
        "state": ACCEPT_COUNT_SUBSCRIBERS,
        "text": ask_count_subsribers_message,
        "edit_name": "edit_count_subsribers",
    },
    {
        "requirements": [["games"]],
        "state": ACCEPT_GAMES,
        "text": ask_games_message,
        "reply_markup": generate_game_buttons,
        "edit_name": "edit_games",
    },
    {
        "requirements": [["channel_hrefs"]],
        "state": ACCEPT_CHANNEL_HREFS,
        "text": ask_channel_hrefs_message,
        "edit_name": "edit_channel_hrefs",
    },
    {
        "requirements": [["video_hrefs"]],
        "state": ACCEPT_VIDEO_HREFS,
        "text": ask_video_hrefs_message,
        "edit_name": "edit_video_hrefs",
    },
]

blogger_request_fallback = {
    "handler": confirm_request_handler,
    "state": WAIT_END_DIALOGUE,
}

blogger_request_conversation_data = {
    "pattern": "^blogger_request_other_type$",
    "states": {
        ACCEPT_NICK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_nick_handler)
        ],
        ACCEPT_NAME_AND_YEARS: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, accept_name_and_years_handler
            )
        ],
        ACCEPT_COUNT_SUBSCRIBERS: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, accept_count_subscribers_handler
            )
        ],
        ACCEPT_GAMES: [
            CallbackQueryHandler(
                accept_games_handler, pattern="^(.*_game)|(confirm_blogger_games)$"
            )
        ],
        ACCEPT_CHANNEL_HREFS: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, accept_channel_hrefs_handler
            )
        ],
        ACCEPT_VIDEO_HREFS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_video_hrefs_handler)
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
