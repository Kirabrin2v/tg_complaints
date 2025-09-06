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
from utils.buttons import (
    group_buttons_by_levels,
    manage_selected_buttons,
    show_selected_buttons,
)
from utils.formatter import replace_pattern_html
from models import User, Moderator
from handlers.start import start_handler
import constants as const
import variables as var

greet_admin_mode_message = load_html("admin/greet_admin_mode.html")
ask_username_message = load_html("admin/ask_username.html")
ask_nick_message = load_html("admin/ask_nick.html")
choice_moderator_types_messsage = load_html("admin/choice_moderator_types.html")
success_add_moderator_message = load_html("admin/success_add_moderator.html")
choice_moderator_message = load_html("admin/choice_moderator.html")
choice_edit_moderator_message = load_html("admin/choice_edit_moderator.html")
confirm_delete_moderator_message = load_html("admin/confirm_delete_moderator.html")
success_delete_moderator_message = load_html("admin/success_delete_moderator.html")
success_edit_request_types_message = load_html("admin/success_edit_request_types.html")
return_to_action_choice_message = load_html("admin/return_to_action_choice.html")
choice_active_moderator_message = load_html("admin/choice_active_moderator.html")
success_edit_active_message = load_html("admin/success_edit_active.html")

wait_choice_action_message = load_html("admin/wait_choice_action.html")

not_found_new_moderator_message = load_html("admin/errors/not_found_new_moderator.html")
exist_moderator_message = load_html("admin/errors/exist_moderator.html")
not_choice_types_message = load_html("admin/errors/not_choice_types.html")

WAIT_CHOICE_ACTION = range(1)

(
    ACCEPT_USERNAME,
    ACCEPT_NICKNAME,
    CHOICE_MODER_TYPES,
    ACCEPT_MODER,
    ACCEPT_TYPE_EDIT,
    CHOICE_UPDATE_TYPES,
    EDIT_ACTIVE_MODER,
    DELETE_MODER,
) = range(8)


async def generate_types_buttons(context: ContextTypes.DEFAULT_TYPE):
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

    buttons.append(
        [
            InlineKeyboardButton(
                const.button_names.to_user("confirm_moderator_types"),
                callback_data="confirm_moderator_types",
            )
        ]
    )

    return buttons


async def send_choice_action_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message

    keyboard = [
        [
            InlineKeyboardButton(
                const.button_names.to_user("add_new_moderator"),
                callback_data="add_new_moderator",
            ),
            InlineKeyboardButton(
                const.button_names.to_user("edit_moderators"),
                callback_data="edit_moderators",
            ),
        ],
        [
            InlineKeyboardButton(
                const.button_names.to_user("main_menu"), callback_data="main_menu"
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    else:
        await message.reply_photo(
            caption=text,
            parse_mode="HTML",
            photo=const.greet_image_path,
            reply_markup=reply_markup,
        )


async def choice_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "return_to_action_choice":
        text = return_to_action_choice_message

    else:
        text = greet_admin_mode_message

    context.user_data["moderator"] = {}

    await send_choice_action_message(update, context, text=text)

    return WAIT_CHOICE_ACTION


async def temp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption="*Какое-то действие*",
        parse_mode="HTML",
        photo=const.greet_image_path,
    )


async def wait_choice_action_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    keyboard = [
        [
            InlineKeyboardButton(
                const.button_names.to_user("add_new_moderator"),
                callback_data="add_new_moderator",
            ),
            InlineKeyboardButton(
                const.button_names.to_user("edit_moderators"),
                callback_data="edit_moderators",
            ),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=wait_choice_action_message,
        parse_mode="HTML",
        reply_markup=reply_markup,
        photo=const.greet_image_path,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await start_handler(update, context)
    # await update.message.reply_text("Вы вышли из режима администратора")
    # context.user_data.clear()
    if context.user_data["moderator"]:
        del context.user_data["moderator"]
    return ConversationHandler.END


async def ask_username_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=ask_username_message,
        parse_mode="HTML",
        photo=const.greet_image_path,
    )

    return ACCEPT_USERNAME


async def accept_username_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.replace("@", "")
    user = await User.get_user_by_username(username=username)
    message = update.message
    if user:
        moderator = await Moderator.get_moderator(tg_id=user.tg_id)
        if moderator:
            await send_choice_action_message(
                update, context, text=exist_moderator_message
            )

            return WAIT_CHOICE_ACTION
        else:

            context.user_data["moderator"] = {"username": username, "tg_id": user.tg_id}

            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                caption=ask_nick_message,
                parse_mode="HTML",
                photo=const.greet_image_path,
            )

            return ACCEPT_NICKNAME

    else:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            caption=not_found_new_moderator_message,
            parse_mode="HTML",
            photo=const.greet_image_path,
        )


async def accept_nick_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nick = update.message.text
    context.user_data["moderator"]["nick"] = nick

    await select_types(update, context)
    buttons = await generate_types_buttons(context)
    reply_markup = InlineKeyboardMarkup(buttons)

    context.user_data["moderator"]["pressed_buttons"] = []
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=choice_moderator_types_messsage,
        parse_mode="HTML",
        reply_markup=reply_markup,
        photo=const.greet_image_path,
    )

    return CHOICE_MODER_TYPES


