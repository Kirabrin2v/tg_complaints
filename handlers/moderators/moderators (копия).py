from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from event_bus import event_bus
from models import Complaint, Moderator, User
from models import Request as BaseRequest
from utils.load_files import load_html
from utils.buttons import group_buttons_by_levels
from utils.formatter import replace_pattern_html, get_datetime
import constants as const
import variables as var

ACCEPT_GROUP, ACCEPT_TYPE, ACCEPT_REQUEST = range(3)

admin_ids = const.admin_ids

notify_new_request_message = load_html("moderators/notify_new_request.html")
show_request_groups_message = load_html("moderators/show_request_groups.html")
show_request_types_message = load_html("moderators/show_request_types.html")
show_requests_list_message = load_html("moderators/show_requests_list.html")

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

start_dialogue_moderator_message = load_html("dialogue/start_dialogue_moderator.html")
start_dialogue_user_message = load_html("dialogue/start_dialogue_user.html")

not_active_request_message = load_html("moderators/errors/not_active_request.html")
no_active_requests_message = load_html("moderators/errors/no_active_requests.html")
no_active_request_types_message = load_html(
    "moderators/errors/no_active_request_types.html"
)


async def show_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_chat.id
    if tg_id not in await var.get_moderator_ids():
        return -1

    query = update.callback_query
    await query.answer()

    request_id = int(query.data.split("_")[-1])
    request = await Complaint.get_complaint(complaint_id=request_id)
    request_type = request.request_type
    user = request.user
    moderator = request.moderator
    href = f'<a href="tg://user?id={user.tg_id}">@{user.username}</a>'
    message_context = request.to_dict()
    message_context["active"] = (
        f"Рассмотрено модератором {moderator.nick}" if moderator else "Активно"
    )
    # context = {
    # 	"href": href,
    # 	"complaint_type": complaint.complaint_type,
    # 	"nick": complaint.nick,
    # 	"date": complaint.date_event,
    # 	"location": complaint.location,
    # 	"description": complaint.description,
    # 	"active": f"Рассмотрено модератором {moderator.nick}" if moderator else "Активно"
    # }

    if "complaint_type" in request_type:
        text = show_complaint_message

    elif "errors_type" in request_type:
        text = show_errors_request_message

    elif "blogger_request" in request_type:
        text = show_blogger_request_message

    elif "buildings_request" in request_type:
        text = show_buildings_request_message

    elif "improvements_request" in request_type:
        text = show_improvements_request_message

    elif "moderation_request" in request_type:
        text = show_moderation_request_message

    text = replace_pattern_html(
        text=text, context=message_context, bimap=const.button_names
    )
    media = []
    if request.video_ids:
        media.extend(
            [
                InputMediaVideo(
                    media=request.video_ids[index], caption=f"Видео №{index+1}"
                )
                for index in range(len(request.video_ids))
            ]
        )
    if request.photo_ids:
        media.extend(
            [
                InputMediaPhoto(
                    media=request.photo_ids[index], caption=f"Фото №{index+1}"
                )
                for index in range(len(request.photo_ids))
            ]
        )

    buttons = [
        InlineKeyboardButton(
            const.button_names.to_user(request_type),
            callback_data=f"{request_type}_list_0",
        ),
        InlineKeyboardButton(
            "Начать диалог", callback_data=f"start_dialogue_{request_id}"
        ),
    ]

    buttons = group_buttons_by_levels(buttons, 2)
    reply_markup = InlineKeyboardMarkup(buttons)

    if len(media) != 0:
        await const.bot.send_media_group(chat_id=tg_id, media=media)
    await const.bot.send_photo(
        chat_id=tg_id,
        caption=text,
        parse_mode="HTML",
        reply_markup=reply_markup,
        photo=const.greet_image_path,
    )


async def show_request_types_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    tg_id = update.effective_chat.id
    if tg_id not in await var.get_moderator_ids():
        return -1

    query = update.callback_query
    await query.answer()

    moderator = await Moderator.get_moderator(tg_id=tg_id)

    if query.data == "complaint":
        request_types = const.complaint_types
    elif query.data == "errors":
        request_types = const.errors_types
    elif query.data == "other":
        request_types = const.other_types

    buttons = []
    for request_type in request_types:
        if request_type in moderator.request_types:
            buttons.append(
                InlineKeyboardButton(
                    const.button_names.to_user(request_type),
                    callback_data=f"{request_type}_list_0",
                )
            )

    if len(buttons) == 0:
        text = no_active_request_types_message
    else:
        text = show_request_types_message
    buttons = group_buttons_by_levels(buttons, 2)
    buttons.append(
        [
            InlineKeyboardButton(
                const.button_names.to_user("show_request_groups"),
                callback_data="show_request_groups",
            )
        ]
    )
    reply_markup = InlineKeyboardMarkup(buttons)

    await query.message.edit_caption(
        caption=text, parse_mode="HTML", reply_markup=reply_markup
    )

    return ACCEPT_REQUEST


