from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import ContextTypes
from utils.load_files import load_html
from utils.buttons import group_buttons_by_levels
from utils.formatter import replace_pattern_html
from utils.formatter import get_datetime
from utils.handlers import send_mediagroup_from_request
from models import (
    User,
    Moderator,
    Complaint,
    ErrorRequest,
    BloggerRequest,
    BuildingsRequest,
    ImprovementsRequest,
    ModerationRequest,
)
import constants as const
import variables as var

start_message = load_html("start/start_message.html")

ask_subcategory_complaint_message = load_html("accept_complaint/ask_subcategory.html")
ask_subcategory_errors_message = load_html("accept_errors/ask_subcategory.html")
ask_subcategory_other_message = load_html("accept_other/ask_subcategory.html")

show_requests_list_message = load_html("start/show_requests_list.html")
show_complaint_message = load_html("moderators/show_request/show_complaint.html")
show_errors_request_message = load_html(
    "moderators/show_request/show_errors_request.html"
)
show_blogger_request_message = load_html(
    "moderators/show_request/show_blogger_request.html"
)
show_buildings_request_message = load_html(
    "moderators/show_request/show_buildings_request.html"
)
show_improvements_request_message = load_html(
    "moderators/show_request/show_improvements_request.html"
)
show_moderation_request_message = load_html(
    "moderators/show_request/show_moderation_request.html"
)

no_active_requests_message = load_html("start/errors/no_active_requests.html")
not_active_request_message = load_html("start/errors/not_active_request.html")


async def get_all_active_requests(user_id: int):
    requests = []
    for Request in [
        Complaint,
        ErrorRequest,
        BloggerRequest,
        BuildingsRequest,
        ImprovementsRequest,
        ModerationRequest,
    ]:
        current_requests = await Request.get_active_requests(user_id=user_id)
        requests += current_requests

    return requests