async def choice_types_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "confirm_moderator_types":
        await query.answer()

        if (
            "pressed_buttons" in context.user_data["moderator"]
            and len(context.user_data["moderator"]["pressed_buttons"]) > 0
        ):
            tg_id = context.user_data["moderator"]["tg_id"]
            username = context.user_data["moderator"]["username"]
            nick = context.user_data["moderator"]["nick"]
            request_types = context.user_data["moderator"]["pressed_buttons"]
            await Moderator.add_moderator(
                tg_id=tg_id, nick=nick, request_types=request_types
            )

            href = f'<a href="tg://user?id={tg_id}">{username}</a>'
            context_text = {
                "href": href,
                "categories": ", ".join(map(const.button_names.to_user, request_types)),
            }

            text = replace_pattern_html(
                success_add_moderator_message, context_text, const.button_names
            )
            await send_choice_action_message(update, context, text=text)

            await var.reload_moderator_ids()

            return WAIT_CHOICE_ACTION

        else:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                caption=not_choice_types_message,
                parse_mode="HTML",
                photo=const.greet_image_path,
            )
    else:
        await select_types(update, context)


async def select_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

        if query.data == "show_request_groups":
            if "active_request_types" in context.user_data["moderator"]:
                del context.user_data["moderator"]["active_request_types"]

            buttons = await generate_types_buttons(context)
            reply_markup = InlineKeyboardMarkup(buttons)

            await query.message.edit_caption(
                caption=choice_moderator_types_messsage,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )

        else:
            if "active_request_types" not in context.user_data["moderator"]:
                if query.data == "complaint":
                    button_names = const.complaint_types
                elif query.data == "errors":
                    button_names = const.errors_types
                elif query.data == "other":
                    button_names = const.other_types

                context.user_data["moderator"]["active_request_types"] = button_names

                buttons = show_selected_buttons(
                    all_button_names=button_names,
                    pressed_buttons=context.user_data["moderator"]["pressed_buttons"],
                )
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
                    caption=choice_moderator_types_messsage,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )

            else:
                await manage_selected_buttons(
                    update=update,
                    context=context,
                    button_names=context.user_data["moderator"]["active_request_types"],
                    callback_data="show_request_groups",
                    user_data=context.user_data["moderator"],
                )


async def choice_update_types_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query.data == "confirm_moderator_types":
        await query.answer()

        tg_id = context.user_data["moderator"]["tg_id"]
        request_types = context.user_data["moderator"]["pressed_buttons"]

        await Moderator.update_moderator(tg_id=tg_id, request_types=request_types)

        await send_choice_action_message(
            update, context, text=success_edit_request_types_message
        )
        return WAIT_CHOICE_ACTION

    else:
        await select_types(update, context)


