from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import ContextTypes
from typing import Any
import constants as const


async def remove_reply_keyboard(tg_id: int) -> None:
    message = await const.bot.send_message(
        chat_id=tg_id,
        text="Отмена",
        reply_markup=ReplyKeyboardRemove(),
        disable_notification=True,
    )
    await message.delete()


def group_buttons_by_levels(buttons: list, count_in_level: int = 2) -> list:
    grouped = []
    index = 0
    while index < len(buttons):
        grouped.append(buttons[index : index + count_in_level])
        index += count_in_level
    return grouped


def show_selected_buttons(all_button_names: list, pressed_buttons: list) -> list:
    buttons = []
    for button_name in all_button_names:
        user_button = const.button_names.to_user(button_name)

        user_button += " ✅" if button_name in pressed_buttons else " ☐"

        buttons.append(InlineKeyboardButton(user_button, callback_data=button_name))

    return buttons


async def generate_buttons(
    context: ContextTypes.DEFAULT_TYPE,
    button_names: list[str],
    callback_data: str,
    user_data: dict[str, Any],
    namespace: str,
) -> list[list[InlineKeyboardButton]]:

    pressed_buttons = user_data[namespace]

    buttons = show_selected_buttons(button_names, pressed_buttons)
    buttons = group_buttons_by_levels(buttons, 2)

    buttons.append(
        [
            InlineKeyboardButton(
                const.button_names.to_user(callback_data), callback_data=callback_data
            )
        ]
    )

    return buttons


async def manage_selected_buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    button_names: list[str],
    callback_data: str,
    user_data: dict[str, Any],
    namespace: str = "pressed_buttons",
) -> None:
    query = update.callback_query
    system_button = query.data
    user_button = const.button_names.to_user(system_button)
    await query.answer(f"Вы выбрали {user_button}")

    if namespace in user_data:
        if system_button in user_data[namespace]:
            user_data[namespace].remove(system_button)
        else:
            user_data[namespace].append(system_button)

    else:
        user_data[namespace] = [system_button]

    buttons = await generate_buttons(
        context, button_names, callback_data, user_data, namespace
    )

    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_reply_markup(reply_markup=reply_markup)
