from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import ContextTypes, ConversationHandler
from utils.buttons import group_buttons_by_levels
from typing import Callable, Awaitable, Any
from collections import defaultdict
import asyncio
from models import Request as RequestBase
import constants as const


def check_used(requirements: list[list[str]], used_keys: list[str]) -> bool:
    return any(all(key in used_keys for key in group) for group in requirements)


class SearchNextHandler:
    def __init__(
        self,
        handlers: list[dict[str, Any]],
        message_info: dict[str, str | int],
        fallback: dict[str, Any],
        shared_reply_markup: InlineKeyboardMarkup = InlineKeyboardMarkup([[]]),
    ):
        self._handlers = handlers
        self._fallback = fallback
        self._message_info = message_info
        self._shared_reply_markup = shared_reply_markup

    async def __call__(
        self,
        update: Update = None,
        context: ContextTypes.DEFAULT_TYPE = None,
        used_keys: list[str] | dict[Any] = [],
        edit_name: str = None,
    ) -> dict[str, Any] | int:

        if edit_name:
            return self.search_handler_by_edit_name(
                edit_name=edit_name, context=context
            )
        else:
            if isinstance(used_keys, dict):
                used_keys = used_keys.keys()
            for handler_info in self._handlers:
                requirements = handler_info["requirements"]

                if not check_used(requirements, used_keys):
                    if "reply_markup" in handler_info:
                        obj = handler_info["reply_markup"]

                        if isinstance(obj, InlineKeyboardMarkup) or isinstance(
                            obj, ReplyKeyboardMarkup
                        ):
                            if isinstance(obj, InlineKeyboardMarkup):
                                reply_markup = InlineKeyboardMarkup(
                                    obj.inline_keyboard
                                    + self._shared_reply_markup.inline_keyboard
                                )
                            else:
                                reply_markup = obj
                        else:
                            reply_markup = InlineKeyboardMarkup(
                                obj(context).inline_keyboard
                                + self._shared_reply_markup.inline_keyboard
                            )

                    else:
                        reply_markup = self._shared_reply_markup

                    handler_state = handler_info["state"]
                    text = handler_info["text"]
                    msg_info = self._message_info

                    await const.bot.send_photo(
                        chat_id=msg_info["chat_id"],
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=reply_markup,
                        photo=msg_info["photo"],
                    )

                    return handler_state
            else:
                await self._fallback["handler"](update, context)
                return self._fallback["state"]

    def search_handler_by_edit_name(
        self, edit_name: str, context: ContextTypes.DEFAULT_TYPE
    ) -> dict[str, Any]:
        for handler_info in self._handlers:
            if "edit_name" in handler_info and handler_info["edit_name"] == edit_name:
                handler_return = handler_info.copy()
                if "reply_markup" in handler_info:
                    obj = handler_return["reply_markup"]
                    if isinstance(obj, InlineKeyboardMarkup) or isinstance(
                        obj, ReplyKeyboardMarkup
                    ):
                        if isinstance(obj, InlineKeyboardMarkup):
                            handler_return["reply_markup"] = InlineKeyboardMarkup(
                                obj.inline_keyboard
                                + self._shared_reply_markup.inline_keyboard
                            )
                    else:
                        handler_return["reply_markup"] = InlineKeyboardMarkup(
                            obj(context).inline_keyboard
                            + self._shared_reply_markup.inline_keyboard
                        )
                else:
                    handler_return["reply_markup"] = self._shared_reply_markup
                return handler_return

        raise ValueError(f"{edit_name} отсутствует в структуре хендлеров")

    def get_all_requirements(self) -> list[str]:
        requirements = []
        for handler_info in self._handlers:
            for group in handler_info["requirements"]:
                for requirement in group:
                    requirements.append(requirement)

        return requirements


def set_conversation_state(update, handler: ConversationHandler, new_state) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    handler._conversations[(chat_id, user_id)] = new_state


media_buffers: dict[tuple[int, str], list] = defaultdict(
    list
)  # (user_id, group_id) → list of messages
media_timers: dict[tuple[int, str], asyncio.Task] = {}


async def accept_group_media_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_data: dict[str, Any],
    photo_namespace: str = "photo_ids",
    video_namespace: str = "video_ids",
):
    message = update.message
    group_id = message.media_group_id
    user_id = message.from_user.id

    if not group_id:
        pass

    key = (user_id, group_id)

    media_buffers[key].append(message)

    # Сброс старого таймера, если есть
    if key in media_timers:
        media_timers[key].cancel()

    # Новый таймер (если новых сообщений не будет 1 сек — обрабатываем)
    media_timers[key] = asyncio.create_task(
        wait_and_process(
            user_id=user_id,
            group_id=group_id,
            update=update,
            context=context,
            user_data=user_data,
            photo_namespace=photo_namespace,
            video_namespace=video_namespace,
        )
    )


async def wait_and_process(
    user_id: int,
    group_id: str,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_data: dict[str, Any],
    photo_namespace: str,
    video_namespace: str,
):
    key = (user_id, group_id)

    try:
        await asyncio.sleep(1)  # Ждём, пока все медиа придут

        media_messages = media_buffers.pop(key, [])
        media_timers.pop(key, None)

        print(
            f"[User {user_id}] Группа {group_id} завершена, {len(media_messages)} медиа"
        )

        user_data[photo_namespace] = []
        user_data[video_namespace] = []

        for msg in media_messages:
            if msg.photo:
                user_data[photo_namespace].append(msg.photo[-1].file_id)
            elif msg.video:
                user_data[video_namespace].append(msg.video.file_id)

        conversation_handler = user_data["conversation_handler"]
        search_next_handler = user_data["search_next_handler"]
        next_handler = await search_next_handler(update, context, user_data)
        set_conversation_state(update, conversation_handler, next_handler)

    except asyncio.CancelledError:
        # Ожидаемо отменили — ничего не делаем
        pass


async def check_and_edit_fullness_request(
    user_data: dict[str, Any], handlers: dict[str, Any], chat_id: int, text: str = None
) -> bool:
    missing_buttons = []
    used_keys = user_data.keys()
    for handler_info in handlers:
        requirements = handler_info["requirements"]
        if "edit_name" in handler_info and not check_used(requirements, used_keys):
            edit_name = handler_info["edit_name"]
            missing_buttons.append(
                InlineKeyboardButton(
                    const.button_names.to_user(edit_name), callback_data=edit_name
                )
            )

    if len(missing_buttons) != 0:
        if text:
            missing_buttons = group_buttons_by_levels(missing_buttons, 2)
            reply_markup = InlineKeyboardMarkup(missing_buttons)
            await const.bot.send_photo(
                chat_id=chat_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
                photo=const.greet_image_path,
            )
        return False

    return True


async def send_mediagroup_from_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE, request: RequestBase
) -> None:
    chat_id = update.effective_chat.id

    media = []
    if hasattr(request, "video_ids") and request.video_ids:
        media.extend(
            [
                InputMediaVideo(
                    media=request.video_ids[index], caption="Доказательства"
                )
                for index in range(len(request.video_ids))
            ]
        )
    if hasattr(request, "photo_ids") and request.photo_ids:
        media.extend(
            [
                InputMediaPhoto(
                    media=request.photo_ids[index], caption="Доказательства"
                )
                for index in range(len(request.photo_ids))
            ]
        )
    if hasattr(request, "document_id") and request.document_id:
        await context.bot.send_document(chat_id=chat_id, document=request.document_id)

    if len(media) != 0:
        await const.bot.send_media_group(chat_id=chat_id, media=media)