async def ask_moderator_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    buttons = []

    moderators = await Moderator.get_moderators()
    for moderator in moderators:
        tg_id = moderator.tg_id
        user = await User.get_user_by_id(tg_id=tg_id)

        if not user:
            continue

        username = f"@{user.username}" if user.username else ""
        fullname = user.fullname or ""
        buttons.append(
            InlineKeyboardButton(
                f"Модератор {username} ({fullname})",
                callback_data=f"edit_moderator_{tg_id}",
            )
        )

    buttons = group_buttons_by_levels(buttons, 1)
    buttons.append(
        [
            InlineKeyboardButton(
                const.button_names.to_user("cancel_action"),
                callback_data="cancel_action",
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(buttons)

    await query.message.edit_caption(
        # chat_id=update.effective_chat.id,
        caption=choice_moderator_message,
        parse_mode="HTML",
        reply_markup=reply_markup,
        # photo=const.greet_image_path
    )

    return ACCEPT_MODER


async def accept_moderator_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tg_id = int(query.data.split("_")[-1])
    await query.answer(f"Выбран Модератор с айди={tg_id}")

    context.user_data["moderator"] = {"tg_id": tg_id}

    buttons = [
        InlineKeyboardButton(
            const.button_names.to_user("edit_request_types"),
            callback_data="edit_request_types",
        ),
        InlineKeyboardButton(
            const.button_names.to_user("edit_is_active"), callback_data="edit_is_active"
        ),
        InlineKeyboardButton(
            const.button_names.to_user("delete_moderator"),
            callback_data="delete_moderator",
        ),
    ]

    buttons = group_buttons_by_levels(buttons, 2)
    buttons.append(
        [
            InlineKeyboardButton(
                const.button_names.to_user("cancel_action"),
                callback_data="cancel_action",
            )
        ]
    )

    reply_markup = InlineKeyboardMarkup(buttons)

    await query.message.edit_caption(
        # chat_id=update.effective_chat.id,
        caption=choice_edit_moderator_message,
        parse_mode="HTML",
        reply_markup=reply_markup,
        # photo=const.greet_image_path
    )

    return ACCEPT_TYPE_EDIT


async def accept_type_edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "edit_request_types":
        tg_id = context.user_data["moderator"]["tg_id"]
        moderator = await Moderator.get_moderator(tg_id=tg_id)
        context.user_data["moderator"]["pressed_buttons"] = moderator.request_types

        buttons = await generate_types_buttons(context)
        reply_markup = InlineKeyboardMarkup(buttons)

        await query.message.edit_caption(
            # chat_id=update.effective_chat.id,
            caption=choice_moderator_types_messsage,
            parse_mode="HTML",
            reply_markup=reply_markup,
            # photo=const.greet_image_path
        )

        return CHOICE_UPDATE_TYPES

    elif query.data == "edit_is_active":
        buttons = [
            InlineKeyboardButton(
                const.button_names.to_user("block_moderator"),
                callback_data="block_moderator",
            ),
            InlineKeyboardButton(
                const.button_names.to_user("unblock_moderator"),
                callback_data="unblock_moderator",
            ),
        ]

        tg_id = context.user_data["moderator"]["tg_id"]
        moderator = await Moderator.get_moderator(tg_id=tg_id)
        selected_button = [
            "unblock_moderator" if moderator.is_active else "block_moderator"
        ]

        buttons = show_selected_buttons(
            ["block_moderator", "unblock_moderator"], selected_button
        )
        buttons = group_buttons_by_levels(buttons, 2)

        reply_markup = InlineKeyboardMarkup(buttons)

        await query.message.edit_caption(
            # chat_id=update.effective_chat.id,
            caption=choice_active_moderator_message,
            parse_mode="HTML",
            reply_markup=reply_markup,
            # photo=const.greet_image_path
        )

        return EDIT_ACTIVE_MODER

    elif query.data == "delete_moderator":
        buttons = [
            InlineKeyboardButton(
                const.button_names.to_user("cancel_action"),
                callback_data="cancel_action",
            ),
            InlineKeyboardButton(
                const.button_names.to_user("confirm_delete_moderator"),
                callback_data="confirm_delete_moderator",
            ),
        ]

        buttons = group_buttons_by_levels(buttons, 2)

        reply_markup = InlineKeyboardMarkup(buttons)

        await query.message.edit_caption(
            # chat_id=update.effective_chat.id,
            caption=confirm_delete_moderator_message,
            parse_mode="HTML",
            reply_markup=reply_markup,
            # photo=const.greet_image_path
        )

        return DELETE_MODER


async def edit_active_moderator_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    is_active = query.data == "unblock_moderator"
    tg_id = context.user_data["moderator"]["tg_id"]
    await Moderator.update_moderator(tg_id=tg_id, is_active=is_active)
    await var.reload_moderator_ids()
    await send_choice_action_message(update, context, text=success_edit_active_message)

    return WAIT_CHOICE_ACTION


async def delete_moderator_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    tg_id = context.user_data["moderator"]["tg_id"]

    await Moderator.delete_moderator(tg_id=tg_id)
    await var.reload_moderator_ids()
    await send_choice_action_message(
        update, context, text=success_delete_moderator_message
    )

    return WAIT_CHOICE_ACTION


admin_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(choice_admin_action, pattern="^admin_mode$")],
    states={
        WAIT_CHOICE_ACTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, wait_choice_action_handler)
        ],
        ACCEPT_USERNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_username_handler)
        ],
        ACCEPT_NICKNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, accept_nick_handler)
        ],
        CHOICE_MODER_TYPES: [
            CallbackQueryHandler(
                choice_types_handler,
                pattern="^((.*_type)|confirm_moderator_types)|(complaint|errors|other)|(show_request_groups)$",
            )
        ],
        ACCEPT_MODER: [
            CallbackQueryHandler(
                accept_moderator_handler, pattern="^edit_moderator_[0-9]*$"
            )
        ],
        ACCEPT_TYPE_EDIT: [
            CallbackQueryHandler(
                accept_type_edit_handler,
                pattern="^(edit_request_types)|(edit_is_active)|(delete_moderator)$",
            )
        ],
        CHOICE_UPDATE_TYPES: [
            CallbackQueryHandler(
                choice_update_types_handler,
                pattern="^((.*_type)|confirm_moderator_types)|(complaint|errors|other)|(show_request_groups)$",
            )
        ],
        EDIT_ACTIVE_MODER: [
            CallbackQueryHandler(
                edit_active_moderator_handler,
                pattern="^(block_moderator)|(unblock_moderator)$",
            )
        ],
        DELETE_MODER: [
            CallbackQueryHandler(
                delete_moderator_handler, pattern="^confirm_delete_moderator$"
            )
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(cancel, pattern="^main_menu$"),
        CallbackQueryHandler(ask_username_handler, pattern="^add_new_moderator$"),
        CallbackQueryHandler(ask_moderator_handler, pattern="^edit_moderators$"),
        CallbackQueryHandler(choice_admin_action, pattern="^cancel_action$"),
        MessageHandler(filters.ALL, temp_handler),
    ],
)