async def show_request_groups_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    tg_id = update.effective_chat.id
    if tg_id not in await var.get_moderator_ids():
        return -1

    type_action = "send"
    query = update.callback_query
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

    buttons = group_buttons_by_levels(buttons, 2)
    reply_markup = InlineKeyboardMarkup(buttons)

    if type_action == "send":
        await context.bot.send_photo(
            chat_id=tg_id,
            caption=show_request_groups_message,
            parse_mode="HTML",
            reply_markup=reply_markup,
            photo=const.greet_image_path,
        )
    else:
        await query.message.edit_caption(
            caption=show_request_groups_message,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

    return ACCEPT_GROUP


async def show_requests_list_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    tg_id = update.effective_chat.id
    if tg_id not in await var.get_moderator_ids():
        return -1

    query = update.callback_query

    count_requests_on_page = const.count_requests_on_page
    request_type, num_page = query.data.split("_list_")
    num_page = int(num_page)

    Request = var.request_type_to_db(request_type=request_type)

    start_index = count_requests_on_page * num_page

    print(f"Start: {start_index}, Count: {count_requests_on_page}")

    requests = await Request.get_active_requests(
        request_type=request_type,
        limit=count_requests_on_page
        + 1,  # Запрашиваем на одну больше, чтобы проверить, останутся ли жалобы для следующей страницы
        start_index=start_index,
    )

    if len(requests) > count_requests_on_page:
        requests.pop()
        show_next_page_button = True
    else:
        show_next_page_button = False

    if num_page == 0:
        show_last_page_button = False
    else:
        show_last_page_button = True

    print(show_last_page_button, show_next_page_button)

    buttons = []
    if len(requests) != 0:
        text = show_requests_list_message

        for request in requests:
            request_id = request.id
            nick = request.nick
            date_create = get_datetime(date=request.date_create, to_string=True)
            buttons.append(
                InlineKeyboardButton(
                    f"{nick} {date_create}",
                    callback_data=f"{request_type}_{request_id}",
                )
            )
        buttons = group_buttons_by_levels(buttons, 2)

        buttons.append([])
        if show_last_page_button:
            buttons[-1].append(
                InlineKeyboardButton(
                    f"Назад [Стр. {num_page}]",
                    callback_data=f"{request_type}_list_{num_page-1}",
                )
            )
        if show_next_page_button:
            buttons[-1].append(
                InlineKeyboardButton(
                    f"Далее [Стр. {num_page + 2}]",
                    callback_data=f"{request_type}_list_{num_page+1}",
                )
            )

    else:
        context_message = {"request_type": request_type}
        text = replace_pattern_html(
            no_active_requests_message,
            context=context_message,
            bimap=const.button_names,
        )

    buttons.append(
        [
            InlineKeyboardButton(
                const.button_names.to_user("show_request_types"),
                callback_data="show_request_types",
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_caption(
        # chat_id=tg_id,
        caption=text,
        # parse_mode="HTML",
        reply_markup=reply_markup,
        # photo=const.greet_image_path
    )

    return ACCEPT_REQUEST


async def notify_new_request(request_id: int, Request: BaseRequest):
    moderator_ids = await var.get_moderator_ids()

    request = await Request.get_request(request_id=request_id)
    request_type = request.request_type
    user = request.user

    href = f'<a href="tg://user?id={user.tg_id}">@{user.username}</a>'

    buttons = [
        [
            InlineKeyboardButton(
                "Подробнее", callback_data=f"{request_type}_{request_id}"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    context_message = {"nick": request.nick, "href": href, "request_type": request_type}

    text = replace_pattern_html(
        notify_new_request_message, context=context_message, bimap=const.button_names
    )

    for tg_id in moderator_ids:
        moderator = await Moderator.get_moderator(tg_id=tg_id)
        if request_type in moderator.request_types:
            await const.bot.send_photo(
                chat_id=tg_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
                photo=const.greet_image_path,
            )
            print("Отправлено:", tg_id)


async def start_dialogue_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()

    complaint_id = int(query.data.split("_")[-1])
    complaint = await Complaint.get_complaint(complaint_id=complaint_id)

    if not complaint.moderator_id and complaint.is_active:
        moderator_id = update.effective_chat.id
        complaint.moderator_id = moderator_id

        await Complaint.set_moderator(
            complaint_id=complaint_id, moderator_id=moderator_id
        )

        moderator = await Moderator.get_moderator(tg_id=moderator_id)
        user_id = complaint.user_id
        user = await User.get_user_by_id(tg_id=user_id)
        context.application.bot_data["moderator_dialogue_id"][moderator_id] = user_id
        context.application.bot_data["dialogue_users"][user_id] = {
            "user": user,
            "moderator": moderator,
            "complaint": complaint,
            "context": [],
        }

        buttons = [[InlineKeyboardButton("Завершить диалог")]]

        reply_markup = ReplyKeyboardMarkup(
            buttons, one_time_keyboard=True, resize_keyboard=True
        )

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=start_dialogue_moderator_message,
            parse_mode="HTML",
            reply_markup=reply_markup,
            photo=const.greet_image_path,
        )

        context_message = {
            "complaint_type": complaint.complaint_type,
            "nick": moderator.nick,
        }
        text = replace_pattern_html(
            start_dialogue_user_message,
            context=context_message,
            bimap=const.button_names,
        )

        await context.bot.send_photo(
            chat_id=user_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
            photo=const.greet_image_path,
        )
    else:

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=not_active_request_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


for complaint_type in const.complaint_types:
    event_bus.subscribe(f"new_{complaint_type}", notify_new_request)

for errors_type in const.errors_types:
    event_bus.subscribe(f"new_{errors_type}", notify_new_request)

for other_type in const.other_types:
    event_bus.subscribe(f"new_{other_type}", notify_new_request)


moderator_handler = ConversationHandler(
    entry_points=[CommandHandler("list", show_request_groups_handler)],
    states={
        ACCEPT_GROUP: [
            CallbackQueryHandler(
                show_request_types_handler, pattern="^(complaint)|(errors)|(other)$"
            )
        ],
        ACCEPT_REQUEST: [
            CallbackQueryHandler(show_request_handler, pattern="^.*_type_[0-9]*$"),
            CallbackQueryHandler(show_requests_list_handler, pattern="^.*_list_[0-9]$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            show_request_groups_handler, pattern="^show_request_groups"
        ),
        CallbackQueryHandler(
            show_request_types_handler, pattern="^(complaint)|(errors)|(other)$"
        ),
        CallbackQueryHandler(show_requests_list_handler, pattern="^.*_list_[0-9]$"),
    ],
)


# admin_handler = ConversationHandler(
# 		entry_points=[CallbackQueryHandler(choice_admin_action, pattern="^admin_mode$")],
# 		states={
# 			WAIT_CHOICE_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, wait_choice_action_handler)],
# 			ACCEPT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_username_handler)],
# 			ACCEPT_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_nick_handler)],
# 			CHOICE_MODER_TYPES: [CallbackQueryHandler(choice_types_handler, pattern="^((.*_complaint_type)|confirm_moderator_types)$")],
# 			ACCEPT_MODER: [CallbackQueryHandler(accept_moderator_handler, pattern="^edit_moderator_[0-9]*$")],
# 			ACCEPT_TYPE_EDIT: [CallbackQueryHandler(accept_type_edit_handler, pattern="^(edit_complaint_types)|(edit_is_active)|(delete_moderator)$")],
# 			CHOICE_UPDATE_TYPES: [CallbackQueryHandler(choice_update_types_handler, pattern="^((.*_complaint_type)|confirm_moderator_types)$")],
# 			EDIT_ACTIVE_MODER: [CallbackQueryHandler(edit_active_moderator_handler, pattern="^(block_moderator)|(unblock_moderator)$")],
# 			DELETE_MODER: [CallbackQueryHandler(delete_moderator_handler, pattern="^confirm_delete_moderator$")]


# 		},
# 		fallbacks=[
# 			CommandHandler("cancel", cancel),
# 			CallbackQueryHandler(cancel, pattern="^main_menu$"),
# 			CallbackQueryHandler(ask_username_handler, pattern="^add_new_moderator$"),
# 			CallbackQueryHandler(ask_moderator_handler, pattern="^edit_moderators$"),
# 			CallbackQueryHandler(choice_admin_action, pattern="^cancel_action$"),
# 			MessageHandler(filters.ALL, temp_handler),
# 		]
# 	)


# #, 6816112442]