async def show_user_requests_list_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    message = query.message

    requests = await get_all_active_requests(user_id=chat_id)

    buttons = []

    if len(requests) != 0:
        text = show_requests_list_message

        for request in requests:
            date_create = get_datetime(date=request.date_create, to_string=True)
            button_text = (
                f"{const.button_names.to_user(request.request_type)} [{date_create}]"
            )
            callback_data = f"active_{request.request_type}_{request.id}"
            buttons.append(
                InlineKeyboardButton(button_text, callback_data=callback_data)
            )
    else:
        text = no_active_requests_message

    buttons = group_buttons_by_levels(buttons, 1)
    buttons.append(
        [
            InlineKeyboardButton(
                const.button_names.to_user("main_menu"), callback_data="main_menu"
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(buttons)

    await message.edit_caption(
        caption=text, parse_mode="HTML", reply_markup=reply_markup
    )


def get_show_request_message(request_type: str) -> str:
    if "complaint_type" in request_type:
        return show_complaint_message
    elif "errors_type" in request_type:
        return show_errors_request_message
    elif "blogger_request" in request_type:
        return show_blogger_request_message
    elif "buildings_request" in request_type:
        return show_buildings_request_message
    elif "improvements_request" in request_type:
        return show_improvements_request_message
    elif "moderation_request" in request_type:
        return show_moderation_request_message


async def show_user_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    message = query.message

    *request_type, request_id = query.data.split("active_")[1].split("_")
    request_type = "_".join(request_type)
    request_id = int(request_id)

    Request = var.request_type_to_db(request_type=request_type)
    request = await Request.get_request(request_id=request_id)

    user = request.user
    moderator = request.moderator
    href = f'<a href="tg://user?id={user.tg_id}">@{user.username}</a>'
    message_context = request.to_dict()
    message_context["active"] = (
        f"Рассмотрено модератором {moderator.nick}" if moderator else "Активно"
    )
    message_context["href"] = href

    if request and request.is_active and not request.moderator_id:
        text = get_show_request_message(request_type=request_type)
        text = replace_pattern_html(
            text=text, context=message_context, bimap=const.button_names
        )
    else:
        text = not_active_request_message

    await send_mediagroup_from_request(update=update, context=context, request=request)

    buttons = [
        [
            InlineKeyboardButton(
                const.button_names.to_user("main_menu"), callback_data="main_menu"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await message.reply_photo(
        caption=text,
        parse_mode="HTML",
        reply_markup=reply_markup,
        photo=const.greet_image_path,
    )


# Команда /start с кнопками
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    message = update.message or query.message
    chat_id = update.effective_chat.id
    type_action = "send"
    if query:
        await query.answer()
        type_action = "edit"

    buttons = [
        InlineKeyboardButton(
            const.button_names.to_user("complaint"), callback_data="complaint"
        ),
        InlineKeyboardButton(
            const.button_names.to_user("errors"), callback_data="errors"
        ),
        InlineKeyboardButton(
            const.button_names.to_user("other"), callback_data="other"
        ),
    ]
    active_requests = await get_all_active_requests(user_id=chat_id)
    if len(active_requests) != 0:
        buttons.append(
            InlineKeyboardButton(
                const.button_names.to_user("show_user_active_requests"),
                callback_data="show_user_active_requests",
            )
        )

    if chat_id in const.admin_ids:
        buttons.append(
            InlineKeyboardButton(
                const.button_names.to_user("admin_mode"), callback_data="admin_mode"
            )
        )

    if chat_id in await var.get_moderator_ids():
        buttons.append(
            InlineKeyboardButton(
                const.button_names.to_user("moderator_mode"),
                callback_data="moderator_mode",
            )
        )

    buttons = group_buttons_by_levels(buttons, 1)

    message_context = {"nickname": message.chat.first_name}
    text = replace_pattern_html(text=start_message, context=message_context)

    reply_markup = InlineKeyboardMarkup(buttons)
    if type_action == "send":
        await context.bot.send_photo(
            chat_id=chat_id,
            caption=text,
            parse_mode="HTML",
            photo=const.greet_image_path,
            reply_markup=reply_markup,
        )
    elif type_action == "edit":
        message = query.message
        await context.bot.edit_message_caption(
            chat_id=message.chat_id,
            message_id=message.message_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


async def choice_subcategory_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    if query.data == "complaint":
        await query.answer()
        # print(context.args)
        buttons = [
            InlineKeyboardButton(
                const.button_names.to_user(complaint_type), callback_data=complaint_type
            )
            for complaint_type in const.complaint_types
        ]

        buttons = group_buttons_by_levels(buttons, 2)
        buttons.append(
            [
                InlineKeyboardButton(
                    const.button_names.to_user("main_menu"), callback_data="main_menu"
                )
            ]
        )

        reply_markup = InlineKeyboardMarkup(buttons)

        await query.edit_message_caption(
            caption=ask_subcategory_complaint_message,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

    elif query.data == "errors":
        await query.answer()

        buttons = [
            InlineKeyboardButton(
                const.button_names.to_user(errors_type), callback_data=errors_type
            )
            for errors_type in const.errors_types
        ]

        buttons = group_buttons_by_levels(buttons, 2)
        buttons.append(
            [
                InlineKeyboardButton(
                    const.button_names.to_user("main_menu"), callback_data="main_menu"
                )
            ]
        )

        reply_markup = InlineKeyboardMarkup(buttons)

        await query.edit_message_caption(
            caption=ask_subcategory_errors_message,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

    elif query.data == "other":
        await query.answer()

        buttons = [
            InlineKeyboardButton(
                const.button_names.to_user(other_type), callback_data=other_type
            )
            for other_type in const.other_types
        ]

        buttons = group_buttons_by_levels(buttons, 2)
        buttons.append(
            [
                InlineKeyboardButton(
                    const.button_names.to_user("main_menu"), callback_data="main_menu"
                )
            ]
        )

        reply_markup = InlineKeyboardMarkup(buttons)

        await query.edit_message_caption(
            caption=ask_subcategory_other_message,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
